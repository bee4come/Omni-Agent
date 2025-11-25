import yaml
import os
from typing import Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from .models import ProjectPolicy, AgentPolicy, UsageSnapshot, PolicyDecision

# Default project for legacy config compatibility
DEFAULT_PROJECT_ID = "default-project"

class RiskEngine:
    """
    Risk assessment engine for detecting suspicious patterns.
    """
    def __init__(self):
        # Track call patterns
        self.call_history = []  # List of {agent_id, service_id, cost, timestamp}
        self.provider_failure_counts = defaultdict(int)  # {service_id: failure_count}
    
    def assess_risk(
        self, 
        agent_id: str, 
        service_id: str, 
        estimated_cost: float,
        agent_priority: str,
        context: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Analyze request and return (risk_level, risk_reason).
        """
        # Pattern 1: Burst detection (>5 calls in last minute from same agent)
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        recent_calls = [
            c for c in self.call_history 
            if c['agent_id'] == agent_id and c['timestamp'] > minute_ago
        ]
        
        if len(recent_calls) > 5:
            total_recent_cost = sum(c['cost'] for c in recent_calls)
            if total_recent_cost > 10.0:
                return ("RISK_BLOCK", f"Burst detected: {len(recent_calls)} calls in 1 min")
        
        # Pattern 2: First-time large call from low-priority agent
        agent_total_calls = len([c for c in self.call_history if c['agent_id'] == agent_id])
        if agent_priority == "LOW" and agent_total_calls < 3 and estimated_cost > 5.0:
            return ("RISK_REVIEW", f"First large call ({estimated_cost:.2f} MNEE) from low-priority agent")
        
        # Pattern 3: Provider failure rate
        failure_count = self.provider_failure_counts.get(service_id, 0)
        if failure_count > 3:
            return ("RISK_REVIEW", f"Provider {service_id} has {failure_count} recent failures")
        
        return ("RISK_OK", "No risk detected")
    
    def record_call(self, agent_id: str, service_id: str, cost: float, success: bool):
        """Record a call for pattern analysis"""
        self.call_history.append({
            'agent_id': agent_id,
            'service_id': service_id,
            'cost': cost,
            'timestamp': datetime.now(),
            'success': success
        })
        # Keep only recent history (last hour)
        hour_ago = datetime.now() - timedelta(hours=1)
        self.call_history = [c for c in self.call_history if c['timestamp'] > hour_ago]
        
        if not success:
            self.provider_failure_counts[service_id] += 1

class PolicyEngine:
    """
    Enhanced Policy Engine for the Billing Hub.
    Enforces Project and Agent level budgets.
    """
    
    def __init__(self, agents_path: str, services_path: str):
        self.projects: Dict[str, ProjectPolicy] = {}
        self.agents: Dict[str, AgentPolicy] = {}
        self.usage: Dict[str, UsageSnapshot] = {} # Key: agent_id (simplified)
        self.services: Dict[str, Any] = {} # Keep services as dicts or simple objects for now
        
        self.risk_engine = RiskEngine()
        
        # Initialize default project
        self.projects[DEFAULT_PROJECT_ID] = ProjectPolicy(
            project_id=DEFAULT_PROJECT_ID,
            name="General Operations",
            daily_budget_mnee=500.0, # High default cap
            hard_cap_mnee=10000.0
        )
        
        self.load_configs(agents_path, services_path)
    
    def load_configs(self, agents_path: str, services_path: str):
        # Load Services
        if os.path.exists(services_path):
            with open(services_path, 'r') as f:
                data = yaml.safe_load(f)
                for s in data.get('services', []):
                    # Store service config. Ideally utilize a ServiceConfig model.
                    # For compatibility with existing code that accesses .unitPrice etc.
                    # we can use a simple object or dict wrapper.
                    # For now, storing as SimpleNamespace or keeping compatible class.
                    # Let's use a dynamic class to satisfy attribute access.
                    class ServiceObj:
                        def __init__(self, **kwargs):
                            self.__dict__.update(kwargs)
                    self.services[s['id']] = ServiceObj(**s)

        # Load Agents
        if os.path.exists(agents_path):
            with open(agents_path, 'r') as f:
                data = yaml.safe_load(f)
                for a in data.get('agents', []):
                    # Map legacy YAML to new AgentPolicy
                    policy = AgentPolicy(
                        agent_id=a['id'],
                        project_id=DEFAULT_PROJECT_ID, # Assign to default project
                        role="worker",
                        daily_budget_mnee=a.get('dailyBudget', 10.0),
                        max_single_call_mnee=a.get('maxPerCall', 5.0),
                        priority=a.get('priority', "NORMAL")
                    )
                    self.agents[a['id']] = policy
                    
                    # Initialize usage snapshot
                    self.usage[a['id']] = UsageSnapshot(
                        project_id=DEFAULT_PROJECT_ID,
                        agent_id=a['id']
                    )
                    # Pre-fill if there was legacy 'currentDailySpend' in YAML? No, usually runtime.

    def evaluate(
        self,
        agent_id: str,
        service_id: str,
        estimated_cost: float,
        quantity: int,
        task_id: str,
        payload: Dict[str, Any]
    ) -> PolicyDecision:
        
        agent = self.agents.get(agent_id)
        service = self.services.get(service_id)
        usage = self.usage.get(agent_id)
        
        # 1. Basic Validation
        if not agent:
            return PolicyDecision(action="DENY", approved_quantity=0, risk_level="RISK_OK", reason=f"Agent {agent_id} unknown")
        if not service:
            return PolicyDecision(action="DENY", approved_quantity=0, risk_level="RISK_OK", reason=f"Service {service_id} unknown")
        if not service.active:
            return PolicyDecision(action="DENY", approved_quantity=0, risk_level="RISK_OK", reason=f"Service {service_id} inactive")

        project = self.projects.get(agent.project_id)
        
        # 2. Project Level Checks
        if project:
            # Check service allow/deny list
            if project.deny_services and service_id in project.deny_services:
                return PolicyDecision(action="DENY", approved_quantity=0, risk_level="RISK_BLOCK", reason=f"Service blocked by project {project.name}")
            if project.allow_services and service_id not in project.allow_services:
                return PolicyDecision(action="DENY", approved_quantity=0, risk_level="RISK_REVIEW", reason=f"Service not whitelisted for project {project.name}")

        # 3. Risk Assessment
        risk_level, risk_reason = self.risk_engine.assess_risk(
            agent_id=agent_id, 
            service_id=service_id, 
            estimated_cost=estimated_cost, 
            agent_priority=agent.priority,
            context={'task_id': task_id}
        )
        
        if risk_level == "RISK_BLOCK":
             return PolicyDecision(action="DENY", approved_quantity=0, risk_level="RISK_BLOCK", reason=f"Risk: {risk_reason}")

        # 4. Budget Checks
        
        # 4.1 Agent Single Call Limit
        if estimated_cost > agent.max_single_call_mnee:
             return PolicyDecision(action="DENY", approved_quantity=0, risk_level="RISK_BLOCK", reason=f"Exceeds single call limit ({agent.max_single_call_mnee} MNEE)")

        # 4.2 Agent Daily Budget
        new_spent = usage.spent_today_mnee + estimated_cost
        if new_spent > agent.daily_budget_mnee:
             return PolicyDecision(action="DENY", approved_quantity=0, risk_level="RISK_BLOCK", reason=f"Daily budget exceeded ({usage.spent_today_mnee:.2f}/{agent.daily_budget_mnee} MNEE)")

        # 5. Project Daily Budget (Aggregate)
        # Calculate total project spend (simple iteration for now)
        project_spent = sum(u.spent_today_mnee for u in self.usage.values() if u.project_id == agent.project_id)
        if project and (project_spent + estimated_cost > project.daily_budget_mnee):
             return PolicyDecision(action="DENY", approved_quantity=0, risk_level="RISK_BLOCK", reason=f"Project daily budget exceeded")

        # Approved
        return PolicyDecision(
            action="ALLOW",
            approved_quantity=quantity,
            risk_level=risk_level,
            reason="Approved" + (f" ({risk_reason})" if risk_level != "RISK_OK" else "")
        )

    def record_call_result(self, agent_id: str, service_id: str, cost: float, success: bool):
        """Update usage stats"""
        self.risk_engine.record_call(agent_id, service_id, cost, success)
        
        if success and agent_id in self.usage:
            self.usage[agent_id].spent_today_mnee += cost
            self.usage[agent_id].spent_total_mnee += cost
            print(f"[POLICY] {agent_id} spent {cost} MNEE. Total today: {self.usage[agent_id].spent_today_mnee}")
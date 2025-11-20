import yaml
import os
from typing import Dict, Optional, List, Literal, Any
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from collections import defaultdict

class PolicyDecision(BaseModel):
    """Enhanced policy decision with risk assessment"""
    action: Literal["ALLOW", "DENY", "DOWNGRADE"]
    approved_quantity: int
    risk_level: Literal["RISK_OK", "RISK_REVIEW", "RISK_BLOCK"]
    reason: str

class AgentConfig(BaseModel):
    id: str
    priority: str  # HIGH, MEDIUM, LOW
    dailyBudget: float
    maxPerCall: float
    currentDailySpend: float = 0.0

class ServiceConfig(BaseModel):
    id: str
    unitPrice: float
    providerAddress: str
    active: bool
    maxDailySpending: Optional[float] = None
    allowedAgents: Optional[List[str]] = None
    blockedAgents: Optional[List[str]] = None
    isVerified: bool = False
    metadataURI: str = ""

class RiskEngine:
    """
    Risk assessment engine for detecting suspicious patterns.
    Even simple rules for MVP.
    """
    
    def __init__(self):
        # Track call patterns
        self.call_history = []  # List of {agent_id, service_id, cost, timestamp}
        self.agent_call_counts = defaultdict(int)  # {(agent_id, time_window): count}
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
        
        Risk patterns:
        1. Burst of high-value calls in short time → RISK_BLOCK
        2. First-time large call from low-priority agent → RISK_REVIEW  
        3. Provider with repeated failures → RISK_REVIEW
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
            if total_recent_cost > 10.0:  # High value threshold
                return ("RISK_BLOCK", f"Burst detected: {len(recent_calls)} calls in 1 min, total cost {total_recent_cost:.2f} MNEE")
        
        # Pattern 2: First-time large call from low-priority agent
        agent_total_calls = len([c for c in self.call_history if c['agent_id'] == agent_id])
        
        if agent_priority == "LOW" and agent_total_calls < 3 and estimated_cost > 5.0:
            return ("RISK_REVIEW", f"First large call ({estimated_cost:.2f} MNEE) from low-priority agent")
        
        # Pattern 3: Provider failure rate
        failure_count = self.provider_failure_counts.get(service_id, 0)
        if failure_count > 3:
            return ("RISK_REVIEW", f"Provider {service_id} has {failure_count} recent failures")
        
        # Pattern 4: Unusually large single call
        if estimated_cost > 20.0:
            return ("RISK_REVIEW", f"Unusually large single call: {estimated_cost:.2f} MNEE")
        
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
        
        # Update failure counts
        if not success:
            self.provider_failure_counts[service_id] += 1
    
    def record_provider_failure(self, service_id: str):
        """Record provider failure"""
        self.provider_failure_counts[service_id] += 1


class PolicyEngine:
    """
    Enhanced Policy Engine with integrated Risk Assessment.
    """
    
    def __init__(self, agents_path: str, services_path: str):
        self.agents: Dict[str, AgentConfig] = {}
        self.services: Dict[str, ServiceConfig] = {}
        self.risk_engine = RiskEngine()
        self.load_configs(agents_path, services_path)
    
    def load_configs(self, agents_path: str, services_path: str):
        with open(agents_path, 'r') as f:
            data = yaml.safe_load(f)
            for a in data['agents']:
                self.agents[a['id']] = AgentConfig(**a)
        
        with open(services_path, 'r') as f:
            data = yaml.safe_load(f)
            for s in data['services']:
                self.services[s['id']] = ServiceConfig(**s)
    
    def evaluate(
        self,
        agent_id: str,
        service_id: str,
        estimated_cost: float,
        quantity: int,
        task_id: str,
        payload: Dict[str, Any]
    ) -> PolicyDecision:
        """
        Comprehensive evaluation combining budget policy and risk assessment.
        
        Flow:
        1. Validate agent and service exist
        2. Check service access control (allowedAgents/blockedAgents)
        3. Run risk assessment
        4. Check budget constraints
        5. Return combined decision
        """
        
        # Step 1: Validate existence
        agent = self.agents.get(agent_id)
        service = self.services.get(service_id)
        
        if not agent:
            return PolicyDecision(
                action="DENY",
                approved_quantity=0,
                risk_level="RISK_OK",
                reason=f"Agent {agent_id} not found in configuration"
            )
        
        if not service:
            return PolicyDecision(
                action="DENY",
                approved_quantity=0,
                risk_level="RISK_OK",
                reason=f"Service {service_id} not registered"
            )
        
        if not service.active:
            return PolicyDecision(
                action="DENY",
                approved_quantity=0,
                risk_level="RISK_OK",
                reason=f"Service {service_id} is not active"
            )
        
        # Step 2: Access control
        if service.blockedAgents and agent_id in service.blockedAgents:
            return PolicyDecision(
                action="DENY",
                approved_quantity=0,
                risk_level="RISK_OK",
                reason=f"Agent {agent_id} is blocked from using {service_id}"
            )
        
        if service.allowedAgents and agent_id not in service.allowedAgents:
            return PolicyDecision(
                action="DENY",
                approved_quantity=0,
                risk_level="RISK_OK",
                reason=f"Agent {agent_id} is not in allowed list for {service_id}"
            )
        
        # Step 3: Risk assessment
        risk_level, risk_reason = self.risk_engine.assess_risk(
            agent_id=agent_id,
            service_id=service_id,
            estimated_cost=estimated_cost,
            agent_priority=agent.priority,
            context={'task_id': task_id, 'payload': payload}
        )
        
        if risk_level == "RISK_BLOCK":
            return PolicyDecision(
                action="DENY",
                approved_quantity=0,
                risk_level=risk_level,
                reason=f"Risk check failed: {risk_reason}"
            )
        
        # Step 4: Budget checks
        
        # 4.1: Check maxPerCall
        if estimated_cost > agent.maxPerCall:
            # Try to downgrade quantity
            max_quantity = int(agent.maxPerCall / service.unitPrice)
            if max_quantity > 0:
                return PolicyDecision(
                    action="DOWNGRADE",
                    approved_quantity=max_quantity,
                    risk_level=risk_level,
                    reason=f"Cost {estimated_cost:.2f} exceeds maxPerCall {agent.maxPerCall:.2f}. Downgraded to quantity={max_quantity}"
                )
            else:
                return PolicyDecision(
                    action="DENY",
                    approved_quantity=0,
                    risk_level=risk_level,
                    reason=f"Cost {estimated_cost:.2f} exceeds maxPerCall {agent.maxPerCall:.2f}"
                )
        
        # 4.2: Check daily budget
        remaining_budget = agent.dailyBudget - agent.currentDailySpend
        
        if estimated_cost > remaining_budget:
            # Try to downgrade
            max_quantity = int(remaining_budget / service.unitPrice)
            if max_quantity > 0:
                return PolicyDecision(
                    action="DOWNGRADE",
                    approved_quantity=max_quantity,
                    risk_level=risk_level,
                    reason=f"Insufficient daily budget. Remaining: {remaining_budget:.2f} MNEE. Downgraded to quantity={max_quantity}"
                )
            else:
                return PolicyDecision(
                    action="DENY",
                    approved_quantity=0,
                    risk_level=risk_level,
                    reason=f"Insufficient daily budget. Remaining: {remaining_budget:.2f} MNEE"
                )
        
        # 4.3: Check service daily spending limit (if configured)
        if service.maxDailySpending:
            # TODO: Track per-service daily spending
            pass
        
        # Step 5: All checks passed
        return PolicyDecision(
            action="ALLOW",
            approved_quantity=quantity,
            risk_level=risk_level,
            reason="Approved" + (f" (Risk: {risk_reason})" if risk_level == "RISK_REVIEW" else "")
        )
    
    def record_call_result(self, agent_id: str, service_id: str, cost: float, success: bool):
        """
        Record call result for risk pattern analysis and update agent spending.
        """
        self.risk_engine.record_call(agent_id, service_id, cost, success)
        
        # Update agent's daily spending if call was successful
        if success:
            agent = self.agents.get(agent_id)
            if agent:
                agent.currentDailySpend += cost
                print(f"[POLICY_ENGINE] Updated {agent_id} spending: {agent.currentDailySpend:.2f} / {agent.dailyBudget:.2f} MNEE")

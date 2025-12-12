"""
MNEE Nexus / Omni-Agent - LangGraph Implementation
Stateful multi-agent orchestrator with payment enforcement
"""
import os
import sys
import uuid
import json
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from policy.engine import PolicyEngine
from payment.client import PaymentClient
from payment.wrapper import PaidToolWrapper
from payment.a2a_client import get_a2a_client
from policy.logger import SystemLogger
from agents.tools import definitions

from .state import GraphState
from .nodes.planner import planner_node
from .nodes.guardian import guardian_node
from .nodes.executor import executor_node
from .nodes.summarizer import summarizer_node
from .nodes.feedback import policy_feedback_node
from .nodes.verifier import verifier_node, get_verifier
from .nodes.escrow import escrow_lock_node, escrow_release_node, get_escrow_manager
from .registry import get_registry


# ============================================================ 
# Tool Registry / Implementation
# ============================================================ 
class PaidServiceTools:
    """
    Registry of tools available to the Agent.
    These methods are called by the Executor based on the plan.
    """
    
    def __init__(self, wrapper: PaidToolWrapper, agent_id: str):
        self.wrapper = wrapper
        self.agent_id = agent_id
    
    def get_quote(self, service_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get a quote from the Merchant Agent (Free tool)"""
        task_id = str(uuid.uuid4())
        # Informational only
        return definitions.request_quote_tool(service_id, task_id, payload)

    def purchase_service(self, quote: Dict[str, Any]) -> Dict[str, Any]:
        """Execute payment based on quote and redeem service"""
        service_id = quote.get('serviceId')
        try:
            unit_price = float(quote.get('unitPriceMNEE', 0))
        except:
            unit_price = 0.0
            
        quantity = quote.get('quantity', 1)
        quote_id = quote.get('quoteId')
        
        payload_for_wrapper = {
            "quoteId": quote_id,
            "serviceId": service_id,
            "original_task_id": quote.get('taskId')
        }

        # We use the wrapper's manual execution method via the tool func
        # But wait, executor calls this function directly.
        # So THIS function must handle the payment logic or call wrapper.execute_with_payment
        
        # Ideally, purchase_service should be wrapped.
        # But since the price is dynamic (from quote), we need to use execute_with_payment manually here.
        
        return self.wrapper.execute_with_payment(
            tool_func=definitions.deliver_service_tool,
            service_id=service_id,
            agent_id=self.agent_id,
            payload_dict=payload_for_wrapper,
            quantity=quantity,
            override_price=unit_price
        )

    def image_gen(self, prompt: str) -> Dict[str, Any]:
        """Generate an image using IMAGE_GEN service"""
        def _call_service(task_id: str = None, service_call_hash: str = None, **kwargs):
            try:
                payload = {"prompt": prompt}
                if task_id: payload["taskId"] = task_id
                if service_call_hash: payload["serviceCallHash"] = service_call_hash
                
                resp = requests.post("http://localhost:8001/image/generate", json=payload, timeout=5)
                return resp.json()
            except Exception as e:
                return {"imageUrl": "https://placeholder.com/cyberpunk-avatar.png", "mock": True, "error": str(e)}
        
        service = self.wrapper.policy.services.get("IMAGE_GEN_PREMIUM")
        cost = service.unitPrice if service else 1.0
        # Use the wrapper decorator
        wrapped = self.wrapper.wrap(_call_service, "IMAGE_GEN_PREMIUM", self.agent_id, cost)
        return wrapped(payload_dict={"prompt": prompt})
    
    def price_oracle(self, symbol: str = "ETH") -> Dict[str, Any]:
        """Get crypto price"""
        def _call_service(task_id: str = None, service_call_hash: str = None, **kwargs):
            try:
                params = {"base": symbol, "quote": "MNEE"}
                if task_id: params["taskId"] = task_id
                if service_call_hash: params["serviceCallHash"] = service_call_hash
                
                resp = requests.get("http://localhost:8002/price", params=params, timeout=5)
                return resp.json()
            except Exception as e:
                return {"base": symbol, "quote": "MNEE", "price": 1234.56, "mock": True, "error": str(e)}
        
        service = self.wrapper.policy.services.get("PRICE_ORACLE")
        cost = service.unitPrice if service else 0.05
        wrapped = self.wrapper.wrap(_call_service, "PRICE_ORACLE", self.agent_id, cost)
        return wrapped(payload_dict={"symbol": symbol})
    
    def batch_compute(self, payload: str) -> Dict[str, Any]:
        """Submit batch job"""
        def _call_service(task_id: str = None, service_call_hash: str = None, **kwargs):
            try:
                data = {"data": payload}
                if task_id: data["taskId"] = task_id
                if service_call_hash: data["serviceCallHash"] = service_call_hash
                resp = requests.post("http://localhost:8003/batch/submit", json=data, timeout=5)
                return resp.json()
            except Exception as e:
                return {"jobId": f"mock-{uuid.uuid4().hex[:8]}", "status": "submitted", "mock": True, "error": str(e)}
        
        service = self.wrapper.policy.services.get("BATCH_COMPUTE")
        cost = service.unitPrice if service else 3.0
        wrapped = self.wrapper.wrap(_call_service, "BATCH_COMPUTE", self.agent_id, cost)
        return wrapped(payload_dict={"payload": payload})
    
    def log_archive(self, content: str) -> Dict[str, Any]:
        """Archive logs"""
        def _call_service(task_id: str = None, service_call_hash: str = None, **kwargs):
            try:
                data = {"content": content, "agent_id": self.agent_id}
                if task_id: data["taskId"] = task_id
                if service_call_hash: data["serviceCallHash"] = service_call_hash
                resp = requests.post("http://localhost:8004/logs/archive", json=data, timeout=5)
                return resp.json()
            except Exception as e:
                return {"archived": True, "storageId": f"mock-{uuid.uuid4().hex[:8]}", "mock": True, "error": str(e)}
        
        service = self.wrapper.policy.services.get("LOG_ARCHIVE")
        cost = service.unitPrice if service else 0.01
        wrapped = self.wrapper.wrap(_call_service, "LOG_ARCHIVE", self.agent_id, cost)
        return wrapped(payload_dict={"content": content})

    def respond(self, message: str) -> Dict[str, Any]:
        """Simple response tool"""
        return {"response": message}


# ============================================================ 
# OmniAgent Class
# ============================================================ 
class OmniAgent:
    """
    Main orchestrator using LangGraph stateful graph.
    """
    
    def __init__(self):
        # Load configurations
        backend_dir = Path(__file__).parent.parent
        project_root = backend_dir.parent
        
        default_agents_path = project_root / "config" / "agents.yaml"
        default_services_path = project_root / "config" / "services.yaml"
        
        self.policy_engine = PolicyEngine(
            agents_path=os.getenv("POLICY_CONFIG_PATH", str(default_agents_path)),
            services_path=os.getenv("SERVICE_CONFIG_PATH", str(default_services_path))
        )
        
        self.payment_client = PaymentClient(policy_engine=self.policy_engine)
        self.logger = SystemLogger()
        self.wrapper = PaidToolWrapper(
            self.policy_engine,
            self.payment_client,
            self.logger
        )
        
        # Tools instance - will be set per agent during run
        self.current_tools = None
        
        # A2A client for agent-to-agent payments
        self.a2a_client = get_a2a_client()
        
        # Escrow manager for trustless transactions
        self.escrow_manager = get_escrow_manager(self.a2a_client)
        
        # Verifier for task output verification
        self.verifier = get_verifier()
        
        # Agent registry for dynamic discovery
        self.registry = get_registry()
        
        # Build the graph
        self.graph = self._build_graph()
        
        print("[OMNI_AGENT] Initialized with LangGraph stateful orchestrator")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph stateful graph with Escrow-Verify-Release protocol.
        
        Flow:
        1. Planner -> Guardian -> Escrow Lock -> Executor -> Verifier -> Escrow Release -> Summarizer
        2. Guardian block -> Feedback -> Summarizer
        3. Executor early_exit -> Feedback -> Summarizer
        """
        workflow = StateGraph(GraphState)
        
        # Add Nodes
        workflow.add_node("planner", planner_node)
        workflow.add_node("guardian", lambda state: guardian_node(state, self.logger, self.policy_engine))
        workflow.add_node("escrow_lock", lambda state: escrow_lock_node(state, self.escrow_manager))
        workflow.add_node("executor", lambda state: executor_node(state, self.current_tools, self.policy_engine, self.a2a_client))
        workflow.add_node("verifier", lambda state: verifier_node(state, self.verifier))
        workflow.add_node("escrow_release", lambda state: escrow_release_node(state, self.escrow_manager))
        workflow.add_node("summarizer", summarizer_node)
        workflow.add_node("feedback", policy_feedback_node)
        
        # Define Edges
        workflow.set_entry_point("planner")
        
        workflow.add_edge("planner", "guardian")
        
        # Guardian -> Escrow Lock or Feedback
        def check_guardian(state: GraphState) -> str:
            if state.guardian_block:
                return "feedback"
            return "escrow_lock"
            
        workflow.add_conditional_edges("guardian", check_guardian)
        
        # Escrow Lock -> Executor
        workflow.add_edge("escrow_lock", "executor")
        
        # Executor -> Verifier or Feedback (if early exit)
        def check_executor(state: GraphState) -> str:
            if state.early_exit:
                return "feedback"
            return "verifier"
            
        workflow.add_conditional_edges("executor", check_executor)
        
        # Verifier -> Escrow Release
        workflow.add_edge("verifier", "escrow_release")
        
        # Escrow Release -> Summarizer
        workflow.add_edge("escrow_release", "summarizer")
        
        workflow.add_edge("feedback", "summarizer")
        workflow.add_edge("summarizer", END)
        
        return workflow.compile()
    
    def run(self, agent_id: str, user_message: str) -> Dict[str, Any]:
        """
        Run the agent graph with a user message.
        """
        # Initialize state
        initial_state = GraphState(
            task_id=str(uuid.uuid4()),
            user_id="user-123", # Mock
            active_agent=agent_id,
            goal=user_message,
            messages=[{"role": "user", "content": user_message}],
            plan=[],
            steps=[],
            current_step_index=0,
            final_answer=None
        )
        
        # Set tools instance for this execution
        self.current_tools = PaidServiceTools(self.wrapper, agent_id)
        
        try:
            print(f"\n{'='*60}")
            print(f"[OMNI_AGENT] Starting execution for agent={agent_id}")
            print(f"{'='*60}\n")
            
            final_state = self.graph.invoke(initial_state)
            
            print(f"\n{'='*60}")
            print(f"[OMNI_AGENT] Execution complete")
            print(f"{'='*60}\n")
            
            # Extract steps for API response
            steps_data = [s.model_dump() for s in final_state.get("steps", [])]
            a2a_transfers_data = [t.model_dump() for t in final_state.get("a2a_transfers", [])]
            escrow_records_data = [e.model_dump() for e in final_state.get("escrow_records", [])]
            
            return {
                "output": final_state.get("final_answer", "No answer generated."),
                "agent_id": agent_id,
                "messages": final_state.get("messages", []),
                "steps": steps_data,
                "a2a_transfers": a2a_transfers_data,
                "escrow_records": escrow_records_data,
                "guardian_reasoning": final_state.get("guardian_reasoning"),
                "guardian_risk_score": final_state.get("guardian_risk_score", 0),
                "guardian_block": final_state.get("guardian_block", False)
            }
            
        finally:
            self.current_tools = None

# ============================================================ 
# CLI Test Interface
# ============================================================ 
if __name__ == "__main__":
    agent = OmniAgent()
    
    print("\n" + "="*60)
    print("MNEE Nexus / Omni-Agent - Interactive Test")
    print("="*60)
    
    test_scenarios = [
        ("user-agent", "我想买个赛博朋克头像"),
        ("user-agent", "Buy me a premium image"),
    ]
    
    for agent_id, message in test_scenarios:
        print(f"\n{'='*60}")
        print(f"Test: agent={agent_id}")
        print(f"Message: {message}")
        print(f"{'='*60}")
        
        result = agent.run(agent_id, message)
        
        print(f"\n[RESULT]")
        print(result['output'])
        print()
        
        input("Press Enter for next test...")

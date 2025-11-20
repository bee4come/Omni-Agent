"""
MNEE Nexus / Omni-Agent - LangGraph Implementation
Stateful multi-agent orchestrator with payment enforcement
"""
from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, FunctionMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_aws import ChatBedrockConverse
from langchain_openai import ChatOpenAI
import operator
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from policy.engine import PolicyEngine
from payment.client import PaymentClient
from payment.wrapper import PaidToolWrapper
from policy.logger import SystemLogger
import requests
import json
import uuid


# ============================================================
# State Definition
# ============================================================
class AgentState(TypedDict):
    """State shared across all nodes in the graph"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    agent_id: str
    current_task: str
    pending_tool_calls: List[Dict[str, Any]]
    payment_results: List[Dict[str, Any]]
    policy_feedback: List[str]
    retry_count: int
    final_output: str


# ============================================================
# LLM Initialization Helper
# ============================================================
def create_llm() -> Optional[Any]:
    """
    Create LLM instance based on environment variables.
    Priority: AWS Bedrock > OpenAI > None (Mock mode)
    """
    if os.getenv("AWS_ACCESS_KEY_ID"):
        print("[LLM] Using AWS Bedrock Converse (Claude Haiku 4.5 Cross-region)...")
        return ChatBedrockConverse(
            model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
            temperature=0,
            region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        )
    elif os.getenv("OPENAI_API_KEY"):
        print("[LLM] Using OpenAI GPT-4...")
        return ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
    else:
        print("[LLM] WARNING: No LLM credentials found. Using keyword-based fallback routing.")
        return None


# ============================================================
# Fallback Keyword-based Router (when no LLM available)
# ============================================================
def fallback_keyword_router(message_content: str) -> Dict[str, Any]:
    """Simple keyword-based routing when LLM is not available"""
    content_lower = message_content.lower()
    
    if any(word in content_lower for word in ['image', 'generate', 'picture', 'avatar', '头像', '图片', '生成']):
        return {
            "action": "image_gen",
            "reasoning": "User wants to generate an image",
            "parameters": {"prompt": message_content}
        }
    elif any(word in content_lower for word in ['price', 'eth', 'mnee', '价格', '换算']):
        return {
            "action": "price_oracle",
            "reasoning": "User wants price information",
            "parameters": {"symbol": "ETH"}
        }
    elif any(word in content_lower for word in ['batch', 'compute', 'job', '批量', '计算']):
        return {
            "action": "batch_compute",
            "reasoning": "User wants to run batch computation",
            "parameters": {"payload": message_content}
        }
    elif any(word in content_lower for word in ['archive', 'log', '归档']):
        return {
            "action": "log_archive",
            "reasoning": "User wants to archive logs",
            "parameters": {"content": message_content}
        }
    else:
        return {
            "action": "respond",
            "reasoning": "General conversation",
            "parameters": {"response": f"I understand you said: {message_content}"}
        }


# ============================================================
# Tool Implementations with Payment Integration
# ============================================================
class PaidServiceTools:
    """Tools that require MNEE payment before execution"""
    
    def __init__(self, wrapper: PaidToolWrapper, agent_id: str):
        self.wrapper = wrapper
        self.agent_id = agent_id
    
    def image_gen(self, prompt: str) -> Dict[str, Any]:
        """Generate an image using IMAGE_GEN service"""
        def _call_service(task_id: str = None, service_call_hash: str = None, **kwargs):
            try:
                payload = {"prompt": prompt}
                if task_id:
                    payload["taskId"] = task_id
                if service_call_hash:
                    payload["serviceCallHash"] = service_call_hash
                
                resp = requests.post(
                    "http://localhost:8001/image/generate",
                    json=payload,
                    timeout=5
                )
                return resp.json()
            except Exception as e:
                return {"imageUrl": "https://placeholder.com/cyberpunk-avatar.png", 
                        "mock": True, "note": f"Provider unavailable: {e}"}
        
        service = self.wrapper.policy.services.get("IMAGE_GEN_PREMIUM")
        cost = service.unitPrice if service else 1.0
        wrapped = self.wrapper.wrap(_call_service, "IMAGE_GEN_PREMIUM", self.agent_id, cost)
        return wrapped(payload_dict={"prompt": prompt})
    
    def price_oracle(self, symbol: str = "ETH") -> Dict[str, Any]:
        """Get crypto price from PRICE_ORACLE service"""
        def _call_service(task_id: str = None, service_call_hash: str = None, **kwargs):
            try:
                params = {"base": symbol, "quote": "MNEE"}
                if task_id:
                    params["taskId"] = task_id
                if service_call_hash:
                    params["serviceCallHash"] = service_call_hash
                
                resp = requests.get(
                    "http://localhost:8002/price",
                    params=params,
                    timeout=5
                )
                return resp.json()
            except Exception as e:
                # Mock response
                return {"base": symbol, "quote": "MNEE", "price": 1234.56, 
                        "mock": True, "note": f"Provider unavailable: {e}"}
        
        service = self.wrapper.policy.services.get("PRICE_ORACLE")
        cost = service.unitPrice if service else 0.05
        wrapped = self.wrapper.wrap(_call_service, "PRICE_ORACLE", self.agent_id, cost)
        return wrapped(payload_dict={"symbol": symbol})
    
    def batch_compute(self, payload: str) -> Dict[str, Any]:
        """Submit batch compute job via BATCH_COMPUTE service"""
        def _call_service(task_id: str = None, service_call_hash: str = None, **kwargs):
            try:
                request_payload = {"data": payload}
                if task_id:
                    request_payload["taskId"] = task_id
                if service_call_hash:
                    request_payload["serviceCallHash"] = service_call_hash
                
                resp = requests.post(
                    "http://localhost:8003/batch/submit",
                    json=request_payload,
                    timeout=5
                )
                return resp.json()
            except Exception as e:
                return {"jobId": f"mock-{uuid.uuid4().hex[:8]}", 
                        "status": "submitted", "mock": True, 
                        "note": f"Provider unavailable: {e}"}
        
        service = self.wrapper.policy.services.get("BATCH_COMPUTE")
        cost = service.unitPrice if service else 3.0
        wrapped = self.wrapper.wrap(_call_service, "BATCH_COMPUTE", self.agent_id, cost)
        return wrapped(payload_dict={"payload": payload})
    
    def log_archive(self, content: str) -> Dict[str, Any]:
        """Archive logs via LOG_ARCHIVE service"""
        def _call_service(task_id: str = None, service_call_hash: str = None, **kwargs):
            try:
                request_payload = {"content": content, "agent_id": self.agent_id}
                if task_id:
                    request_payload["taskId"] = task_id
                if service_call_hash:
                    request_payload["serviceCallHash"] = service_call_hash
                
                resp = requests.post(
                    "http://localhost:8004/logs/archive",
                    json=request_payload,
                    timeout=5
                )
                return resp.json()
            except Exception as e:
                return {"archived": True, 
                        "storageId": f"mock-storage-{uuid.uuid4().hex[:8]}", 
                        "mock": True, "note": f"Provider unavailable: {e}"}
        
        service = self.wrapper.policy.services.get("LOG_ARCHIVE")
        cost = service.unitPrice if service else 0.01
        wrapped = self.wrapper.wrap(_call_service, "LOG_ARCHIVE", self.agent_id, cost)
        return wrapped(payload_dict={"content": content})


# ============================================================
# Graph Nodes
# ============================================================

def user_input_node(state: AgentState) -> AgentState:
    """Entry point: Receives user message"""
    print(f"\n[USER_INPUT_NODE] Agent={state['agent_id']}, Message Count={len(state['messages'])}")
    return state


def planning_node(state: AgentState, llm: Optional[Any], tools: PaidServiceTools) -> AgentState:
    """Planning/Routing: Analyze user intent and decide which tools to call"""
    print(f"\n[PLANNING_NODE] Analyzing request...")
    
    last_message = state['messages'][-1].content if state['messages'] else ""
    
    if llm:
        # Use real LLM to determine action
        try:
            system_prompt = f"""You are agent '{state['agent_id']}' in the MNEE payment orchestration system.
Analyze the user's request and determine which action to take.
Respond with ONLY a JSON object in this format:
{{
    "action": "image_gen" | "price_oracle" | "batch_compute" | "log_archive" | "respond",
    "reasoning": "explanation of your decision",
    "parameters": {{relevant parameters}}
}}

Available actions:
- image_gen: Generate images (requires prompt)
- price_oracle: Get crypto prices (requires symbol like ETH)
- batch_compute: Run batch computations (requires payload/description)
- log_archive: Archive logs (requires content)
- respond: Just respond to user without tool call"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": last_message}
            ]
            
            response = llm.invoke(messages)
            response_content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to parse JSON from response
            decision = json.loads(response_content)
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"[PLANNING_NODE] LLM response parsing failed: {e}, using fallback")
            decision = fallback_keyword_router(last_message)
    else:
        # Use fallback keyword router
        decision = fallback_keyword_router(last_message)
    
    action = decision.get('action')
    params = decision.get('parameters', {})
    
    print(f"[PLANNING_NODE] Decision: {action}")
    
    # Add tool call to pending list
    state['pending_tool_calls'].append({
        'action': action,
        'parameters': params,
        'reasoning': decision.get('reasoning', '')
    })
    
    return state


def tool_execution_node(state: AgentState, tools: PaidServiceTools) -> AgentState:
    """Execute tool calls with payment enforcement"""
    print(f"\n[TOOL_EXECUTION_NODE] Pending calls: {len(state['pending_tool_calls'])}")
    
    if not state['pending_tool_calls']:
        return state
    
    # Process first pending call
    call = state['pending_tool_calls'][0]
    action = call['action']
    params = call['parameters']
    
    result = None
    
    try:
        if action == 'image_gen':
            result = tools.image_gen(params.get('prompt', ''))
        elif action == 'price_oracle':
            result = tools.price_oracle(params.get('symbol', 'ETH'))
        elif action == 'batch_compute':
            result = tools.batch_compute(params.get('payload', ''))
        elif action == 'log_archive':
            result = tools.log_archive(params.get('content', ''))
        elif action == 'respond':
            result = {'response': params.get('response', 'OK')}
        else:
            result = {'error': f'Unknown action: {action}'}
        
        # Check if payment was rejected
        if isinstance(result, dict) and result.get('error') == 'Policy Rejected':
            state['policy_feedback'].append(
                f"⚠️ Payment rejected for {action}: {result.get('reason', 'Unknown')}"
            )
            print(f"[TOOL_EXECUTION_NODE] Policy rejected: {result.get('reason')}")
        else:
            state['payment_results'].append({
                'action': action,
                'result': result,
                'task_id': result.get('_task_id') if isinstance(result, dict) else None,
                'tx_hash': result.get('_payment_tx') if isinstance(result, dict) else None
            })
            print(f"[TOOL_EXECUTION_NODE] Success: {action}")
    
    except Exception as e:
        print(f"[TOOL_EXECUTION_NODE] Error: {e}")
        state['payment_results'].append({
            'action': action,
            'result': {'error': str(e)}
        })
    
    # Remove processed call
    state['pending_tool_calls'] = state['pending_tool_calls'][1:]
    
    return state


def policy_feedback_node(state: AgentState) -> AgentState:
    """Handle policy rejections and provide user feedback"""
    print(f"\n[POLICY_FEEDBACK_NODE] Feedback count: {len(state['policy_feedback'])}")
    
    if state['policy_feedback']:
        # Aggregate feedback
        feedback_text = "\n".join(state['policy_feedback'])
        state['messages'].append(AIMessage(content=f"Policy Feedback:\n{feedback_text}"))
    
    return state


def output_synthesis_node(state: AgentState) -> AgentState:
    """Synthesize final response from tool results"""
    print(f"\n[OUTPUT_SYNTHESIS_NODE] Synthesizing from {len(state['payment_results'])} results")
    
    if not state['payment_results']:
        state['final_output'] = "No results to display."
        return state
    
    output_parts = []
    
    for pr in state['payment_results']:
        action = pr['action']
        result = pr['result']
        
        if isinstance(result, dict):
            if result.get('error'):
                output_parts.append(f"❌ {action}: {result['error']}")
            elif action == 'image_gen':
                url = result.get('imageUrl', 'N/A')
                mock_note = " (Mock)" if result.get('mock') else ""
                output_parts.append(f"🖼️ Image generated{mock_note}: {url}")
            elif action == 'price_oracle':
                price = result.get('price', 'N/A')
                base = result.get('base', 'N/A')
                quote = result.get('quote', 'N/A')
                mock_note = " (Mock)" if result.get('mock') else ""
                output_parts.append(f"💰 {base}/{quote} Price{mock_note}: {price}")
            elif action == 'batch_compute':
                job_id = result.get('jobId', 'N/A')
                status = result.get('status', 'N/A')
                mock_note = " (Mock)" if result.get('mock') else ""
                output_parts.append(f"⚙️ Batch Job{mock_note}: {job_id} - Status: {status}")
            elif action == 'log_archive':
                storage_id = result.get('storageId', 'N/A')
                mock_note = " (Mock)" if result.get('mock') else ""
                output_parts.append(f"📦 Archived{mock_note}: {storage_id}")
            elif action == 'respond':
                output_parts.append(f"💬 {result.get('response', '')}")
        
        # Include payment info
        if pr.get('tx_hash'):
            output_parts.append(f"  ├─ Payment TX: {pr['tx_hash'][:16]}...")
        if pr.get('task_id'):
            output_parts.append(f"  └─ Task ID: {pr['task_id'][:16]}...")
    
    state['final_output'] = "\n\n".join(output_parts)
    state['messages'].append(AIMessage(content=state['final_output']))
    
    return state


def should_continue(state: AgentState) -> str:
    """Routing: Decide whether to continue processing or end"""
    # If there are pending tool calls, execute them
    if state['pending_tool_calls']:
        return "execute_tools"
    
    # If no results yet and retry count is low, go back to planning
    if not state['payment_results'] and state['retry_count'] < 2:
        state['retry_count'] += 1
        return "planning"
    
    # Otherwise, synthesize output
    return "output"


# ============================================================
# OmniAgent Class - Main Interface
# ============================================================
class OmniAgent:
    """
    Main orchestrator using LangGraph stateful graph.
    Manages multiple agents with shared treasury and policy enforcement.
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
        
        self.payment_client = PaymentClient()
        self.logger = SystemLogger()
        self.wrapper = PaidToolWrapper(
            self.policy_engine,
            self.payment_client,
            self.logger
        )
        
        # Initialize LLM (Bedrock > OpenAI > None)
        self.llm = create_llm()
        
        # Tools instance - will be set per agent during run
        self.current_tools = None
        
        # Build the graph
        self.graph = self._build_graph()
        
        print("[OMNI_AGENT] Initialized with LangGraph stateful orchestrator")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph stateful graph"""
        workflow = StateGraph(AgentState)
        
        # Add nodes (tools will be accessed via self.current_tools)
        workflow.add_node("user_input", user_input_node)
        workflow.add_node("planning", lambda state: planning_node(state, self.llm, self.current_tools))
        workflow.add_node("execute_tools", lambda state: tool_execution_node(state, self.current_tools))
        workflow.add_node("policy_feedback", policy_feedback_node)
        workflow.add_node("output", output_synthesis_node)
        
        # Define edges
        workflow.set_entry_point("user_input")
        workflow.add_edge("user_input", "planning")
        
        # Conditional routing from planning
        workflow.add_conditional_edges(
            "planning",
            should_continue,
            {
                "execute_tools": "execute_tools",
                "planning": "planning",
                "output": "policy_feedback"
            }
        )
        
        # From tool execution, check if more tools pending
        workflow.add_conditional_edges(
            "execute_tools",
            should_continue,
            {
                "execute_tools": "execute_tools",
                "planning": "planning",
                "output": "policy_feedback"
            }
        )
        
        workflow.add_edge("policy_feedback", "output")
        workflow.add_edge("output", END)
        
        return workflow.compile()
    
    def run(self, agent_id: str, user_message: str) -> Dict[str, Any]:
        """
        Run the agent graph with a user message.
        
        Args:
            agent_id: The agent making the request (e.g., 'user-agent', 'batch-agent')
            user_message: The user's input message
        
        Returns:
            Dict with 'output' and execution metadata
        """
        # Initialize state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=user_message)],
            "agent_id": agent_id,
            "current_task": user_message,
            "pending_tool_calls": [],
            "payment_results": [],
            "policy_feedback": [],
            "retry_count": 0,
            "final_output": ""
        }
        
        # Set tools instance for this agent (accessed by nodes via self.current_tools)
        self.current_tools = PaidServiceTools(self.wrapper, agent_id)
        
        try:
            # Execute graph
            print(f"\n{'='*60}")
            print(f"[OMNI_AGENT] Starting execution for agent={agent_id}")
            print(f"{'='*60}")
            
            final_state = self.graph.invoke(initial_state)
            
            print(f"\n{'='*60}")
            print(f"[OMNI_AGENT] Execution complete")
            print(f"{'='*60}\n")
            
            return {
                "output": final_state['final_output'],
                "agent_id": agent_id,
                "messages": [msg.content for msg in final_state['messages']],
                "payment_results": final_state['payment_results'],
                "policy_feedback": final_state['policy_feedback']
            }
        
        finally:
            # Clean up
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
        ("user-agent", "帮我生成一张赛博朋克风的 Twitter 头像"),
        ("user-agent", "现在 ETH 什么价格？100 MNEE 大约多少 ETH？"),
        ("batch-agent", "Run a large batch computation job with 100 iterations"),
        ("user-agent", "Archive this conversation"),
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

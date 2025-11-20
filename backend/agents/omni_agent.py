from langchain_aws import ChatBedrockConverse
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import StructuredTool

from agents.tools.definitions import (
    generate_image_tool,
    get_price_tool,
    submit_batch_job_tool,
    archive_log_tool
)
from policy.engine import PolicyEngine
from policy.logger import SystemLogger
from payment.client import PaymentClient
from payment.wrapper import PaidToolWrapper
import os

class OmniAgent:
    def __init__(self):
        # Get absolute paths for config files
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(backend_dir)
        
        default_agents_path = os.path.join(project_root, "config", "agents.yaml")
        default_services_path = os.path.join(project_root, "config", "services.yaml")
        
        self.policy_engine = PolicyEngine(
            agents_path=os.getenv("POLICY_CONFIG_PATH", default_agents_path),
            services_path=os.getenv("SERVICE_CONFIG_PATH", default_services_path)
        )
        self.payment_client = PaymentClient()
        self.logger = SystemLogger()
        self.wrapper = PaidToolWrapper(self.policy_engine, self.payment_client, self.logger)
        
        # Initialize LLM
        if os.getenv("AWS_ACCESS_KEY_ID"):
            print("Using AWS Bedrock Converse (Claude Haiku 4.5 Cross-region)...")
            self.llm = ChatBedrockConverse(
                model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
                temperature=0,
                region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
            )
        elif os.getenv("OPENAI_API_KEY"):
            print("Using OpenAI...")
            self.llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
        else:
            print("WARNING: No LLM credentials found. Using Mock Agent logic.")
            self.llm = None

    def create_agent(self, agent_id: str):
        # 1. Wrap Tools with Payment Logic
        # We define them here so we can use them in the mock logic too if needed
        # But for the mock logic, we might just call them directly based on regex.
        
        tools = [
            StructuredTool.from_function(
                func=self.wrapper.wrap(
                    generate_image_tool, 
                    service_id="IMAGE_GEN_PREMIUM", 
                    agent_id=agent_id,
                    cost_per_call=1.0
                ),
                name="generate_image",
                description="Generate an image given a prompt. Costs 1.0 MNEE."
            ),
            StructuredTool.from_function(
                func=self.wrapper.wrap(
                    get_price_tool, 
                    service_id="PRICE_ORACLE", 
                    agent_id=agent_id,
                    cost_per_call=0.05
                ),
                name="get_price",
                description="Get the price of a token (e.g. ETH). Costs 0.05 MNEE."
            ),
            StructuredTool.from_function(
                func=self.wrapper.wrap(
                    submit_batch_job_tool, 
                    service_id="BATCH_COMPUTE", 
                    agent_id=agent_id,
                    cost_per_call=3.0
                ),
                name="submit_batch_job",
                description="Submit a heavy batch job. Costs 3.0 MNEE."
            ),
             StructuredTool.from_function(
                func=self.wrapper.wrap(
                    archive_log_tool, 
                    service_id="LOG_ARCHIVE", 
                    agent_id=agent_id,
                    cost_per_call=0.01
                ),
                name="archive_log",
                description="Archive a log entry. Costs 0.01 MNEE."
            )
        ]

        if self.llm:
            # 2. Create Real Agent
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"You are the {agent_id}. You have a budget and must pay for tools using MNEE. "
                           "If a tool is rejected due to policy, explain why to the user."),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            agent = create_tool_calling_agent(self.llm, tools, prompt)
            executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
            return executor
        else:
            # Return a Mock Executor that mimics the interface
            return MockExecutor(tools)

    def run(self, agent_id: str, user_input: str):
        executor = self.create_agent(agent_id)
        return executor.invoke({"input": user_input})

class MockExecutor:
    def __init__(self, tools):
        self.tools = {t.name: t for t in tools}

    def invoke(self, inputs):
        user_input = inputs["input"].lower()
        output = "I didn't understand that command."

        # Simple keyword matching for the demo
        if "image" in user_input or "avatar" in user_input:
            tool = self.tools["generate_image"]
            # We manually trigger the tool which includes the wrapper (Policy + Payment)
            try:
                res = tool.func(prompt=user_input)
                if "error" in res and res["error"] == "Policy Rejected":
                     output = f"Sorry, I cannot do that. {res['reason']}"
                else:
                     output = f"Here is your image: {res.get('url', 'Error generating')}"
            except Exception as e:
                 output = f"Tool execution failed: {e}"

        elif "price" in user_input:
            tool = self.tools["get_price"]
            try:
                res = tool.func(symbol="ETH")
                output = f"The price of ETH is ${res.get('price', '???')}"
            except Exception as e:
                 output = f"Tool execution failed: {e}"

        elif "batch" in user_input or "job" in user_input:
            tool = self.tools["submit_batch_job"]
            try:
                res = tool.func(payload="demo_job")
                if "error" in res and res["error"] == "Policy Rejected":
                     output = f"I cannot submit this job. {res['reason']}"
                else:
                     output = f"Job submitted! ID: {res.get('job_id')}"
            except Exception as e:
                 output = f"Tool execution failed: {e}"
        
        elif "log" in user_input:
             tool = self.tools["archive_log"]
             try:
                res = tool.func(content="User requested log", agent_id="mock-agent")
                output = f"Log archived. Total logs: {res.get('total_logs')}"
             except Exception as e:
                 output = f"Tool execution failed: {e}"

        return {"output": output}

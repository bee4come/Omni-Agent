try:
    from langchain.agents import AgentExecutor
    print("Success: from langchain.agents import AgentExecutor")
except ImportError as e:
    print(f"Failed: {e}")

try:
    from langchain.agents.agent import AgentExecutor
    print("Success: from langchain.agents.agent import AgentExecutor")
except ImportError as e:
    print(f"Failed: {e}")

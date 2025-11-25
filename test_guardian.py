import sys
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv("backend/.env")

# Force absolute paths for config
cwd = os.getcwd()
os.environ["POLICY_CONFIG_PATH"] = os.path.join(cwd, "config/agents.yaml")
os.environ["SERVICE_CONFIG_PATH"] = os.path.join(cwd, "config/services.yaml")

# Add backend to path
sys.path.append(os.path.join(cwd, "backend"))

from agents.omni_agent import OmniAgent

def test_guardian():
    print("Initializing OmniAgent...")
    agent = OmniAgent()
    
    print("\n--- Test: Image Generation (Standard Flow) ---")
    user_msg = "I need a cool cyberpunk avatar for my profile."
    print(f"User: {user_msg}")
    
    try:
        result = agent.run("user-agent", user_msg)
        
        print("\n[Execution Result]")
        print(result['output'])
        
        # Print State Dump to see Guardian Reasoning
        # (In a real app, the frontend would pull this from the API response)
        # Since result['steps'] doesn't include the graph state, I rely on the console logs I added in guardian.py
        
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    test_guardian()

#!/usr/bin/env python3
"""
Quick test script to verify the MNEE Nexus backend is working correctly.
Run this after starting the backend to test all major endpoints.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def make_request(method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
    url = f"{BASE_URL}{endpoint}"
    print(f"\n🔹 {method.upper()} {endpoint}")
    
    try:
        response = requests.request(method, url, **kwargs)
        print(f"   Status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            return data
        else:
            print(f"   Error: {response.text}")
            return {}
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return {}

def test_backend():
    print_section("Backend Health Check")
    make_request("GET", "/")
    
    print_section("Treasury & Agents")
    make_request("GET", "/treasury")
    make_request("GET", "/agents")
    make_request("GET", "/agents/user-agent")
    
    print_section("Services")
    make_request("GET", "/services")
    make_request("GET", "/services/IMAGE_GEN_PREMIUM")
    
    print_section("Statistics")
    make_request("GET", "/stats")
    
    print_section("Chat Test - Generate Image")
    make_request("POST", "/chat", json={
        "agent_id": "user-agent",
        "message": "Generate a cyberpunk avatar"
    })
    
    print_section("Transactions & Logs After Chat")
    make_request("GET", "/transactions", params={"limit": 10})
    make_request("GET", "/policy/logs", params={"limit": 10})
    
    print_section("Chat Test - Get Price")
    make_request("POST", "/chat", json={
        "agent_id": "user-agent",
        "message": "What is the price of ETH?"
    })
    
    print_section("Chat Test - Batch Job (May be rejected)")
    make_request("POST", "/chat", json={
        "agent_id": "batch-agent",
        "message": "Submit a batch job"
    })
    
    print_section("Final Stats")
    make_request("GET", "/stats")
    make_request("GET", "/treasury")
    
    print_section("Tests Complete!")
    print("✅ If you see responses above, the backend is working correctly.")
    print("📊 Check http://localhost:8000/docs for interactive API documentation.")

if __name__ == "__main__":
    print("="*60)
    print("  MNEE Nexus Backend Test Suite")
    print("="*60)
    print("\nMake sure the backend is running on http://localhost:8000")
    print("Press Ctrl+C to cancel...\n")
    
    try:
        input("Press ENTER to start tests...")
        test_backend()
    except KeyboardInterrupt:
        print("\n\n❌ Tests cancelled by user")

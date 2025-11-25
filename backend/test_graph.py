#!/usr/bin/env python3
"""
Test script for new LangGraph architecture.

Tests the complete flow:
  Planner -> Guardian -> Executor -> Summarizer

Run this after starting Hardhat and deploying contracts.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.graph import get_agent_graph


def test_simple_query():
    """Test 1: Simple price query (low cost, should succeed)"""
    print("\n" + "=" * 70)
    print("TEST 1: Simple Price Query")
    print("=" * 70)

    graph = get_agent_graph()

    result = graph.invoke(
        agent_id="user-agent",
        user_message="What is the current ETH price?"
    )

    print("\n[RESULT]")
    print(result['final_answer'])
    print(f"\nSteps executed: {len(result['steps'])}")
    print(f"Success: {result['success']}")

    return result['success']


def test_image_generation():
    """Test 2: Image generation (1 MNEE, should succeed for user-agent)"""
    print("\n" + "=" * 70)
    print("TEST 2: Image Generation")
    print("=" * 70)

    graph = get_agent_graph()

    result = graph.invoke(
        agent_id="user-agent",
        user_message="Generate a cyberpunk avatar"
    )

    print("\n[RESULT]")
    print(result['final_answer'])
    print(f"\nSteps executed: {len(result['steps'])}")
    print(f"Success: {result['success']}")

    # Check if payment was made
    for step in result['steps']:
        if step['tx_hash']:
            print(f"\nPayment TX: {step['tx_hash']}")
            print(f"Amount: {step['amount_mnee']} MNEE")

    return result['success']


def test_budget_limit():
    """Test 3: Expensive operation with low-priority agent (should be blocked)"""
    print("\n" + "=" * 70)
    print("TEST 3: Budget Limit (ops-agent with expensive call)")
    print("=" * 70)

    graph = get_agent_graph()

    result = graph.invoke(
        agent_id="ops-agent",
        user_message="Run a batch compute job"
    )

    print("\n[RESULT]")
    print(result['final_answer'])
    print(f"\nSteps executed: {len(result['steps'])}")
    print(f"Success: {result['success']}")

    # Check for policy blocks
    denied_steps = [s for s in result['steps'] if s['status'] == 'denied']
    if denied_steps:
        print(f"\nDenied steps: {len(denied_steps)}")
        for step in denied_steps:
            print(f"  - {step['description']}: {step['error']}")

    return not result['success']


def test_multi_step():
    """Test 4: Multi-step plan (buy service via merchant)"""
    print("\n" + "=" * 70)
    print("TEST 4: Multi-Step A2A Purchase")
    print("=" * 70)

    graph = get_agent_graph()

    result = graph.invoke(
        agent_id="user-agent",
        user_message="Buy a premium image from the merchant"
    )

    print("\n[RESULT]")
    print(result['final_answer'])
    print(f"\nSteps executed: {len(result['steps'])}")
    print(f"Success: {result['success']}")

    # Show step breakdown
    print("\n[STEP BREAKDOWN]")
    for i, step in enumerate(result['steps'], 1):
        print(f"{i}. {step['description']}")
        print(f"   Tool: {step['tool_name']}")
        print(f"   Status: {step['status']}")
        if step['amount_mnee']:
            print(f"   Cost: {step['amount_mnee']} MNEE")

    return result['success']


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("MNEE Nexus - LangGraph Architecture Test Suite")
    print("=" * 70)

    tests = [
        ("Simple Price Query", test_simple_query),
        ("Image Generation", test_image_generation),
        ("Budget Limit Check", test_budget_limit),
        ("Multi-Step Purchase", test_multi_step),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "PASS" if success else "FAIL"
        except Exception as e:
            print(f"\n[ERROR] {test_name} failed with exception: {e}")
            results[test_name] = "ERROR"
            import traceback
            traceback.print_exc()

        input("\nPress Enter to continue to next test...")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, result in results.items():
        symbol = "✓" if result == "PASS" else "✗"
        print(f"{symbol} {test_name}: {result}")

    passed = sum(1 for r in results.values() if r == "PASS")
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)

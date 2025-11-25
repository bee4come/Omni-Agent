#!/usr/bin/env python3
"""
Verify LangChain 1.0 compatibility.

This script checks that all LangChain/LangGraph imports work correctly
with the updated package versions.
"""

import sys


def test_langgraph_imports():
    """Test LangGraph core imports"""
    print("Testing LangGraph imports...")
    try:
        from langgraph.graph import StateGraph, END, START
        from langgraph.checkpoint.memory import InMemorySaver
        print("  ✓ StateGraph, END, START imported")
        print("  ✓ InMemorySaver imported")
        return True
    except ImportError as e:
        print(f"  ✗ LangGraph import failed: {e}")
        return False


def test_langchain_core_imports():
    """Test LangChain core imports"""
    print("\nTesting LangChain core imports...")
    try:
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        print("  ✓ Message types imported")
        return True
    except ImportError as e:
        print(f"  ✗ LangChain core import failed: {e}")
        return False


def test_provider_imports():
    """Test provider-specific imports"""
    print("\nTesting provider imports...")

    success = True

    # Test OpenAI (may not be installed)
    try:
        from langchain_openai import ChatOpenAI
        print("  ✓ ChatOpenAI imported")
    except ImportError as e:
        print(f"  ⚠ ChatOpenAI import failed (optional): {e}")

    # Test AWS (may not be installed)
    try:
        from langchain_aws import ChatBedrockConverse
        print("  ✓ ChatBedrockConverse imported")
    except ImportError as e:
        print(f"  ⚠ ChatBedrockConverse import failed (optional): {e}")

    return success


def test_pydantic():
    """Test Pydantic v2"""
    print("\nTesting Pydantic...")
    try:
        from pydantic import BaseModel, Field
        import pydantic

        version = pydantic.VERSION
        print(f"  ✓ Pydantic {version} imported")

        if version.startswith("2."):
            print("  ✓ Pydantic v2 confirmed")
            return True
        else:
            print(f"  ✗ Pydantic v1 detected ({version}), v2 required")
            return False

    except ImportError as e:
        print(f"  ✗ Pydantic import failed: {e}")
        return False


def test_simple_graph():
    """Test creating and running a simple graph"""
    print("\nTesting simple StateGraph creation...")
    try:
        from langgraph.graph import StateGraph, START, END
        from typing import TypedDict

        class TestState(TypedDict):
            value: str

        def test_node(state: TestState) -> TestState:
            return {"value": state["value"] + "_processed"}

        workflow = StateGraph(TestState)
        workflow.add_node("test", test_node)
        workflow.add_edge(START, "test")
        workflow.add_edge("test", END)

        graph = workflow.compile()

        result = graph.invoke({"value": "test"})

        if result["value"] == "test_processed":
            print("  ✓ Graph compiled and executed successfully")
            return True
        else:
            print(f"  ✗ Unexpected result: {result}")
            return False

    except Exception as e:
        print(f"  ✗ Graph test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_project_imports():
    """Test our project's specific imports"""
    print("\nTesting project-specific imports...")
    try:
        sys.path.insert(0, "/home/zty/Omni-Agent/backend")

        from agents.state import GraphState, StepRecord, PlanStep
        print("  ✓ Project state models imported")

        from agents.nodes.planner import planner_node
        from agents.nodes.guardian import guardian_node
        from agents.nodes.executor import executor_node
        from agents.nodes.feedback import policy_feedback_node
        from agents.nodes.summarizer import summarizer_node
        print("  ✓ All node modules imported")

        from agents.graph import build_omni_agent_graph, get_agent_graph
        print("  ✓ Graph builder imported")

        return True

    except ImportError as e:
        print(f"  ✗ Project import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("LangChain 1.0 Compatibility Verification")
    print("=" * 70)

    tests = [
        ("LangGraph Imports", test_langgraph_imports),
        ("LangChain Core Imports", test_langchain_core_imports),
        ("Provider Imports", test_provider_imports),
        ("Pydantic v2", test_pydantic),
        ("Simple Graph", test_simple_graph),
        ("Project Imports", test_project_imports),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = "PASS" if success else "FAIL"
        except Exception as e:
            print(f"\n  ✗ {test_name} crashed: {e}")
            results[test_name] = "ERROR"
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for test_name, result in results.items():
        symbol = "✓" if result == "PASS" else "✗"
        print(f"{symbol} {test_name}: {result}")

    passed = sum(1 for r in results.values() if r == "PASS")
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed! LangChain 1.0 compatibility confirmed.")
        return 0
    else:
        print("\n✗ Some tests failed. Check requirements.txt and reinstall packages.")
        print("\nTo fix:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())

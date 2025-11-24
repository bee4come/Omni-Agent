#!/usr/bin/env python3
"""
Swarm Architecture Test Script

This script demonstrates the complete Swarm workflow:
1. Manager creates execution plan
2. Customer executes purchases
3. Merchant delivers services
4. Treasurer records transactions
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.swarm import SwarmOrchestrator
from payment.client import PaymentClient
from policy.engine import PolicyEngine


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_swarm_basic():
    """Test basic Swarm functionality without actual payments"""
    print_section("Swarm Architecture Test - Basic Mode")

    # Initialize Swarm without payment client (mock mode)
    swarm = SwarmOrchestrator(payment_client=None, policy_engine=None)

    # Test various requests
    test_requests = [
        "Generate a cyberpunk avatar for my profile",
        "What is the current ETH price?",
        "Run a batch job to process 50 tasks",
        "Archive these logs for 30 days"
    ]

    for i, request in enumerate(test_requests, 1):
        print(f"\n\nTest {i}: {request}")
        print("-" * 70)

        result = swarm.process_request(request, requesting_agent_id="test-agent")

        print(f"\nResult:")
        print(f"  Success: {result['success']}")
        print(f"  Tasks: {result['execution_summary']['total_tasks']}")
        print(f"  Successful: {result['execution_summary']['successful_tasks']}")
        print(f"  Failed: {result['execution_summary']['failed_tasks']}")
        print(f"  Cost: {result['financial_summary']['total_spent']} MNEE")

        if result['task_results']:
            print(f"\n  Task Results:")
            for task_result in result['task_results']:
                print(f"    - {task_result['service_id']}: {task_result['success']}")
                if task_result['service_data']:
                    print(f"      Data: {task_result['service_data']}")

    # Print system statistics
    print_section("System Statistics")
    stats = swarm.get_system_stats()

    print("\nManager Stats:")
    for key, value in stats['manager'].items():
        print(f"  {key}: {value}")

    print("\nCustomer Stats:")
    for key, value in stats['customer'].items():
        print(f"  {key}: {value}")

    print("\nMerchant Stats:")
    for key, value in stats['merchant'].items():
        print(f"  {key}: {value}")

    print("\nTreasurer Stats:")
    for key, value in stats['treasurer'].items():
        print(f"  {key}: {value}")

    # Check for anomalies
    print_section("Anomaly Detection")
    anomaly_report = swarm.detect_anomalies()
    print(f"\nAnomalies Detected: {anomaly_report['anomalies_detected']}")
    if anomaly_report['anomalies']:
        for anomaly in anomaly_report['anomalies']:
            print(f"  - {anomaly['type']}: {anomaly['severity']}")


def test_swarm_with_policy():
    """Test Swarm with Policy Engine (no actual payments)"""
    print_section("Swarm Architecture Test - With Policy Engine")

    # Initialize Policy Engine
    try:
        policy_engine = PolicyEngine(
            "../config/agents.yaml",
            "../config/services.yaml"
        )
        print("[OK] Policy Engine loaded")
    except Exception as e:
        print(f"[WARN] Could not load Policy Engine: {e}")
        print("[INFO] Running without policy checks")
        policy_engine = None

    # Initialize Swarm
    swarm = SwarmOrchestrator(
        payment_client=None,  # No actual payments in test mode
        policy_engine=policy_engine
    )

    # Test request that might trigger policy
    request = "Generate 5 images and run 10 batch jobs"
    print(f"\nTest Request: {request}")
    print("-" * 70)

    result = swarm.process_request(request, requesting_agent_id="test-agent")

    print(f"\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  Tasks: {result['execution_summary']['total_tasks']}")
    print(f"  Cost: {result['financial_summary']['total_spent']} MNEE")


def test_individual_agents():
    """Test each agent individually"""
    print_section("Individual Agent Tests")

    # Test Manager
    print("\n1. Testing Manager Agent...")
    from agents.swarm import ManagerAgent
    manager = ManagerAgent()
    plan = manager.plan("Generate image and check price")
    print(f"   Plan created: {len(plan.tasks)} tasks, {plan.total_estimated_cost} MNEE")

    # Test Merchant
    print("\n2. Testing Merchant Agent...")
    from agents.swarm import MerchantAgent
    merchant = MerchantAgent(merchant_id="test-merchant")
    quote = merchant.quote("IMAGE_GEN_PREMIUM", {"prompt": "test"})
    print(f"   Quote issued: {quote['unit_price_mnee']} MNEE, ID: {quote['quote_id']}")

    # Test Treasurer
    print("\n3. Testing Treasurer Agent...")
    from agents.swarm import TreasurerAgent
    treasurer = TreasurerAgent()
    receipt = {
        "agent_id": "test-agent",
        "service_id": "IMAGE_GEN_PREMIUM",
        "task_id": "task-test",
        "payment_id": "pay-test",
        "amount": 1.0,
        "status": "success",
        "service_call_hash": "0xtest",
        "policy_action": "ALLOW",
        "risk_level": "RISK_OK"
    }
    record = treasurer.record_transaction(receipt)
    print(f"   Transaction recorded: {record.record_id}")

    # Test Customer (without payment client)
    print("\n4. Testing Customer Agent...")
    from agents.swarm import CustomerAgent
    customer = CustomerAgent(agent_id="test-customer")
    stats = customer.get_purchase_stats()
    print(f"   Customer initialized: {stats['total_purchases']} purchases")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  MNEE Nexus - Swarm Architecture Test Suite")
    print("=" * 70)

    try:
        # Run tests
        test_individual_agents()
        test_swarm_basic()
        test_swarm_with_policy()

        print_section("All Tests Complete")
        print("\n[SUCCESS] Swarm architecture is operational!")
        print("\nNext steps:")
        print("  1. Start Guardian Service: cd guardian && ./start_guardian.sh")
        print("  2. Configure Payment Client with Guardian URL")
        print("  3. Run integration tests with actual payments")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Example 1: Simple Usage

Demonstrates the easiest way to use MNEE services.
"""

import sys
import os

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sdk import MNEEAgent


def main():
    print("=" * 70)
    print("  MNEE Nexus SDK - Example 1: Simple Usage")
    print("=" * 70)

    # Initialize agent
    print("\n1. Initializing agent...")
    agent = MNEEAgent(agent_id="example-agent")

    # Check budget before starting
    print("\n2. Checking budget...")
    budget = agent.get_budget_status()
    print(f"   Daily budget: {budget['daily_budget']} MNEE")
    print(f"   Current spending: {budget['current_spending']} MNEE")
    print(f"   Remaining: {budget['remaining_budget']} MNEE")

    # List available services
    print("\n3. Available services:")
    services = agent.list_available_services()
    for service in services:
        status = "Active" if service['active'] else "Inactive"
        print(f"   - {service['id']}: {service['unit_price']} MNEE ({status})")

    # Request a service
    print("\n4. Requesting service...")
    result = agent.request_service("Generate a cyberpunk avatar for my profile")

    # Check result
    if result["success"]:
        print(f"\n   Success! Cost: {result['total_cost']} MNEE")
        print(f"   Plan ID: {result['plan_id']}")

        print("\n   Results:")
        for i, data in enumerate(result["service_data"], 1):
            print(f"   {i}. {data}")

        # Check updated budget
        updated_budget = agent.get_budget_status()
        print(f"\n   Updated budget: {updated_budget['remaining_budget']} MNEE")
    else:
        print(f"\n   Failed: {result.get('error', 'Unknown error')}")

    # Get transaction history
    print("\n5. Transaction history:")
    history = agent.get_transaction_history()
    print(f"   Total transactions: {len(history)}")
    if history:
        latest = history[-1]
        print(f"   Latest: {latest['service_id']} - {latest['amount']} MNEE")

    print("\n" + "=" * 70)
    print("  Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

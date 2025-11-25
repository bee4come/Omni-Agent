#!/usr/bin/env python3
"""
Example 4: Budget Monitoring

Demonstrates budget monitoring and cost management patterns.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sdk import MNEEAgent, PaymentSDK


def check_budget_status(agent):
    """Helper function to display budget status"""
    budget = agent.get_budget_status()
    remaining_pct = (budget['remaining_budget'] / budget['daily_budget'] * 100)

    print(f"\n   Budget Status:")
    print(f"   - Daily budget: {budget['daily_budget']} MNEE")
    print(f"   - Current spending: {budget['current_spending']} MNEE")
    print(f"   - Remaining: {budget['remaining_budget']} MNEE ({remaining_pct:.1f}%)")

    # Budget warning levels
    if remaining_pct < 10:
        print("   - WARNING: Critical budget level (< 10%)")
    elif remaining_pct < 25:
        print("   - ALERT: Low budget (< 25%)")
    elif remaining_pct < 50:
        print("   - INFO: Half budget consumed")
    else:
        print("   - OK: Sufficient budget remaining")

    return budget


def main():
    print("=" * 70)
    print("  MNEE Nexus SDK - Example 4: Budget Monitoring")
    print("=" * 70)

    # Initialize agent
    print("\n1. Initializing agent...")
    agent = MNEEAgent(agent_id="monitored-agent")

    # Check initial budget
    print("\n2. Initial budget check:")
    initial_budget = check_budget_status(agent)

    # Example 1: Pre-flight budget check
    print("\n3. Pre-flight budget check before expensive operation...")

    # Use PaymentSDK for fine-grained control
    payment_sdk = PaymentSDK(agent_id="monitored-agent")

    # Check price first
    service_id = "BATCH_COMPUTE"
    price = payment_sdk.get_service_price(service_id)
    print(f"   Service: {service_id}")
    print(f"   Price: {price} MNEE per unit")

    # Calculate if we can afford it
    quantity = 5
    estimated_cost = price * quantity
    print(f"   Quantity: {quantity} units")
    print(f"   Estimated cost: {estimated_cost} MNEE")

    budget = payment_sdk.get_agent_budget()
    if budget['remaining'] < estimated_cost:
        print(f"\n   BLOCKED: Insufficient budget!")
        print(f"   Need: {estimated_cost} MNEE")
        print(f"   Have: {budget['remaining']} MNEE")
        print(f"   Shortfall: {estimated_cost - budget['remaining']} MNEE")
        return
    else:
        print(f"\n   APPROVED: Sufficient budget available")

    # Example 2: Execute with budget monitoring
    print("\n4. Executing request with budget monitoring...")

    result = agent.request_service("Generate a cyberpunk avatar")

    if result["success"]:
        print(f"   Operation successful!")
        print(f"   Cost: {result['total_cost']} MNEE")

        # Check updated budget
        print("\n5. Post-operation budget check:")
        updated_budget = check_budget_status(agent)

        # Calculate spending
        spent = initial_budget['remaining_budget'] - updated_budget['remaining_budget']
        print(f"\n   Operation cost: {spent} MNEE")
    else:
        print(f"   Operation failed: {result.get('error', 'Unknown error')}")

    # Example 3: Budget-aware batch processing
    print("\n6. Budget-aware batch processing...")

    # Get current budget
    current_budget = agent.get_budget_status()
    remaining = current_budget['remaining_budget']

    # Calculate how many IMAGE_GEN_PREMIUM calls we can afford
    image_price = payment_sdk.get_service_price("IMAGE_GEN_PREMIUM")
    max_calls = int(remaining / image_price)

    print(f"   Remaining budget: {remaining} MNEE")
    print(f"   Service price: {image_price} MNEE")
    print(f"   Maximum affordable calls: {max_calls}")

    # Only proceed if we can afford at least 1 call
    if max_calls > 0:
        safe_quantity = min(max_calls, 3)  # Cap at 3 for demo
        print(f"   Executing {safe_quantity} calls...")

        for i in range(safe_quantity):
            print(f"\n   Call {i+1}/{safe_quantity}:")
            result = agent.request_service(f"Generate avatar variant {i+1}")

            if result["success"]:
                print(f"     Success! Cost: {result['total_cost']} MNEE")
                # Check budget after each call
                budget = check_budget_status(agent)
            else:
                print(f"     Failed: {result.get('error', 'Unknown error')}")
                break
    else:
        print("   Insufficient budget for any calls!")

    # Example 4: Transaction history analysis
    print("\n7. Transaction history analysis:")
    history = agent.get_transaction_history()

    if history:
        print(f"   Total transactions: {len(history)}")

        # Aggregate by service
        service_spending = {}
        for tx in history:
            service_id = tx['service_id']
            amount = tx['amount']
            if service_id not in service_spending:
                service_spending[service_id] = 0
            service_spending[service_id] += amount

        print("\n   Spending breakdown:")
        for service_id, amount in sorted(service_spending.items(), key=lambda x: x[1], reverse=True):
            print(f"   - {service_id}: {amount} MNEE")

        # Latest transaction
        latest = history[-1]
        print(f"\n   Latest transaction:")
        print(f"   - Service: {latest['service_id']}")
        print(f"   - Amount: {latest['amount']} MNEE")
        print(f"   - Status: {latest['status']}")
    else:
        print("   No transactions yet")

    # Final budget report
    print("\n8. Final budget report:")
    final_budget = check_budget_status(agent)

    total_spent = initial_budget['current_spending'] - final_budget['remaining_budget']
    print(f"\n   Session summary:")
    print(f"   - Total spent this session: {abs(total_spent)} MNEE")
    print(f"   - Daily spending: {final_budget['current_spending']} MNEE")
    print(f"   - Budget utilization: {(final_budget['current_spending'] / final_budget['daily_budget'] * 100):.1f}%")

    print("\n" + "=" * 70)
    print("  Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

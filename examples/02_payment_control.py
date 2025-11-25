#!/usr/bin/env python3
"""
Example 2: Payment Control

Demonstrates fine-grained payment control using PaymentSDK.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sdk import PaymentSDK


def main():
    print("=" * 70)
    print("  MNEE Nexus SDK - Example 2: Payment Control")
    print("=" * 70)

    # Initialize SDK
    print("\n1. Initializing Payment SDK...")
    sdk = PaymentSDK(agent_id="payment-example")

    # Check agent budget
    print("\n2. Agent budget:")
    budget = sdk.get_agent_budget()
    print(f"   Daily budget: {budget['daily_budget']} MNEE")
    print(f"   Max per call: {budget['max_per_call']} MNEE")
    print(f"   Current spending: {budget['current_spending']} MNEE")
    print(f"   Remaining: {budget['remaining']} MNEE")
    print(f"   Priority: {budget['priority']}")

    # Get service price
    service_id = "IMAGE_GEN_PREMIUM"
    print(f"\n3. Checking {service_id} price...")
    price = sdk.get_service_price(service_id)
    print(f"   Unit price: {price} MNEE")

    # Check policy before paying
    print("\n4. Checking policy...")
    decision = sdk.check_policy(service_id, estimated_cost=price)
    print(f"   Action: {decision['action']}")
    print(f"   Risk level: {decision['risk_level']}")
    print(f"   Reason: {decision['reason']}")

    if decision["action"] != "ALLOW":
        print(f"\n   Payment would be {decision['action']}. Exiting.")
        return

    # Execute payment
    print("\n5. Executing payment...")
    result = sdk.pay_for_service(
        service_id=service_id,
        quantity=1,
        payload={
            "prompt": "A futuristic city with flying cars",
            "style": "cyberpunk",
            "resolution": "1024x1024"
        }
    )

    # Check result
    if result.success:
        print(f"\n   Payment successful!")
        print(f"   Payment ID: {result.payment_id}")
        print(f"   Transaction hash: {result.tx_hash}")
        print(f"   Service call hash: {result.service_call_hash}")
        print(f"   Amount: {result.amount} MNEE")
        print(f"   Risk level: {result.risk_level}")
        print(f"   Policy action: {result.policy_action}")
    else:
        print(f"\n   Payment failed!")
        print(f"   Error: {result.error}")
        print(f"   Risk level: {result.risk_level}")

    # Check updated budget
    print("\n6. Updated budget:")
    updated_budget = sdk.get_agent_budget()
    print(f"   Current spending: {updated_budget['current_spending']} MNEE")
    print(f"   Remaining: {updated_budget['remaining']} MNEE")

    # Check treasury balance
    print("\n7. Treasury balance:")
    treasury_balance = sdk.get_treasury_balance()
    print(f"   Balance: {treasury_balance} MNEE")

    print("\n" + "=" * 70)
    print("  Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

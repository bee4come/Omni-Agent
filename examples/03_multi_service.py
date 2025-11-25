#!/usr/bin/env python3
"""
Example 3: Multi-Service Workflow

Demonstrates complex workflows using multiple services.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sdk import SwarmSDK


def main():
    print("=" * 70)
    print("  MNEE Nexus SDK - Example 3: Multi-Service Workflow")
    print("=" * 70)

    # Initialize Swarm SDK
    print("\n1. Initializing Swarm SDK...")
    swarm = SwarmSDK()

    # Example 1: Simple multi-service request
    print("\n2. Executing multi-service workflow...")
    print("   Request: Generate an image and check ETH price")

    result = swarm.execute(
        user_request="Generate a cyberpunk avatar and check ETH price",
        agent_id="multi-service-agent"
    )

    print(f"\n   Execution result:")
    print(f"   Plan ID: {result['plan_id']}")
    print(f"   Tasks: {result['successful_tasks']}/{result['total_tasks']} successful")
    print(f"   Total cost: {result['total_cost']} MNEE")

    # Display individual task results
    print("\n   Task details:")
    for i, task in enumerate(result["tasks"], 1):
        status = "SUCCESS" if task["success"] else "FAILED"
        print(f"   {i}. {task['service_id']} - {status}")
        if task["success"]:
            print(f"      Payment ID: {task['payment_id']}")
            print(f"      Data: {task['data']}")
        else:
            print(f"      Error: {task['error']}")

    # Example 2: Complex batch workflow
    print("\n3. Executing complex batch workflow...")
    print("   Request: Generate 3 images and archive logs")

    complex_result = swarm.execute(
        user_request="Generate 3 different avatar images and archive all logs",
        agent_id="batch-agent"
    )

    print(f"\n   Batch execution result:")
    print(f"   Plan ID: {complex_result['plan_id']}")
    print(f"   Tasks completed: {complex_result['successful_tasks']}/{complex_result['total_tasks']}")
    print(f"   Total cost: {complex_result['total_cost']} MNEE")

    # Get system statistics
    print("\n4. System statistics:")
    stats = swarm.get_statistics()

    print(f"\n   Manager Agent:")
    print(f"   - Total plans created: {stats['manager']['total_plans']}")
    print(f"   - Unique agents: {stats['manager']['unique_agents']}")

    print(f"\n   Customer Agent:")
    print(f"   - Total purchases: {stats['customer']['total_purchases']}")
    print(f"   - Successful: {stats['customer']['successful_purchases']}")
    print(f"   - Failed: {stats['customer']['failed_purchases']}")
    print(f"   - Total spent: {stats['customer']['total_spent']} MNEE")

    print(f"\n   Merchant Agent:")
    print(f"   - Services delivered: {stats['merchant']['services_delivered']}")
    print(f"   - Total revenue: {stats['merchant']['total_revenue']} MNEE")

    print(f"\n   Treasurer Agent:")
    print(f"   - Total transactions: {stats['treasurer']['total_transactions']}")
    print(f"   - Total volume: {stats['treasurer']['total_volume']} MNEE")
    print(f"   - Success rate: {stats['treasurer']['success_rate']:.1f}%")

    # Get daily summary
    print("\n5. Daily summary:")
    summary = swarm.get_daily_summary()
    print(f"   Transactions: {summary['total_transactions']}")
    print(f"   Volume: {summary['total_volume']} MNEE")
    print(f"   Success rate: {summary['success_rate']:.1f}%")
    print(f"   Unique agents: {summary['unique_agents']}")
    print(f"   Unique services: {summary['unique_services']}")

    # Detect anomalies
    print("\n6. Anomaly detection:")
    anomalies = swarm.detect_anomalies()
    if anomalies["anomalies_detected"] > 0:
        print(f"   WARNING: {anomalies['anomalies_detected']} anomalies detected!")
        for anomaly in anomalies["anomalies"]:
            print(f"   - {anomaly['type']}: {anomaly['severity']}")
            print(f"     Reason: {anomaly['reason']}")
    else:
        print("   No anomalies detected. System operating normally.")

    print("\n" + "=" * 70)
    print("  Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

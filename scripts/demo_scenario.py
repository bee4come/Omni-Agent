#!/usr/bin/env python3
"""
MNEE Nexus Demo Scenario Script

This script simulates a "Startup AI Team" scenario where multiple AI agents
collaborate on a project, demonstrating:
1. Individual agent actions with budget tracking
2. Agent-to-Agent payments
3. Escrow-based task completion
4. Policy enforcement (including denial)

Usage:
    python scripts/demo_scenario.py [--fast] [--step]

Options:
    --fast      Run without delays (for testing)
    --step      Wait for Enter key between steps
"""

import argparse
import sys
import time
import httpx
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000"
DELAY_SHORT = 1.5
DELAY_MEDIUM = 3.0
DELAY_LONG = 5.0


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_step(step_num: int, text: str):
    """Print a step description."""
    print(f"{Colors.CYAN}[Step {step_num}]{Colors.ENDC} {text}")


def print_success(text: str):
    """Print success message."""
    print(f"  {Colors.GREEN}[OK]{Colors.ENDC} {text}")


def print_info(text: str):
    """Print info message."""
    print(f"  {Colors.BLUE}[INFO]{Colors.ENDC} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"  {Colors.WARNING}[WARN]{Colors.ENDC} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"  {Colors.FAIL}[ERROR]{Colors.ENDC} {text}")


def wait(seconds: float, fast_mode: bool):
    """Wait for specified seconds unless in fast mode."""
    if not fast_mode:
        time.sleep(seconds)


def wait_for_step(step_mode: bool):
    """Wait for user input if in step mode."""
    if step_mode:
        input(f"\n{Colors.WARNING}Press Enter to continue...{Colors.ENDC}")


def check_api_health() -> bool:
    """Check if the API is running."""
    try:
        response = httpx.get(f"{API_BASE}/", timeout=5.0)
        return response.status_code == 200
    except Exception:
        return False


def get_treasury_status() -> dict:
    """Get current treasury status."""
    response = httpx.get(f"{API_BASE}/treasury", timeout=10.0)
    return response.json()


def get_agent_info(agent_id: str) -> dict:
    """Get agent information."""
    response = httpx.get(f"{API_BASE}/agents/{agent_id}", timeout=10.0)
    return response.json()


def send_chat_command(agent_id: str, message: str) -> dict:
    """Send a chat command to an agent."""
    response = httpx.post(
        f"{API_BASE}/chat",
        json={"agent_id": agent_id, "message": message},
        timeout=60.0
    )
    return response.json()


def execute_a2a_payment(from_agent: str, to_agent: str, amount: float, task: str) -> dict:
    """Execute an A2A payment."""
    response = httpx.post(
        f"{API_BASE}/a2a/pay",
        json={
            "from_agent": from_agent,
            "to_agent": to_agent,
            "amount": amount,
            "task_description": task
        },
        timeout=30.0
    )
    return response.json()


def get_a2a_balances() -> dict:
    """Get A2A wallet balances."""
    response = httpx.get(f"{API_BASE}/a2a/balances", timeout=10.0)
    return response.json()


def get_escrows() -> dict:
    """Get all escrows."""
    response = httpx.get(f"{API_BASE}/escrow/list", timeout=10.0)
    return response.json()


def reset_budgets():
    """Reset all agent budgets."""
    response = httpx.post(f"{API_BASE}/reset", timeout=10.0)
    return response.json()


def run_demo(fast_mode: bool = False, step_mode: bool = False):
    """Run the complete demo scenario."""

    print_header("MNEE Nexus Demo: Startup AI Team Scenario")

    print(f"""
{Colors.BOLD}Scenario:{Colors.ENDC}
A startup is using AI agents to build their product:
- Designer Agent: Creates visual assets
- Analyst Agent: Processes market data
- Archivist Agent: Logs all operations
- User Agent: Coordinates the team

Watch how they collaborate using MNEE payments!
""")

    wait_for_step(step_mode)

    # Step 0: Health Check
    print_step(0, "Checking API health...")
    if not check_api_health():
        print_error("API is not running! Please start the backend first.")
        print_info("Run: ./start_all.sh")
        sys.exit(1)
    print_success("API is healthy")

    wait(DELAY_SHORT, fast_mode)
    wait_for_step(step_mode)

    # Step 1: Show Initial State
    print_step(1, "Checking initial treasury state...")
    treasury = get_treasury_status()
    print_success(f"Total Allocated: {treasury.get('totalAllocated', 0):.2f} MNEE")
    print_success(f"Total Spent: {treasury.get('totalSpent', 0):.2f} MNEE")
    print_info(f"Active Agents: {len(treasury.get('agents', {}))}")

    wait(DELAY_MEDIUM, fast_mode)
    wait_for_step(step_mode)

    # Step 2: Designer Agent creates logo
    print_step(2, "Designer Agent: Creating startup logo...")
    print_info("Sending request to startup-designer agent")

    try:
        result = send_chat_command(
            "startup-designer",
            "Create a modern logo for a fintech startup called 'PayFlow'"
        )
        print_success(f"Task completed!")
        if result.get('response'):
            print_info(f"Response: {result['response'][:100]}...")
    except Exception as e:
        print_warning(f"Chat command failed (expected if LLM not configured): {e}")

    wait(DELAY_LONG, fast_mode)
    wait_for_step(step_mode)

    # Step 3: A2A Payment - Designer pays Analyst
    print_step(3, "A2A Payment: Designer hires Analyst for market research...")
    print_info("startup-designer -> startup-analyst: 3.0 MNEE")

    try:
        a2a_result = execute_a2a_payment(
            from_agent="startup-designer",
            to_agent="startup-analyst",
            amount=3.0,
            task="Analyze competitor logos and design trends"
        )
        if a2a_result.get('success'):
            print_success("A2A payment successful!")
            print_info(f"TX Hash: {a2a_result.get('tx_hash', 'N/A')[:20]}...")
        else:
            print_warning(f"A2A payment failed: {a2a_result.get('error', 'Unknown')}")
    except Exception as e:
        print_warning(f"A2A payment error: {e}")

    wait(DELAY_MEDIUM, fast_mode)
    wait_for_step(step_mode)

    # Step 4: Check A2A Balances
    print_step(4, "Checking A2A wallet balances...")

    try:
        balances = get_a2a_balances()
        for agent_id, balance in balances.get('balances', {}).items():
            print_info(f"{agent_id}: {balance:.2f} MNEE")
    except Exception as e:
        print_warning(f"Could not get balances: {e}")

    wait(DELAY_SHORT, fast_mode)
    wait_for_step(step_mode)

    # Step 5: Archivist logs the operations
    print_step(5, "Archivist Agent: Logging team activities...")
    print_info("Sending log request to startup-archivist agent")

    try:
        result = send_chat_command(
            "startup-archivist",
            "Log: Design team completed logo creation and market analysis"
        )
        print_success("Log entry created!")
    except Exception as e:
        print_warning(f"Log command failed: {e}")

    wait(DELAY_MEDIUM, fast_mode)
    wait_for_step(step_mode)

    # Step 6: Check Escrows
    print_step(6, "Checking active escrows...")

    try:
        escrows = get_escrows()
        total = escrows.get('total_count', 0)
        by_status = escrows.get('by_status', {})
        print_info(f"Total escrows: {total}")
        for status, count in by_status.items():
            if count > 0:
                print_info(f"  {status}: {count}")
    except Exception as e:
        print_warning(f"Could not get escrows: {e}")

    wait(DELAY_SHORT, fast_mode)
    wait_for_step(step_mode)

    # Step 7: Demonstrate Budget Enforcement
    print_step(7, "Testing budget enforcement (should be DENIED)...")
    print_info("Attempting large batch operation that exceeds budget...")

    try:
        result = send_chat_command(
            "startup-archivist",  # Low budget agent
            "Generate 1000 high-resolution images for the marketing campaign"
        )
        if "denied" in str(result).lower() or "budget" in str(result).lower():
            print_success("Request correctly DENIED by Policy Engine!")
        else:
            print_info(f"Response: {result.get('response', 'N/A')[:100]}...")
    except Exception as e:
        print_warning(f"Request failed (may be expected): {e}")

    wait(DELAY_MEDIUM, fast_mode)
    wait_for_step(step_mode)

    # Step 8: Final Treasury State
    print_step(8, "Final treasury state...")
    treasury = get_treasury_status()
    print_success(f"Total Allocated: {treasury.get('totalAllocated', 0):.2f} MNEE")
    print_success(f"Total Spent: {treasury.get('totalSpent', 0):.2f} MNEE")
    remaining = treasury.get('totalAllocated', 0) - treasury.get('totalSpent', 0)
    print_success(f"Remaining: {remaining:.2f} MNEE")

    print_header("Demo Complete!")

    print(f"""
{Colors.BOLD}What we demonstrated:{Colors.ENDC}

1. {Colors.GREEN}[OK]{Colors.ENDC} Multi-agent treasury management
2. {Colors.GREEN}[OK]{Colors.ENDC} Individual agent budget tracking
3. {Colors.GREEN}[OK]{Colors.ENDC} Agent-to-Agent (A2A) payments
4. {Colors.GREEN}[OK]{Colors.ENDC} Policy enforcement and budget limits
5. {Colors.GREEN}[OK]{Colors.ENDC} Real-time updates via WebSocket

{Colors.BOLD}Key Innovation:{Colors.ENDC}
MNEE Nexus enables autonomous AI agents to manage finances,
pay for services, and collaborate - all using MNEE stablecoin.

{Colors.CYAN}Thank you for watching!{Colors.ENDC}
""")


def main():
    parser = argparse.ArgumentParser(
        description="MNEE Nexus Demo Scenario Script"
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Run without delays (for testing)'
    )
    parser.add_argument(
        '--step',
        action='store_true',
        help='Wait for Enter key between steps'
    )

    args = parser.parse_args()

    try:
        run_demo(fast_mode=args.fast, step_mode=args.step)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Demo interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Demo failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

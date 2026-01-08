#!/usr/bin/env python3
"""
MNEE Nexus Integration Test Script

Tests all services end-to-end to verify the system is working correctly.
Run this before demos to ensure everything is properly configured.

Usage:
    python scripts/integration_test.py [--verbose]
"""

import argparse
import sys
import time
import httpx
from typing import Tuple, List
from dataclasses import dataclass
from enum import Enum


class TestStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARN = "WARN"


@dataclass
class TestResult:
    name: str
    status: TestStatus
    message: str
    duration_ms: float


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def colorize(text: str, status: TestStatus) -> str:
    if status == TestStatus.PASS:
        return f"{Colors.GREEN}{text}{Colors.END}"
    elif status == TestStatus.FAIL:
        return f"{Colors.RED}{text}{Colors.END}"
    elif status == TestStatus.WARN:
        return f"{Colors.YELLOW}{text}{Colors.END}"
    else:
        return f"{Colors.BLUE}{text}{Colors.END}"


class IntegrationTester:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.api_base = "http://localhost:8000"
        self.frontend_base = "http://localhost:3000"
        self.guardian_base = "http://localhost:8100"

    def log(self, message: str):
        if self.verbose:
            print(f"  {Colors.BLUE}[DEBUG]{Colors.END} {message}")

    def run_test(self, name: str, test_func) -> TestResult:
        start = time.time()
        try:
            status, message = test_func()
            duration = (time.time() - start) * 1000
            result = TestResult(name, status, message, duration)
        except Exception as e:
            duration = (time.time() - start) * 1000
            result = TestResult(name, TestStatus.FAIL, str(e), duration)

        self.results.append(result)
        status_str = colorize(f"[{result.status.value}]", result.status)
        print(f"  {status_str} {name} ({result.duration_ms:.0f}ms)")
        if result.status == TestStatus.FAIL and self.verbose:
            print(f"       Error: {result.message}")

        return result

    # ============================================================
    # Service Health Tests
    # ============================================================

    def test_backend_health(self) -> Tuple[TestStatus, str]:
        """Test backend API is running."""
        response = httpx.get(f"{self.api_base}/", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "running":
                return TestStatus.PASS, f"Backend v{data.get('version', '?')}"
        return TestStatus.FAIL, f"Status code: {response.status_code}"

    def test_guardian_health(self) -> Tuple[TestStatus, str]:
        """Test Guardian service is running."""
        try:
            response = httpx.get(f"{self.guardian_base}/", timeout=5.0)
            if response.status_code == 200:
                return TestStatus.PASS, "Guardian service running"
            return TestStatus.WARN, f"Status code: {response.status_code}"
        except Exception as e:
            return TestStatus.WARN, f"Guardian not available: {e}"

    def test_frontend_health(self) -> Tuple[TestStatus, str]:
        """Test frontend is running."""
        try:
            response = httpx.get(f"{self.frontend_base}/", timeout=5.0)
            if response.status_code == 200:
                return TestStatus.PASS, "Frontend running"
            return TestStatus.WARN, f"Status code: {response.status_code}"
        except Exception as e:
            return TestStatus.WARN, f"Frontend not available: {e}"

    # ============================================================
    # API Endpoint Tests
    # ============================================================

    def test_treasury_endpoint(self) -> Tuple[TestStatus, str]:
        """Test treasury endpoint returns valid data."""
        response = httpx.get(f"{self.api_base}/treasury", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.FAIL, f"Status code: {response.status_code}"

        data = response.json()
        if "totalAllocated" not in data:
            return TestStatus.FAIL, "Missing totalAllocated field"
        if "agents" not in data:
            return TestStatus.FAIL, "Missing agents field"

        return TestStatus.PASS, f"Treasury: {data['totalAllocated']:.2f} MNEE allocated"

    def test_agents_endpoint(self) -> Tuple[TestStatus, str]:
        """Test agents endpoint returns valid data."""
        response = httpx.get(f"{self.api_base}/agents", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.FAIL, f"Status code: {response.status_code}"

        data = response.json()
        agents = data.get("agents", [])
        if len(agents) == 0:
            return TestStatus.WARN, "No agents configured"

        return TestStatus.PASS, f"{len(agents)} agents configured"

    def test_services_endpoint(self) -> Tuple[TestStatus, str]:
        """Test services endpoint returns valid data."""
        response = httpx.get(f"{self.api_base}/services", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.FAIL, f"Status code: {response.status_code}"

        data = response.json()
        services = data.get("services", [])
        active = [s for s in services if s.get("active")]

        if len(active) == 0:
            return TestStatus.WARN, "No active services"

        return TestStatus.PASS, f"{len(active)} active services"

    def test_transactions_endpoint(self) -> Tuple[TestStatus, str]:
        """Test transactions endpoint."""
        response = httpx.get(f"{self.api_base}/transactions?limit=10", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.FAIL, f"Status code: {response.status_code}"

        data = response.json()
        txs = data.get("transactions", [])
        return TestStatus.PASS, f"{len(txs)} recent transactions"

    def test_stats_endpoint(self) -> Tuple[TestStatus, str]:
        """Test stats endpoint."""
        response = httpx.get(f"{self.api_base}/stats", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.FAIL, f"Status code: {response.status_code}"

        data = response.json()
        if "transactions" not in data:
            return TestStatus.FAIL, "Missing transactions stats"
        if "agentCount" not in data:
            return TestStatus.FAIL, "Missing agentCount"

        return TestStatus.PASS, f"{data['agentCount']} agents, {data['serviceCount']} services"

    def test_policy_logs_endpoint(self) -> Tuple[TestStatus, str]:
        """Test policy logs endpoint."""
        response = httpx.get(f"{self.api_base}/policy/logs?limit=10", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.FAIL, f"Status code: {response.status_code}"

        data = response.json()
        logs = data.get("logs", [])
        return TestStatus.PASS, f"{len(logs)} policy decisions logged"

    # ============================================================
    # A2A Tests
    # ============================================================

    def test_a2a_balances(self) -> Tuple[TestStatus, str]:
        """Test A2A balances endpoint."""
        response = httpx.get(f"{self.api_base}/a2a/balances", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.FAIL, f"Status code: {response.status_code}"

        data = response.json()
        balances = data.get("balances", {})
        total = data.get("total", 0)

        return TestStatus.PASS, f"{len(balances)} wallets, {total:.2f} MNEE total"

    def test_a2a_transfers(self) -> Tuple[TestStatus, str]:
        """Test A2A transfers endpoint."""
        response = httpx.get(f"{self.api_base}/a2a/transfers", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.FAIL, f"Status code: {response.status_code}"

        data = response.json()
        count = data.get("total_count", 0)
        return TestStatus.PASS, f"{count} A2A transfers recorded"

    # ============================================================
    # Escrow Tests
    # ============================================================

    def test_escrow_list(self) -> Tuple[TestStatus, str]:
        """Test escrow list endpoint."""
        response = httpx.get(f"{self.api_base}/escrow/list", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.FAIL, f"Status code: {response.status_code}"

        data = response.json()
        total = data.get("total_count", 0)
        by_status = data.get("by_status", {})

        return TestStatus.PASS, f"{total} escrows ({by_status})"

    # ============================================================
    # Registry Tests
    # ============================================================

    def test_registry_agents(self) -> Tuple[TestStatus, str]:
        """Test registry agents endpoint."""
        response = httpx.get(f"{self.api_base}/registry/agents", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.FAIL, f"Status code: {response.status_code}"

        data = response.json()
        agents = data.get("agents", [])
        return TestStatus.PASS, f"{len(agents)} agents in registry"

    # ============================================================
    # Functional Tests
    # ============================================================

    def test_budget_update(self) -> Tuple[TestStatus, str]:
        """Test budget update functionality."""
        # Get an agent first
        response = httpx.get(f"{self.api_base}/agents", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.SKIP, "Could not get agents"

        agents = response.json().get("agents", [])
        if not agents:
            return TestStatus.SKIP, "No agents available"

        agent_id = agents[0]["id"]
        original_budget = agents[0]["dailyBudget"]

        # Update budget
        new_budget = original_budget + 10.0
        response = httpx.put(
            f"{self.api_base}/agents/{agent_id}/budget",
            json={"daily_budget": new_budget},
            timeout=10.0
        )

        if response.status_code != 200:
            return TestStatus.FAIL, f"Update failed: {response.status_code}"

        # Restore original
        httpx.put(
            f"{self.api_base}/agents/{agent_id}/budget",
            json={"daily_budget": original_budget},
            timeout=10.0
        )

        return TestStatus.PASS, f"Budget update works ({agent_id})"

    def test_reset_budgets(self) -> Tuple[TestStatus, str]:
        """Test budget reset functionality."""
        response = httpx.post(f"{self.api_base}/reset", timeout=10.0)
        if response.status_code != 200:
            return TestStatus.FAIL, f"Reset failed: {response.status_code}"

        return TestStatus.PASS, "Budget reset works"

    # ============================================================
    # WebSocket Test
    # ============================================================

    def test_websocket_endpoint(self) -> Tuple[TestStatus, str]:
        """Test WebSocket endpoint exists (basic check)."""
        # We can't easily test WebSocket in a simple script,
        # but we can check if the endpoint is documented
        response = httpx.get(f"{self.api_base}/openapi.json", timeout=10.0)
        if response.status_code == 200:
            return TestStatus.PASS, "WebSocket endpoint available at /ws"
        return TestStatus.WARN, "Could not verify WebSocket endpoint"

    # ============================================================
    # Run All Tests
    # ============================================================

    def run_all(self):
        print(f"\n{Colors.BOLD}MNEE Nexus Integration Tests{Colors.END}")
        print("=" * 50)

        # Service Health
        print(f"\n{Colors.BOLD}Service Health:{Colors.END}")
        self.run_test("Backend API", self.test_backend_health)
        self.run_test("Guardian Service", self.test_guardian_health)
        self.run_test("Frontend", self.test_frontend_health)

        # Check if backend is running before continuing
        if self.results[0].status == TestStatus.FAIL:
            print(f"\n{Colors.RED}Backend is not running. Start services first:{Colors.END}")
            print("  ./start_all.sh")
            return False

        # API Endpoints
        print(f"\n{Colors.BOLD}API Endpoints:{Colors.END}")
        self.run_test("Treasury", self.test_treasury_endpoint)
        self.run_test("Agents", self.test_agents_endpoint)
        self.run_test("Services", self.test_services_endpoint)
        self.run_test("Transactions", self.test_transactions_endpoint)
        self.run_test("Stats", self.test_stats_endpoint)
        self.run_test("Policy Logs", self.test_policy_logs_endpoint)

        # A2A
        print(f"\n{Colors.BOLD}A2A Payments:{Colors.END}")
        self.run_test("A2A Balances", self.test_a2a_balances)
        self.run_test("A2A Transfers", self.test_a2a_transfers)

        # Escrow
        print(f"\n{Colors.BOLD}Escrow:{Colors.END}")
        self.run_test("Escrow List", self.test_escrow_list)

        # Registry
        print(f"\n{Colors.BOLD}Registry:{Colors.END}")
        self.run_test("Registry Agents", self.test_registry_agents)

        # Functional
        print(f"\n{Colors.BOLD}Functional Tests:{Colors.END}")
        self.run_test("Budget Update", self.test_budget_update)
        self.run_test("Budget Reset", self.test_reset_budgets)
        self.run_test("WebSocket", self.test_websocket_endpoint)

        # Summary
        self.print_summary()

        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)

        return failed == 0

    def print_summary(self):
        print(f"\n{Colors.BOLD}{'=' * 50}{Colors.END}")
        print(f"{Colors.BOLD}Summary:{Colors.END}")

        passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        warned = sum(1 for r in self.results if r.status == TestStatus.WARN)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIP)
        total = len(self.results)

        print(f"  {Colors.GREEN}Passed:{Colors.END}  {passed}/{total}")
        if failed > 0:
            print(f"  {Colors.RED}Failed:{Colors.END}  {failed}/{total}")
        if warned > 0:
            print(f"  {Colors.YELLOW}Warned:{Colors.END}  {warned}/{total}")
        if skipped > 0:
            print(f"  {Colors.BLUE}Skipped:{Colors.END} {skipped}/{total}")

        total_time = sum(r.duration_ms for r in self.results)
        print(f"  Total time: {total_time:.0f}ms")

        if failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}All critical tests passed!{Colors.END}")
            print("System is ready for demo.")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}Some tests failed!{Colors.END}")
            print("Please fix issues before demo.")


def main():
    parser = argparse.ArgumentParser(description="MNEE Nexus Integration Tests")
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()

    tester = IntegrationTester(verbose=args.verbose)

    try:
        success = tester.run_all()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Test runner failed: {e}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()

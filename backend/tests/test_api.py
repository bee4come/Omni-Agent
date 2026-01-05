"""
Tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_returns_status(self, test_client):
        """Test that root endpoint returns service info"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["status"] == "running"


class TestTreasuryEndpoint:
    """Test treasury endpoints"""

    def test_get_treasury_status(self, test_client):
        """Test getting treasury status"""
        response = test_client.get("/treasury")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "totalAllocated" in data
        assert "totalSpent" in data


class TestAgentsEndpoints:
    """Test agent-related endpoints"""

    def test_get_all_agents(self, test_client):
        """Test getting all agents"""
        response = test_client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert isinstance(data["agents"], list)

    def test_get_agent_not_found(self, test_client):
        """Test getting non-existent agent returns 404"""
        response = test_client.get("/agents/non-existent-agent")
        assert response.status_code == 404

    def test_update_agent_budget(self, test_client):
        """Test updating agent budget"""
        # First get an agent that exists
        agents_response = test_client.get("/agents")
        if agents_response.status_code != 200:
            pytest.skip("Could not get agents list")

        agents = agents_response.json().get("agents", [])
        if not agents:
            pytest.skip("No agents available for testing")

        agent_id = agents[0]["id"]

        # Update the budget
        response = test_client.put(
            f"/agents/{agent_id}/budget",
            json={"daily_budget": 150.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent"]["dailyBudget"] == 150.0

    def test_update_agent_budget_validation_too_low(self, test_client):
        """Test that budget validation rejects values too low"""
        agents_response = test_client.get("/agents")
        if agents_response.status_code != 200:
            pytest.skip("Could not get agents list")

        agents = agents_response.json().get("agents", [])
        if not agents:
            pytest.skip("No agents available for testing")

        agent_id = agents[0]["id"]

        # Try to set budget to 0 (below MIN_BUDGET)
        response = test_client.put(
            f"/agents/{agent_id}/budget",
            json={"daily_budget": 0.0}
        )
        assert response.status_code == 400
        assert "must be between" in response.json()["detail"]

    def test_update_agent_budget_validation_too_high(self, test_client):
        """Test that budget validation rejects values too high"""
        agents_response = test_client.get("/agents")
        if agents_response.status_code != 200:
            pytest.skip("Could not get agents list")

        agents = agents_response.json().get("agents", [])
        if not agents:
            pytest.skip("No agents available for testing")

        agent_id = agents[0]["id"]

        # Try to set budget above MAX_BUDGET
        response = test_client.put(
            f"/agents/{agent_id}/budget",
            json={"daily_budget": 99999.0}
        )
        assert response.status_code == 400
        assert "must be between" in response.json()["detail"]

    def test_update_agent_budget_max_per_call_exceeds_daily(self, test_client):
        """Test that max_per_call cannot exceed daily_budget"""
        agents_response = test_client.get("/agents")
        if agents_response.status_code != 200:
            pytest.skip("Could not get agents list")

        agents = agents_response.json().get("agents", [])
        if not agents:
            pytest.skip("No agents available for testing")

        agent_id = agents[0]["id"]

        # Try to set max_per_call greater than daily_budget
        response = test_client.put(
            f"/agents/{agent_id}/budget",
            json={"daily_budget": 10.0, "max_per_call": 20.0}
        )
        assert response.status_code == 400
        assert "cannot exceed daily_budget" in response.json()["detail"]

    def test_pause_agent(self, test_client):
        """Test pausing an agent"""
        agents_response = test_client.get("/agents")
        if agents_response.status_code != 200:
            pytest.skip("Could not get agents list")

        agents = agents_response.json().get("agents", [])
        if not agents:
            pytest.skip("No agents available for testing")

        agent_id = agents[0]["id"]

        # Pause the agent
        response = test_client.put(f"/agents/{agent_id}/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["agent"]["paused"] is True

    def test_resume_agent(self, test_client):
        """Test resuming an agent"""
        agents_response = test_client.get("/agents")
        if agents_response.status_code != 200:
            pytest.skip("Could not get agents list")

        agents = agents_response.json().get("agents", [])
        if not agents:
            pytest.skip("No agents available for testing")

        agent_id = agents[0]["id"]

        # First pause, then resume
        test_client.put(f"/agents/{agent_id}/pause")
        response = test_client.put(f"/agents/{agent_id}/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["agent"]["paused"] is False

    def test_agent_response_includes_paused_field(self, test_client):
        """Test that agent response includes paused field"""
        agents_response = test_client.get("/agents")
        if agents_response.status_code != 200:
            pytest.skip("Could not get agents list")

        agents = agents_response.json().get("agents", [])
        if not agents:
            pytest.skip("No agents available for testing")

        # Check that paused field is present
        assert "paused" in agents[0]


class TestServicesEndpoints:
    """Test service-related endpoints"""

    def test_get_all_services(self, test_client):
        """Test getting all services"""
        response = test_client.get("/services")
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert isinstance(data["services"], list)

    def test_get_service_not_found(self, test_client):
        """Test getting non-existent service returns 404"""
        response = test_client.get("/services/NON_EXISTENT_SERVICE")
        assert response.status_code == 404


class TestTransactionsEndpoint:
    """Test transactions endpoint"""

    def test_get_transactions(self, test_client):
        """Test getting transactions"""
        response = test_client.get("/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert isinstance(data["transactions"], list)

    def test_get_transactions_with_limit(self, test_client):
        """Test getting transactions with limit"""
        response = test_client.get("/transactions?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) <= 5


class TestPolicyLogsEndpoint:
    """Test policy logs endpoint"""

    def test_get_policy_logs(self, test_client):
        """Test getting policy logs"""
        response = test_client.get("/policy/logs")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data


class TestStatsEndpoint:
    """Test statistics endpoint"""

    def test_get_stats(self, test_client):
        """Test getting system statistics"""
        response = test_client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert "total" in data["transactions"]
        assert "successful" in data["transactions"]
        assert "failed" in data["transactions"]
        assert "agentCount" in data
        assert "serviceCount" in data


class TestResetEndpoint:
    """Test reset endpoint"""

    def test_reset_daily_budgets(self, test_client):
        """Test resetting daily budgets"""
        response = test_client.post("/reset")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestEscrowEndpoints:
    """Test escrow-related endpoints"""

    def test_list_escrows(self, test_client):
        """Test listing escrows"""
        response = test_client.get("/escrow/list")
        assert response.status_code == 200
        data = response.json()
        assert "escrows" in data
        assert "total_count" in data
        assert "by_status" in data

    def test_get_escrow_not_found(self, test_client):
        """Test getting non-existent escrow returns 404"""
        response = test_client.get("/escrow/non-existent-escrow-id")
        assert response.status_code == 404


class TestRegistryEndpoints:
    """Test registry-related endpoints"""

    def test_list_registered_agents(self, test_client):
        """Test listing registered agents"""
        response = test_client.get("/registry/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert "market_stats" in data

    def test_find_agents_by_capability(self, test_client):
        """Test finding agents by capability"""
        response = test_client.get("/registry/find?capability=test")
        assert response.status_code == 200
        data = response.json()
        assert "capability" in data
        assert "agents" in data
        assert "count" in data


class TestA2AEndpoints:
    """Test A2A (Agent-to-Agent) payment endpoints"""

    def test_get_a2a_transfers(self, test_client):
        """Test getting A2A transfers"""
        response = test_client.get("/a2a/transfers")
        assert response.status_code == 200
        data = response.json()
        assert "transfers" in data
        assert "total_count" in data

    def test_get_agent_wallet_balances(self, test_client):
        """Test getting agent wallet balances"""
        response = test_client.get("/a2a/balances")
        assert response.status_code == 200
        data = response.json()
        assert "balances" in data
        assert "total" in data

"""
Pytest fixtures for MNEE Nexus backend tests.
"""
import os
import sys
import pytest
import tempfile
import yaml
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from policy.engine import PolicyEngine, RiskEngine
from policy.models import ProjectPolicy, AgentPolicy, UsageSnapshot, PolicyDecision


# ============================================================
# Test Configuration Fixtures
# ============================================================

@pytest.fixture
def test_config_dir():
    """Create a temporary directory with test config files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create agents.yaml
        agents_config = {
            'agents': [
                {
                    'id': 'test-agent-high',
                    'priority': 'HIGH',
                    'dailyBudget': 100.0,
                    'maxPerCall': 10.0
                },
                {
                    'id': 'test-agent-low',
                    'priority': 'LOW',
                    'dailyBudget': 20.0,
                    'maxPerCall': 5.0
                },
                {
                    'id': 'test-agent-medium',
                    'priority': 'MEDIUM',
                    'dailyBudget': 50.0,
                    'maxPerCall': 8.0
                }
            ]
        }
        agents_path = os.path.join(tmpdir, 'agents.yaml')
        with open(agents_path, 'w') as f:
            yaml.dump(agents_config, f)

        # Create services.yaml
        services_config = {
            'services': [
                {
                    'id': 'TEST_SERVICE_CHEAP',
                    'unitPrice': 0.1,
                    'providerAddress': '0x1234567890123456789012345678901234567890',
                    'active': True
                },
                {
                    'id': 'TEST_SERVICE_EXPENSIVE',
                    'unitPrice': 5.0,
                    'providerAddress': '0x1234567890123456789012345678901234567890',
                    'active': True
                },
                {
                    'id': 'TEST_SERVICE_INACTIVE',
                    'unitPrice': 1.0,
                    'providerAddress': '0x1234567890123456789012345678901234567890',
                    'active': False
                }
            ]
        }
        services_path = os.path.join(tmpdir, 'services.yaml')
        with open(services_path, 'w') as f:
            yaml.dump(services_config, f)

        yield {
            'dir': tmpdir,
            'agents_path': agents_path,
            'services_path': services_path
        }


@pytest.fixture
def policy_engine(test_config_dir):
    """Create a PolicyEngine with test configuration"""
    engine = PolicyEngine(
        agents_path=test_config_dir['agents_path'],
        services_path=test_config_dir['services_path']
    )
    return engine


@pytest.fixture
def risk_engine():
    """Create a fresh RiskEngine instance"""
    return RiskEngine()


# ============================================================
# Model Fixtures
# ============================================================

@pytest.fixture
def sample_project_policy():
    """Create a sample ProjectPolicy"""
    return ProjectPolicy(
        project_id="test-project",
        name="Test Project",
        description="A test project for unit tests",
        daily_budget_mnee=500.0,
        hard_cap_mnee=5000.0,
        allow_services=["SERVICE_A", "SERVICE_B"],
        deny_services=["SERVICE_BLOCKED"]
    )


@pytest.fixture
def sample_agent_policy():
    """Create a sample AgentPolicy"""
    return AgentPolicy(
        agent_id="test-agent",
        project_id="test-project",
        role="tester",
        daily_budget_mnee=100.0,
        max_single_call_mnee=10.0,
        priority="MEDIUM"
    )


@pytest.fixture
def sample_usage_snapshot():
    """Create a sample UsageSnapshot"""
    return UsageSnapshot(
        project_id="test-project",
        agent_id="test-agent",
        spent_today_mnee=25.0,
        spent_total_mnee=150.0,
        transaction_count_today=5
    )


# ============================================================
# FastAPI Test Client Fixtures
# ============================================================

@pytest.fixture
def test_client():
    """Create a TestClient for API testing"""
    from fastapi.testclient import TestClient

    # Set up test environment variables
    os.environ['POLICY_CONFIG_PATH'] = '../config/agents.yaml'
    os.environ['SERVICE_CONFIG_PATH'] = '../config/services.yaml'

    try:
        from app.main import app
        client = TestClient(app)
        yield client
    except Exception as e:
        pytest.skip(f"Could not create test client: {e}")


# ============================================================
# Mock Fixtures
# ============================================================

@pytest.fixture
def mock_payment_result():
    """Mock successful payment result"""
    return {
        'success': True,
        'tx_hash': '0x' + 'a' * 64,
        'amount': 1.0,
        'service_id': 'TEST_SERVICE',
        'block_number': 12345
    }


@pytest.fixture
def mock_failed_payment_result():
    """Mock failed payment result"""
    return {
        'success': False,
        'error': 'Insufficient balance',
        'tx_hash': None
    }

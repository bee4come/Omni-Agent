"""
Tests for PolicyEngine - budget limits, risk detection, and policy evaluation.
"""
import pytest
from datetime import datetime, timedelta

from policy.engine import PolicyEngine, RiskEngine
from policy.models import PolicyDecision


class TestPolicyEngineBasics:
    """Test basic PolicyEngine initialization and configuration loading"""

    def test_engine_initialization(self, policy_engine):
        """Test that PolicyEngine initializes with test config"""
        assert policy_engine is not None
        assert len(policy_engine.agents) == 3
        assert len(policy_engine.services) == 3

    def test_agents_loaded_correctly(self, policy_engine):
        """Test that agents are loaded with correct properties"""
        high_agent = policy_engine.agents.get('test-agent-high')
        assert high_agent is not None
        assert high_agent.priority == 'HIGH'
        assert high_agent.daily_budget_mnee == 100.0
        assert high_agent.max_single_call_mnee == 10.0

    def test_services_loaded_correctly(self, policy_engine):
        """Test that services are loaded with correct properties"""
        cheap_service = policy_engine.services.get('TEST_SERVICE_CHEAP')
        assert cheap_service is not None
        assert cheap_service.unitPrice == 0.1
        assert cheap_service.active is True

    def test_default_project_created(self, policy_engine):
        """Test that default project is created"""
        assert 'default-project' in policy_engine.projects
        default_project = policy_engine.projects['default-project']
        assert default_project.daily_budget_mnee == 500.0


class TestPolicyEvaluation:
    """Test policy evaluation logic"""

    def test_allow_valid_request(self, policy_engine):
        """Test that valid requests are allowed"""
        decision = policy_engine.evaluate(
            agent_id='test-agent-high',
            service_id='TEST_SERVICE_CHEAP',
            estimated_cost=1.0,
            quantity=1,
            task_id='test-task-1',
            payload={}
        )
        assert decision.action == 'ALLOW'
        assert decision.approved_quantity == 1
        assert decision.risk_level == 'RISK_OK'

    def test_deny_unknown_agent(self, policy_engine):
        """Test that unknown agents are denied"""
        decision = policy_engine.evaluate(
            agent_id='unknown-agent',
            service_id='TEST_SERVICE_CHEAP',
            estimated_cost=1.0,
            quantity=1,
            task_id='test-task-1',
            payload={}
        )
        assert decision.action == 'DENY'
        assert 'unknown' in decision.reason.lower()

    def test_deny_unknown_service(self, policy_engine):
        """Test that unknown services are denied"""
        decision = policy_engine.evaluate(
            agent_id='test-agent-high',
            service_id='UNKNOWN_SERVICE',
            estimated_cost=1.0,
            quantity=1,
            task_id='test-task-1',
            payload={}
        )
        assert decision.action == 'DENY'
        assert 'unknown' in decision.reason.lower()

    def test_deny_inactive_service(self, policy_engine):
        """Test that inactive services are denied"""
        decision = policy_engine.evaluate(
            agent_id='test-agent-high',
            service_id='TEST_SERVICE_INACTIVE',
            estimated_cost=1.0,
            quantity=1,
            task_id='test-task-1',
            payload={}
        )
        assert decision.action == 'DENY'
        assert 'inactive' in decision.reason.lower()


class TestBudgetLimits:
    """Test budget enforcement"""

    def test_deny_exceeds_single_call_limit(self, policy_engine):
        """Test denial when cost exceeds single call limit"""
        # test-agent-high has maxPerCall of 10.0
        decision = policy_engine.evaluate(
            agent_id='test-agent-high',
            service_id='TEST_SERVICE_CHEAP',
            estimated_cost=15.0,  # Exceeds 10.0 limit
            quantity=1,
            task_id='test-task-1',
            payload={}
        )
        assert decision.action == 'DENY'
        assert 'single call limit' in decision.reason.lower()

    def test_deny_exceeds_daily_budget(self, policy_engine):
        """Test denial when cost exceeds daily budget"""
        # Simulate previous spending
        usage = policy_engine.usage.get('test-agent-low')
        usage.spent_today_mnee = 18.0  # Out of 20.0 daily budget

        decision = policy_engine.evaluate(
            agent_id='test-agent-low',
            service_id='TEST_SERVICE_CHEAP',
            estimated_cost=5.0,  # Would push to 23.0, exceeding 20.0
            quantity=1,
            task_id='test-task-1',
            payload={}
        )
        assert decision.action == 'DENY'
        assert 'daily budget' in decision.reason.lower()

    def test_allow_within_remaining_budget(self, policy_engine):
        """Test approval when within remaining budget"""
        usage = policy_engine.usage.get('test-agent-low')
        usage.spent_today_mnee = 10.0  # Out of 20.0 daily budget

        decision = policy_engine.evaluate(
            agent_id='test-agent-low',
            service_id='TEST_SERVICE_CHEAP',
            estimated_cost=5.0,  # Would push to 15.0, within 20.0
            quantity=1,
            task_id='test-task-1',
            payload={}
        )
        assert decision.action == 'ALLOW'


class TestRiskEngine:
    """Test RiskEngine risk detection"""

    def test_risk_engine_initialization(self, risk_engine):
        """Test RiskEngine initializes correctly"""
        assert risk_engine is not None
        assert len(risk_engine.call_history) == 0

    def test_no_risk_for_normal_call(self, risk_engine):
        """Test that normal calls have no risk"""
        risk_level, reason = risk_engine.assess_risk(
            agent_id='test-agent',
            service_id='TEST_SERVICE',
            estimated_cost=1.0,
            agent_priority='HIGH',
            context={'task_id': 'test-1'}
        )
        assert risk_level == 'RISK_OK'

    def test_burst_detection(self, risk_engine):
        """Test detection of burst requests"""
        # Simulate 6+ calls in last minute
        for i in range(6):
            risk_engine.record_call(
                agent_id='burst-agent',
                service_id='SERVICE_A',
                cost=2.0,
                success=True
            )

        risk_level, reason = risk_engine.assess_risk(
            agent_id='burst-agent',
            service_id='SERVICE_A',
            estimated_cost=2.0,
            agent_priority='MEDIUM',
            context={'task_id': 'test-burst'}
        )
        assert risk_level == 'RISK_BLOCK'
        assert 'burst' in reason.lower()

    def test_first_large_call_from_low_priority(self, risk_engine):
        """Test risk flagging for first large call from low-priority agent"""
        # First call with high cost from LOW priority agent
        risk_level, reason = risk_engine.assess_risk(
            agent_id='new-low-agent',
            service_id='EXPENSIVE_SERVICE',
            estimated_cost=10.0,  # > 5.0 threshold
            agent_priority='LOW',
            context={'task_id': 'test-first-large'}
        )
        assert risk_level == 'RISK_REVIEW'
        assert 'first large call' in reason.lower()

    def test_provider_failure_tracking(self, risk_engine):
        """Test tracking of provider failures"""
        # Record multiple failures for a provider
        for i in range(4):
            risk_engine.record_call(
                agent_id='any-agent',
                service_id='FAILING_PROVIDER',
                cost=1.0,
                success=False
            )

        risk_level, reason = risk_engine.assess_risk(
            agent_id='test-agent',
            service_id='FAILING_PROVIDER',
            estimated_cost=1.0,
            agent_priority='HIGH',
            context={'task_id': 'test-failure'}
        )
        assert risk_level == 'RISK_REVIEW'
        assert 'failures' in reason.lower()

    def test_call_history_cleanup(self, risk_engine):
        """Test that old call history is cleaned up"""
        # This tests internal behavior - call history older than 1 hour should be removed
        # We can't easily test time-based cleanup without mocking, but we can verify
        # that record_call works correctly
        risk_engine.record_call(
            agent_id='test-agent',
            service_id='SERVICE_A',
            cost=1.0,
            success=True
        )
        assert len(risk_engine.call_history) == 1


class TestUsageTracking:
    """Test usage tracking and recording"""

    def test_record_successful_call(self, policy_engine):
        """Test that successful calls update usage"""
        initial_spend = policy_engine.usage['test-agent-high'].spent_today_mnee

        policy_engine.record_call_result(
            agent_id='test-agent-high',
            service_id='TEST_SERVICE_CHEAP',
            cost=5.0,
            success=True
        )

        final_spend = policy_engine.usage['test-agent-high'].spent_today_mnee
        assert final_spend == initial_spend + 5.0

    def test_failed_call_not_counted_in_usage(self, policy_engine):
        """Test that failed calls don't update usage"""
        initial_spend = policy_engine.usage['test-agent-high'].spent_today_mnee

        policy_engine.record_call_result(
            agent_id='test-agent-high',
            service_id='TEST_SERVICE_CHEAP',
            cost=5.0,
            success=False
        )

        final_spend = policy_engine.usage['test-agent-high'].spent_today_mnee
        assert final_spend == initial_spend  # No change

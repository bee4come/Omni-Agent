"""
Tests for the database persistence layer.
"""
import pytest
import tempfile
import os

from db.models import init_database, TransactionRecord, PolicyLogRecord, EscrowRecord
from db.repository import DatabaseRepository


@pytest.fixture
def test_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    db_url = f"sqlite:///{db_path}"
    repo = DatabaseRepository(db_url)

    yield repo

    # Cleanup
    os.unlink(db_path)


class TestTransactionRepository:
    """Test transaction CRUD operations."""

    def test_log_transaction(self, test_db):
        """Test logging a transaction."""
        result = test_db.log_transaction(
            agent_id='test-agent',
            service_id='TEST_SERVICE',
            task_id='task-1',
            amount=1.5,
            status='SUCCESS',
            tx_hash='0x' + 'a' * 64
        )

        assert result is not None
        assert result['agent_id'] == 'test-agent'
        assert result['amount'] == 1.5
        assert result['status'] == 'SUCCESS'

    def test_get_recent_transactions(self, test_db):
        """Test getting recent transactions."""
        # Log some transactions
        for i in range(5):
            test_db.log_transaction(
                agent_id=f'agent-{i}',
                service_id='SERVICE_A',
                task_id=f'task-{i}',
                amount=float(i + 1),
                status='SUCCESS'
            )

        results = test_db.get_recent_transactions(limit=3)
        assert len(results) == 3

    def test_get_agent_transactions(self, test_db):
        """Test getting transactions for a specific agent."""
        # Log transactions for different agents
        test_db.log_transaction(
            agent_id='agent-a',
            service_id='SERVICE_A',
            task_id='task-1',
            amount=1.0,
            status='SUCCESS'
        )
        test_db.log_transaction(
            agent_id='agent-b',
            service_id='SERVICE_A',
            task_id='task-2',
            amount=2.0,
            status='SUCCESS'
        )
        test_db.log_transaction(
            agent_id='agent-a',
            service_id='SERVICE_B',
            task_id='task-3',
            amount=3.0,
            status='SUCCESS'
        )

        results = test_db.get_agent_transactions('agent-a')
        assert len(results) == 2
        assert all(r['agent_id'] == 'agent-a' for r in results)

    def test_get_total_spent_by_agent(self, test_db):
        """Test calculating total spent by an agent."""
        test_db.log_transaction(
            agent_id='spender',
            service_id='SERVICE_A',
            task_id='task-1',
            amount=10.0,
            status='SUCCESS'
        )
        test_db.log_transaction(
            agent_id='spender',
            service_id='SERVICE_B',
            task_id='task-2',
            amount=5.0,
            status='SUCCESS'
        )
        test_db.log_transaction(
            agent_id='spender',
            service_id='SERVICE_C',
            task_id='task-3',
            amount=7.0,
            status='FAILED'  # Should not count
        )

        total = test_db.get_total_spent_by_agent('spender')
        assert total == 15.0  # 10 + 5, not 7 (failed)


class TestPolicyLogRepository:
    """Test policy log CRUD operations."""

    def test_log_policy_decision(self, test_db):
        """Test logging a policy decision."""
        result = test_db.log_policy_decision(
            agent_id='test-agent',
            service_id='TEST_SERVICE',
            action='ALLOW',
            reason='Within budget',
            estimated_cost=5.0,
            risk_level='RISK_OK'
        )

        assert result is not None
        assert result['action'] == 'ALLOW'
        assert result['risk_level'] == 'RISK_OK'

    def test_get_recent_policy_logs(self, test_db):
        """Test getting recent policy logs."""
        for i in range(5):
            test_db.log_policy_decision(
                agent_id=f'agent-{i}',
                service_id='SERVICE_A',
                action='ALLOW' if i % 2 == 0 else 'DENY',
                reason=f'Reason {i}'
            )

        results = test_db.get_recent_policy_logs(limit=3)
        assert len(results) == 3

    def test_get_policy_stats(self, test_db):
        """Test getting policy decision statistics."""
        # Log various decisions
        for _ in range(3):
            test_db.log_policy_decision(
                agent_id='agent-1',
                service_id='SERVICE_A',
                action='ALLOW',
                reason='OK'
            )
        for _ in range(2):
            test_db.log_policy_decision(
                agent_id='agent-1',
                service_id='SERVICE_A',
                action='DENY',
                reason='Budget exceeded'
            )

        stats = test_db.get_policy_stats()
        assert stats.get('ALLOW') == 3
        assert stats.get('DENY') == 2


class TestEscrowRepository:
    """Test escrow CRUD operations."""

    def test_create_escrow(self, test_db):
        """Test creating an escrow."""
        result = test_db.create_escrow(
            escrow_id='escrow-1',
            payer_agent_id='agent-a',
            payee_agent_id='agent-b',
            amount=100.0,
            task_description='Complete task'
        )

        assert result is not None
        assert result['escrow_id'] == 'escrow-1'
        assert result['status'] == 'created'
        assert result['amount'] == 100.0

    def test_update_escrow_status(self, test_db):
        """Test updating escrow status."""
        test_db.create_escrow(
            escrow_id='escrow-2',
            payer_agent_id='agent-a',
            payee_agent_id='agent-b',
            amount=50.0
        )

        result = test_db.update_escrow_status(
            escrow_id='escrow-2',
            status='released',
            verification_result='Task completed successfully'
        )

        assert result['status'] == 'released'
        assert result['verification_result'] == 'Task completed successfully'
        assert result['resolved_at'] is not None

    def test_get_escrow(self, test_db):
        """Test getting a specific escrow."""
        test_db.create_escrow(
            escrow_id='escrow-3',
            payer_agent_id='agent-a',
            payee_agent_id='agent-b',
            amount=75.0
        )

        result = test_db.get_escrow('escrow-3')
        assert result is not None
        assert result['escrow_id'] == 'escrow-3'

        # Test non-existent
        result = test_db.get_escrow('non-existent')
        assert result is None

    def test_get_escrows_by_status(self, test_db):
        """Test filtering escrows by status."""
        test_db.create_escrow(
            escrow_id='escrow-4',
            payer_agent_id='agent-a',
            payee_agent_id='agent-b',
            amount=10.0
        )
        test_db.create_escrow(
            escrow_id='escrow-5',
            payer_agent_id='agent-a',
            payee_agent_id='agent-c',
            amount=20.0
        )
        test_db.update_escrow_status('escrow-5', 'released')

        created = test_db.get_escrows_by_status('created')
        released = test_db.get_escrows_by_status('released')

        assert len(created) == 1
        assert len(released) == 1


class TestAgentUsageRepository:
    """Test agent usage tracking."""

    def test_update_agent_usage(self, test_db):
        """Test updating agent usage."""
        result = test_db.update_agent_usage(
            agent_id='usage-agent',
            project_id='project-1',
            amount_spent=5.0,
            success=True
        )

        assert result['agent_id'] == 'usage-agent'
        assert result['spent_today'] == 5.0
        assert result['successful_calls'] == 1

        # Update again
        result = test_db.update_agent_usage(
            agent_id='usage-agent',
            project_id='project-1',
            amount_spent=3.0,
            success=False
        )

        assert result['spent_today'] == 8.0
        assert result['successful_calls'] == 1
        assert result['failed_calls'] == 1

    def test_record_denied_call(self, test_db):
        """Test recording denied calls."""
        test_db.record_denied_call('denied-agent', 'project-1')
        test_db.record_denied_call('denied-agent', 'project-1')

        result = test_db.get_agent_usage_today('denied-agent')
        assert result['denied_calls'] == 2

    def test_get_agent_usage_today(self, test_db):
        """Test getting today's usage."""
        test_db.update_agent_usage(
            agent_id='today-agent',
            project_id='project-1',
            amount_spent=10.0,
            success=True
        )

        result = test_db.get_agent_usage_today('today-agent')
        assert result is not None
        assert result['spent_today'] == 10.0

        # Non-existent agent
        result = test_db.get_agent_usage_today('non-existent')
        assert result is None


class TestSystemStats:
    """Test system statistics."""

    def test_get_system_stats(self, test_db):
        """Test getting system statistics."""
        # Create some data
        test_db.log_transaction(
            agent_id='agent-1',
            service_id='SERVICE_A',
            task_id='task-1',
            amount=10.0,
            status='SUCCESS'
        )
        test_db.log_policy_decision(
            agent_id='agent-1',
            service_id='SERVICE_A',
            action='ALLOW',
            reason='OK'
        )
        test_db.create_escrow(
            escrow_id='stats-escrow',
            payer_agent_id='agent-1',
            payee_agent_id='agent-2',
            amount=50.0
        )

        stats = test_db.get_system_stats()

        assert 'transactions' in stats
        assert 'policy_actions' in stats
        assert 'escrows' in stats
        assert stats['transactions']['total'] >= 1
        assert stats['escrows']['total'] >= 1

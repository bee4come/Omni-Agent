"""
Database repository for MNEE Nexus.
Provides CRUD operations for all database tables.
"""
import os
from datetime import datetime, date
from typing import List, Dict, Optional, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, desc, and_
from sqlalchemy.orm import sessionmaker, Session

from .models import (
    Base, TransactionRecord, PolicyLogRecord,
    EscrowRecord, AgentUsageRecord, init_database
)

# Singleton repository instance
_repository: Optional['DatabaseRepository'] = None


def get_repository() -> 'DatabaseRepository':
    """Get or create the singleton repository instance."""
    global _repository
    if _repository is None:
        db_path = os.environ.get('MNEE_DB_PATH', 'mnee_nexus.db')
        db_url = f"sqlite:///{db_path}"
        _repository = DatabaseRepository(db_url)
    return _repository


class DatabaseRepository:
    """
    Repository class providing CRUD operations for all tables.
    Thread-safe with session-per-request pattern.
    """

    def __init__(self, db_url: str = "sqlite:///mnee_nexus.db"):
        """
        Initialize the repository with database connection.

        Args:
            db_url: SQLAlchemy database URL
        """
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionFactory = sessionmaker(bind=self.engine)

    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations."""
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ============================================================
    # Transaction Records
    # ============================================================

    def log_transaction(
        self,
        agent_id: str,
        service_id: str,
        task_id: str,
        amount: float,
        status: str,
        tx_hash: Optional[str] = None,
        service_call_hash: Optional[str] = None,
        block_number: Optional[int] = None,
        gas_used: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> TransactionRecord:
        """Log a new transaction."""
        with self.session_scope() as session:
            record = TransactionRecord(
                agent_id=agent_id,
                service_id=service_id,
                task_id=task_id,
                amount=amount,
                status=status,
                tx_hash=tx_hash,
                service_call_hash=service_call_hash,
                block_number=block_number,
                gas_used=gas_used,
                error_message=error_message
            )
            session.add(record)
            session.flush()
            return record.to_dict()

    def get_recent_transactions(self, limit: int = 50) -> List[Dict]:
        """Get recent transactions."""
        with self.session_scope() as session:
            records = session.query(TransactionRecord)\
                .order_by(desc(TransactionRecord.timestamp))\
                .limit(limit)\
                .all()
            return [r.to_dict() for r in records]

    def get_agent_transactions(self, agent_id: str, limit: int = 100) -> List[Dict]:
        """Get transactions for a specific agent."""
        with self.session_scope() as session:
            records = session.query(TransactionRecord)\
                .filter(TransactionRecord.agent_id == agent_id)\
                .order_by(desc(TransactionRecord.timestamp))\
                .limit(limit)\
                .all()
            return [r.to_dict() for r in records]

    def get_service_transactions(self, service_id: str, limit: int = 100) -> List[Dict]:
        """Get transactions for a specific service."""
        with self.session_scope() as session:
            records = session.query(TransactionRecord)\
                .filter(TransactionRecord.service_id == service_id)\
                .order_by(desc(TransactionRecord.timestamp))\
                .limit(limit)\
                .all()
            return [r.to_dict() for r in records]

    def get_total_spent_by_agent(self, agent_id: str) -> float:
        """Get total amount spent by an agent."""
        with self.session_scope() as session:
            from sqlalchemy import func
            result = session.query(func.sum(TransactionRecord.amount))\
                .filter(and_(
                    TransactionRecord.agent_id == agent_id,
                    TransactionRecord.status == 'SUCCESS'
                ))\
                .scalar()
            return result or 0.0

    def get_total_revenue_by_service(self, service_id: str) -> float:
        """Get total revenue for a service."""
        with self.session_scope() as session:
            from sqlalchemy import func
            result = session.query(func.sum(TransactionRecord.amount))\
                .filter(and_(
                    TransactionRecord.service_id == service_id,
                    TransactionRecord.status == 'SUCCESS'
                ))\
                .scalar()
            return result or 0.0

    # ============================================================
    # Policy Log Records
    # ============================================================

    def log_policy_decision(
        self,
        agent_id: str,
        service_id: str,
        action: str,
        reason: str,
        estimated_cost: Optional[float] = None,
        risk_level: str = "RISK_OK",
        task_id: Optional[str] = None,
        agent_budget_remaining: Optional[float] = None,
        project_budget_remaining: Optional[float] = None
    ) -> PolicyLogRecord:
        """Log a policy decision."""
        with self.session_scope() as session:
            record = PolicyLogRecord(
                agent_id=agent_id,
                service_id=service_id,
                action=action,
                reason=reason,
                estimated_cost=estimated_cost,
                risk_level=risk_level,
                task_id=task_id,
                agent_budget_remaining=agent_budget_remaining,
                project_budget_remaining=project_budget_remaining
            )
            session.add(record)
            session.flush()
            return record.to_dict()

    def get_recent_policy_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent policy logs."""
        with self.session_scope() as session:
            records = session.query(PolicyLogRecord)\
                .order_by(desc(PolicyLogRecord.timestamp))\
                .limit(limit)\
                .all()
            return [r.to_dict() for r in records]

    def get_policy_logs_by_agent(self, agent_id: str, limit: int = 100) -> List[Dict]:
        """Get policy logs for a specific agent."""
        with self.session_scope() as session:
            records = session.query(PolicyLogRecord)\
                .filter(PolicyLogRecord.agent_id == agent_id)\
                .order_by(desc(PolicyLogRecord.timestamp))\
                .limit(limit)\
                .all()
            return [r.to_dict() for r in records]

    def get_policy_stats(self) -> Dict[str, int]:
        """Get policy decision statistics."""
        with self.session_scope() as session:
            from sqlalchemy import func
            results = session.query(
                PolicyLogRecord.action,
                func.count(PolicyLogRecord.id)
            ).group_by(PolicyLogRecord.action).all()
            return {action: count for action, count in results}

    # ============================================================
    # Escrow Records
    # ============================================================

    def create_escrow(
        self,
        escrow_id: str,
        payer_agent_id: str,
        payee_agent_id: str,
        amount: float,
        task_description: Optional[str] = None
    ) -> Dict:
        """Create a new escrow record."""
        with self.session_scope() as session:
            record = EscrowRecord(
                escrow_id=escrow_id,
                payer_agent_id=payer_agent_id,
                payee_agent_id=payee_agent_id,
                amount=amount,
                task_description=task_description,
                status='created'
            )
            session.add(record)
            session.flush()
            return record.to_dict()

    def update_escrow_status(
        self,
        escrow_id: str,
        status: str,
        verification_result: Optional[str] = None,
        dispute_reason: Optional[str] = None
    ) -> Optional[Dict]:
        """Update escrow status."""
        with self.session_scope() as session:
            record = session.query(EscrowRecord)\
                .filter(EscrowRecord.escrow_id == escrow_id)\
                .first()
            if not record:
                return None

            record.status = status
            if verification_result:
                record.verification_result = verification_result
                record.verified_at = datetime.utcnow()
            if dispute_reason:
                record.dispute_reason = dispute_reason
            if status in ('released', 'refunded'):
                record.resolved_at = datetime.utcnow()

            session.flush()
            return record.to_dict()

    def get_escrow(self, escrow_id: str) -> Optional[Dict]:
        """Get a specific escrow by ID."""
        with self.session_scope() as session:
            record = session.query(EscrowRecord)\
                .filter(EscrowRecord.escrow_id == escrow_id)\
                .first()
            return record.to_dict() if record else None

    def get_all_escrows(self) -> List[Dict]:
        """Get all escrows."""
        with self.session_scope() as session:
            records = session.query(EscrowRecord)\
                .order_by(desc(EscrowRecord.created_at))\
                .all()
            return [r.to_dict() for r in records]

    def get_escrows_by_status(self, status: str) -> List[Dict]:
        """Get escrows by status."""
        with self.session_scope() as session:
            records = session.query(EscrowRecord)\
                .filter(EscrowRecord.status == status)\
                .order_by(desc(EscrowRecord.created_at))\
                .all()
            return [r.to_dict() for r in records]

    # ============================================================
    # Agent Usage Records
    # ============================================================

    def update_agent_usage(
        self,
        agent_id: str,
        project_id: str,
        amount_spent: float,
        success: bool
    ) -> Dict:
        """Update agent's daily usage."""
        today = date.today().isoformat()

        with self.session_scope() as session:
            record = session.query(AgentUsageRecord)\
                .filter(and_(
                    AgentUsageRecord.date == today,
                    AgentUsageRecord.agent_id == agent_id
                ))\
                .first()

            if not record:
                record = AgentUsageRecord(
                    date=today,
                    agent_id=agent_id,
                    project_id=project_id,
                    spent_today=0.0,
                    transaction_count=0,
                    successful_calls=0,
                    failed_calls=0,
                    denied_calls=0
                )
                session.add(record)

            record.spent_today = (record.spent_today or 0.0) + amount_spent
            record.transaction_count = (record.transaction_count or 0) + 1
            if success:
                record.successful_calls = (record.successful_calls or 0) + 1
            else:
                record.failed_calls = (record.failed_calls or 0) + 1

            session.flush()
            return record.to_dict()

    def record_denied_call(self, agent_id: str, project_id: str) -> Dict:
        """Record a denied call for an agent."""
        today = date.today().isoformat()

        with self.session_scope() as session:
            record = session.query(AgentUsageRecord)\
                .filter(and_(
                    AgentUsageRecord.date == today,
                    AgentUsageRecord.agent_id == agent_id
                ))\
                .first()

            if not record:
                record = AgentUsageRecord(
                    date=today,
                    agent_id=agent_id,
                    project_id=project_id,
                    spent_today=0.0,
                    transaction_count=0,
                    successful_calls=0,
                    failed_calls=0,
                    denied_calls=0
                )
                session.add(record)

            record.denied_calls = (record.denied_calls or 0) + 1
            session.flush()
            return record.to_dict()

    def get_agent_usage_today(self, agent_id: str) -> Optional[Dict]:
        """Get agent's usage for today."""
        today = date.today().isoformat()

        with self.session_scope() as session:
            record = session.query(AgentUsageRecord)\
                .filter(and_(
                    AgentUsageRecord.date == today,
                    AgentUsageRecord.agent_id == agent_id
                ))\
                .first()
            return record.to_dict() if record else None

    def get_usage_history(
        self,
        agent_id: str,
        days: int = 7
    ) -> List[Dict]:
        """Get agent's usage history for the last N days."""
        with self.session_scope() as session:
            records = session.query(AgentUsageRecord)\
                .filter(AgentUsageRecord.agent_id == agent_id)\
                .order_by(desc(AgentUsageRecord.date))\
                .limit(days)\
                .all()
            return [r.to_dict() for r in records]

    # ============================================================
    # Statistics
    # ============================================================

    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        with self.session_scope() as session:
            from sqlalchemy import func

            # Transaction stats
            total_tx = session.query(func.count(TransactionRecord.id)).scalar() or 0
            successful_tx = session.query(func.count(TransactionRecord.id))\
                .filter(TransactionRecord.status == 'SUCCESS').scalar() or 0
            total_volume = session.query(func.sum(TransactionRecord.amount))\
                .filter(TransactionRecord.status == 'SUCCESS').scalar() or 0.0

            # Policy stats
            policy_stats = self.get_policy_stats()

            # Escrow stats
            total_escrows = session.query(func.count(EscrowRecord.id)).scalar() or 0
            active_escrows = session.query(func.count(EscrowRecord.id))\
                .filter(EscrowRecord.status.in_(['created', 'submitted', 'verifying']))\
                .scalar() or 0

            return {
                'transactions': {
                    'total': total_tx,
                    'successful': successful_tx,
                    'failed': total_tx - successful_tx,
                    'total_volume': total_volume
                },
                'policy_actions': policy_stats,
                'escrows': {
                    'total': total_escrows,
                    'active': active_escrows
                }
            }

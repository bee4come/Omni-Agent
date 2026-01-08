"""
SQLAlchemy models for MNEE Nexus database.

Tables:
- transactions: Payment transaction records
- policy_logs: Policy decision audit log
- escrows: Escrow transaction records
- agent_usage: Daily usage snapshots per agent
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    Text, ForeignKey, Index, create_engine
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class TransactionRecord(Base):
    """
    Records all payment transactions between agents and services.
    """
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    service_id = Column(String(100), nullable=False, index=True)
    task_id = Column(String(200), nullable=False)
    amount = Column(Float, nullable=False)
    tx_hash = Column(String(66), nullable=True)  # Ethereum tx hash (0x + 64 chars)
    status = Column(String(20), nullable=False, index=True)  # SUCCESS, FAILED, MOCK
    service_call_hash = Column(String(100), nullable=True)  # Anti-spoofing hash

    # Additional metadata
    block_number = Column(Integer, nullable=True)
    gas_used = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index('ix_transactions_agent_status', 'agent_id', 'status'),
        Index('ix_transactions_service_status', 'service_id', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'agent_id': self.agent_id,
            'service_id': self.service_id,
            'task_id': self.task_id,
            'amount': self.amount,
            'tx_hash': self.tx_hash,
            'status': self.status,
            'service_call_hash': self.service_call_hash,
            'block_number': self.block_number,
            'gas_used': self.gas_used,
            'error_message': self.error_message
        }


class PolicyLogRecord(Base):
    """
    Records all policy decisions for auditing.
    """
    __tablename__ = 'policy_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    agent_id = Column(String(100), nullable=False, index=True)
    service_id = Column(String(100), nullable=False, index=True)
    action = Column(String(20), nullable=False, index=True)  # ALLOW, DENY, DOWNGRADE
    reason = Column(Text, nullable=False)
    estimated_cost = Column(Float, nullable=True)
    risk_level = Column(String(20), default='RISK_OK')  # RISK_OK, RISK_REVIEW, RISK_BLOCK

    # Context
    task_id = Column(String(200), nullable=True)
    agent_budget_remaining = Column(Float, nullable=True)
    project_budget_remaining = Column(Float, nullable=True)

    __table_args__ = (
        Index('ix_policy_logs_agent_action', 'agent_id', 'action'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'agent_id': self.agent_id,
            'service_id': self.service_id,
            'action': self.action,
            'reason': self.reason,
            'cost': self.estimated_cost,
            'risk_level': self.risk_level,
            'task_id': self.task_id
        }


class EscrowRecord(Base):
    """
    Records escrow transactions for A2A payments.
    """
    __tablename__ = 'escrows'

    id = Column(Integer, primary_key=True, autoincrement=True)
    escrow_id = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Parties
    payer_agent_id = Column(String(100), nullable=False, index=True)
    payee_agent_id = Column(String(100), nullable=False, index=True)

    # Transaction details
    amount = Column(Float, nullable=False)
    task_description = Column(Text, nullable=True)

    # Status tracking
    status = Column(String(20), nullable=False, index=True)  # created, submitted, verifying, released, refunded, disputed

    # Verification
    verification_result = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    # Resolution
    dispute_reason = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'escrow_id': self.escrow_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'payer_agent_id': self.payer_agent_id,
            'payee_agent_id': self.payee_agent_id,
            'amount': self.amount,
            'task_description': self.task_description,
            'status': self.status,
            'verification_result': self.verification_result,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'dispute_reason': self.dispute_reason,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class AgentUsageRecord(Base):
    """
    Daily usage snapshots for agents.
    """
    __tablename__ = 'agent_usage'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD format
    agent_id = Column(String(100), nullable=False)
    project_id = Column(String(100), nullable=False)

    spent_today = Column(Float, default=0.0)
    transaction_count = Column(Integer, default=0)

    # Stats
    successful_calls = Column(Integer, default=0)
    failed_calls = Column(Integer, default=0)
    denied_calls = Column(Integer, default=0)

    __table_args__ = (
        Index('ix_agent_usage_date_agent', 'date', 'agent_id', unique=True),
    )

    def to_dict(self):
        return {
            'date': self.date,
            'agent_id': self.agent_id,
            'project_id': self.project_id,
            'spent_today': self.spent_today,
            'transaction_count': self.transaction_count,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'denied_calls': self.denied_calls
        }


def init_database(db_url: str = "sqlite:///mnee_nexus.db"):
    """
    Initialize the database and create all tables.

    Args:
        db_url: Database connection URL. Defaults to SQLite file.

    Returns:
        SQLAlchemy engine instance
    """
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    return engine

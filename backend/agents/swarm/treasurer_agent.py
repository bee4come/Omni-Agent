"""
Treasurer Agent - Transaction Recording and Auditing

Responsibilities:
- Record all transactions
- Maintain audit trail
- Generate financial reports
- Track agent spending patterns
- Alert on anomalies
"""

from typing import Dict, List, Optional
from datetime import datetime, date
from collections import defaultdict
from pydantic import BaseModel


class TransactionRecord(BaseModel):
    """Complete transaction record"""
    record_id: str
    timestamp: str
    agent_id: str
    service_id: str
    task_id: str
    payment_id: str
    tx_hash: Optional[str] = None
    amount: float
    status: str  # "success", "failed", "pending"
    service_call_hash: str
    policy_action: str  # "ALLOW", "DENY", "DOWNGRADE"
    risk_level: str  # "RISK_OK", "RISK_REVIEW", "RISK_BLOCK"


class TreasurerAgent:
    """
    Treasurer Agent - Financial record keeper and auditor

    The Treasurer maintains a complete audit trail of all
    financial transactions in the system.
    """

    def __init__(self, agent_id: str = "treasurer-agent"):
        self.agent_id = agent_id
        self.transactions: List[TransactionRecord] = []
        self.daily_totals: Dict[str, float] = defaultdict(float)
        self.agent_spending: Dict[str, float] = defaultdict(float)
        self.service_revenue: Dict[str, float] = defaultdict(float)

    def record_transaction(self, receipt: Dict) -> TransactionRecord:
        """
        Record a transaction from Customer Agent

        Args:
            receipt: Payment receipt from Customer Agent

        Returns:
            TransactionRecord for audit trail
        """
        record = TransactionRecord(
            record_id=f"rec-{len(self.transactions) + 1:06d}",
            timestamp=datetime.now().isoformat(),
            agent_id=receipt.get("agent_id", "unknown"),
            service_id=receipt.get("service_id", "unknown"),
            task_id=receipt.get("task_id", "unknown"),
            payment_id=receipt.get("payment_id", ""),
            tx_hash=receipt.get("tx_hash", ""),
            amount=receipt.get("amount", 0.0),
            status=receipt.get("status", "success"),
            service_call_hash=receipt.get("service_call_hash", ""),
            policy_action=receipt.get("policy_action", "ALLOW"),
            risk_level=receipt.get("risk_level", "RISK_OK")
        )

        self.transactions.append(record)

        # Update aggregates
        today = date.today().isoformat()
        self.daily_totals[today] += record.amount
        self.agent_spending[record.agent_id] += record.amount
        self.service_revenue[record.service_id] += record.amount

        print(f"[TREASURER] Recorded transaction {record.record_id}: {record.amount} MNEE")

        return record

    def get_daily_report(self, target_date: Optional[str] = None) -> Dict:
        """
        Generate daily financial report

        Args:
            target_date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Daily report with spending breakdown
        """
        if target_date is None:
            target_date = date.today().isoformat()

        day_transactions = [
            t for t in self.transactions
            if t.timestamp.startswith(target_date)
        ]

        agent_breakdown = defaultdict(float)
        service_breakdown = defaultdict(float)
        successful_count = 0
        failed_count = 0

        for t in day_transactions:
            agent_breakdown[t.agent_id] += t.amount
            service_breakdown[t.service_id] += t.amount
            if t.status == "success":
                successful_count += 1
            else:
                failed_count += 1

        return {
            "date": target_date,
            "total_transactions": len(day_transactions),
            "successful_transactions": successful_count,
            "failed_transactions": failed_count,
            "total_spending": self.daily_totals[target_date],
            "spending_by_agent": dict(agent_breakdown),
            "spending_by_service": dict(service_breakdown)
        }

    def get_agent_report(self, agent_id: str) -> Dict:
        """
        Generate report for specific agent

        Args:
            agent_id: Agent to generate report for

        Returns:
            Agent-specific financial report
        """
        agent_transactions = [
            t for t in self.transactions
            if t.agent_id == agent_id
        ]

        service_usage = defaultdict(int)
        service_spending = defaultdict(float)
        risk_alerts = 0

        for t in agent_transactions:
            service_usage[t.service_id] += 1
            service_spending[t.service_id] += t.amount
            if t.risk_level == "RISK_REVIEW" or t.risk_level == "RISK_BLOCK":
                risk_alerts += 1

        return {
            "agent_id": agent_id,
            "total_transactions": len(agent_transactions),
            "total_spending": self.agent_spending[agent_id],
            "services_used": dict(service_usage),
            "spending_by_service": dict(service_spending),
            "risk_alerts": risk_alerts,
            "average_transaction": (
                self.agent_spending[agent_id] / len(agent_transactions)
                if agent_transactions else 0.0
            )
        }

    def get_service_report(self, service_id: str) -> Dict:
        """
        Generate report for specific service

        Args:
            service_id: Service to generate report for

        Returns:
            Service-specific financial report
        """
        service_transactions = [
            t for t in self.transactions
            if t.service_id == service_id
        ]

        agent_usage = defaultdict(int)
        policy_actions = defaultdict(int)

        for t in service_transactions:
            agent_usage[t.agent_id] += 1
            policy_actions[t.policy_action] += 1

        return {
            "service_id": service_id,
            "total_transactions": len(service_transactions),
            "total_revenue": self.service_revenue[service_id],
            "usage_by_agent": dict(agent_usage),
            "policy_actions": dict(policy_actions),
            "average_revenue": (
                self.service_revenue[service_id] / len(service_transactions)
                if service_transactions else 0.0
            )
        }

    def detect_anomalies(self) -> List[Dict]:
        """
        Detect spending anomalies

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Check for agents with high spending
        for agent_id, spending in self.agent_spending.items():
            if spending > 100.0:  # Threshold
                anomalies.append({
                    "type": "high_spending",
                    "agent_id": agent_id,
                    "amount": spending,
                    "severity": "warning"
                })

        # Check for failed transactions
        failed = [t for t in self.transactions if t.status == "failed"]
        if len(failed) > 5:  # More than 5 failures
            anomalies.append({
                "type": "high_failure_rate",
                "count": len(failed),
                "severity": "error"
            })

        # Check for risk alerts
        risk_transactions = [
            t for t in self.transactions
            if t.risk_level in ["RISK_REVIEW", "RISK_BLOCK"]
        ]
        if len(risk_transactions) > 3:
            anomalies.append({
                "type": "high_risk_activity",
                "count": len(risk_transactions),
                "severity": "critical"
            })

        return anomalies

    def get_summary(self) -> Dict:
        """Get overall financial summary"""
        return {
            "total_transactions": len(self.transactions),
            "total_volume": sum(t.amount for t in self.transactions),
            "unique_agents": len(self.agent_spending),
            "unique_services": len(self.service_revenue),
            "success_rate": (
                len([t for t in self.transactions if t.status == "success"]) / len(self.transactions) * 100
                if self.transactions else 0.0
            ),
            "top_spending_agent": max(self.agent_spending.items(), key=lambda x: x[1])[0] if self.agent_spending else None,
            "top_revenue_service": max(self.service_revenue.items(), key=lambda x: x[1])[0] if self.service_revenue else None,
            "anomalies_detected": len(self.detect_anomalies())
        }

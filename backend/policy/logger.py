from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel

class PolicyLogEntry(BaseModel):
    timestamp: str
    agent_id: str
    service_id: str
    action: str  # "ALLOWED", "REJECTED", "DOWNGRADED", "DENY"
    reason: str
    cost: Optional[float] = None
    risk_level: Optional[str] = "RISK_OK"  # "RISK_OK", "RISK_REVIEW", "RISK_BLOCK"
    
class TransactionLogEntry(BaseModel):
    timestamp: str
    agent_id: str
    service_id: str
    task_id: str
    amount: float
    tx_hash: Optional[str] = None
    status: str  # "SUCCESS", "FAILED", "MOCK"
    service_call_hash: Optional[str] = None  # Anti-spoofing hash

class SystemLogger:
    def __init__(self):
        self.policy_logs: List[PolicyLogEntry] = []
        self.transaction_logs: List[TransactionLogEntry] = []
        
    def log_policy_decision(self, agent_id: str, service_id: str, action: str, reason: str, cost: Optional[float] = None, risk_level: str = "RISK_OK"):
        entry = PolicyLogEntry(
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            service_id=service_id,
            action=action,
            reason=reason,
            cost=cost,
            risk_level=risk_level
        )
        self.policy_logs.append(entry)
        print(f"[POLICY LOG] {action} | Agent={agent_id} | Service={service_id} | Risk={risk_level} | Reason={reason}")
        
    def log_transaction(self, agent_id: str, service_id: str, task_id: str, amount: float, tx_hash: Optional[str] = None, status: str = "SUCCESS", service_call_hash: Optional[str] = None):
        entry = TransactionLogEntry(
            timestamp=datetime.now().isoformat(),
            agent_id=agent_id,
            service_id=service_id,
            task_id=task_id,
            amount=amount,
            tx_hash=tx_hash,
            status=status,
            service_call_hash=service_call_hash
        )
        self.transaction_logs.append(entry)
        print(f"[TRANSACTION LOG] {status} | Agent={agent_id} | Service={service_id} | Amount={amount} MNEE | ServiceCallHash={service_call_hash[:16] if service_call_hash else 'N/A'}...")
        
    def get_recent_policy_logs(self, limit: int = 50) -> List[Dict]:
        return [log.model_dump() for log in self.policy_logs[-limit:]]
        
    def get_recent_transactions(self, limit: int = 50) -> List[Dict]:
        return [log.model_dump() for log in self.transaction_logs[-limit:]]
        
    def get_agent_transactions(self, agent_id: str) -> List[Dict]:
        return [log.model_dump() for log in self.transaction_logs if log.agent_id == agent_id]
        
    def get_service_transactions(self, service_id: str) -> List[Dict]:
        return [log.model_dump() for log in self.transaction_logs if log.service_id == service_id]
        
    def get_total_spent_by_agent(self, agent_id: str) -> float:
        return sum(log.amount for log in self.transaction_logs 
                  if log.agent_id == agent_id and log.status == "SUCCESS")
        
    def get_total_revenue_by_service(self, service_id: str) -> float:
        return sum(log.amount for log in self.transaction_logs 
                  if log.service_id == service_id and log.status == "SUCCESS")

"""
Escrow Node - Implements the Escrow-Verify-Release Protocol

This node manages trustless transactions between Customer and Merchant agents:
1. Lock funds before task execution
2. Hold funds during execution
3. Release/refund based on verification results

The escrow mechanism solves the "Delivery vs Payment" trust deadlock in
decentralized Agent networks.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from ..state import GraphState, EscrowRecord, PlanStep


class EscrowManager:
    """
    Manages escrow transactions for the Agent labor market.
    
    In production, this would interact with a smart contract.
    For the hackathon MVP, we simulate the escrow logic in Python
    while maintaining the same state transitions.
    """
    
    def __init__(self, a2a_client=None):
        self.a2a_client = a2a_client
        self.escrows: Dict[str, EscrowRecord] = {}
    
    def create_escrow(
        self,
        task_id: str,
        customer_agent: str,
        merchant_agent: str,
        amount: float,
        requirement_hash: Optional[str] = None
    ) -> EscrowRecord:
        """
        Create a new escrow and lock funds.
        
        This is called before task execution begins.
        The customer's funds are locked in the escrow contract.
        """
        escrow_id = f"ESC-{uuid.uuid4().hex[:8]}"
        
        # Calculate platform fee (1%)
        fee = amount * 0.01
        
        escrow = EscrowRecord(
            escrow_id=escrow_id,
            task_id=task_id,
            customer_agent=customer_agent,
            merchant_agent=merchant_agent,
            amount=amount,
            fee=fee,
            status="created",
            created_at=datetime.now().isoformat(),
            requirement_hash=requirement_hash
        )
        
        # Attempt to lock funds on-chain
        if self.a2a_client:
            try:
                result = self.a2a_client.execute_a2a_payment(
                    from_agent=customer_agent,
                    to_agent="escrow-contract",  # Funds go to escrow, not merchant
                    amount=amount,
                    task_description=f"Escrow lock for task {task_id}"
                )
                escrow.lock_tx_hash = result.get("tx_hash")
                print(f"    [ESCROW] Funds locked: {amount} MNEE (TX: {escrow.lock_tx_hash})")
            except Exception as e:
                print(f"    [ESCROW] Lock failed: {e}")
                escrow.status = "failed"
        else:
            # Simulated lock
            escrow.lock_tx_hash = f"0x{uuid.uuid4().hex}"
            print(f"    [ESCROW] Simulated lock: {amount} MNEE")
        
        self.escrows[escrow_id] = escrow
        return escrow
    
    def submit_work(
        self,
        escrow_id: str,
        work_ipfs_cid: Optional[str] = None,
        work_data: Optional[Dict[str, Any]] = None
    ) -> EscrowRecord:
        """
        Merchant submits completed work.
        
        The work evidence (IPFS CID or data hash) is recorded
        for verification.
        """
        escrow = self.escrows.get(escrow_id)
        if not escrow:
            raise ValueError(f"Escrow {escrow_id} not found")
        
        if escrow.status != "created":
            raise ValueError(f"Invalid status for submission: {escrow.status}")
        
        escrow.status = "submitted"
        escrow.submitted_at = datetime.now().isoformat()
        
        if work_ipfs_cid:
            escrow.work_ipfs_cid = work_ipfs_cid
        elif work_data:
            # Hash the work data as evidence
            import hashlib
            import json
            data_str = json.dumps(work_data, sort_keys=True)
            escrow.work_ipfs_cid = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        
        print(f"    [ESCROW] Work submitted for {escrow_id}")
        return escrow
    
    def verify_and_release(
        self,
        escrow_id: str,
        verification_score: float,
        passed: bool
    ) -> EscrowRecord:
        """
        Verify work and release/refund funds.
        
        This is the critical settlement step:
        - If verification passes: release funds to merchant
        - If verification fails: refund funds to customer
        """
        escrow = self.escrows.get(escrow_id)
        if not escrow:
            raise ValueError(f"Escrow {escrow_id} not found")
        
        if escrow.status not in ["submitted", "verifying"]:
            raise ValueError(f"Invalid status for verification: {escrow.status}")
        
        escrow.status = "verifying"
        escrow.verification_score = verification_score
        escrow.verification_passed = passed
        escrow.verified_at = datetime.now().isoformat()
        
        if passed:
            # Release funds to merchant
            escrow.status = "released"
            escrow.released_at = datetime.now().isoformat()
            
            if self.a2a_client:
                try:
                    # Transfer from escrow to merchant (minus fee)
                    payout = escrow.amount - escrow.fee
                    result = self.a2a_client.execute_a2a_payment(
                        from_agent="escrow-contract",
                        to_agent=escrow.merchant_agent,
                        amount=payout,
                        task_description=f"Escrow release for {escrow.task_id}"
                    )
                    escrow.release_tx_hash = result.get("tx_hash")
                    print(f"    [ESCROW] Released {payout} MNEE to {escrow.merchant_agent}")
                except Exception as e:
                    print(f"    [ESCROW] Release failed: {e}")
            else:
                escrow.release_tx_hash = f"0x{uuid.uuid4().hex}"
                print(f"    [ESCROW] Simulated release to {escrow.merchant_agent}")
        else:
            # Refund to customer
            escrow.status = "refunded"
            
            if self.a2a_client:
                try:
                    result = self.a2a_client.execute_a2a_payment(
                        from_agent="escrow-contract",
                        to_agent=escrow.customer_agent,
                        amount=escrow.amount,
                        task_description=f"Escrow refund for {escrow.task_id}"
                    )
                    escrow.release_tx_hash = result.get("tx_hash")
                    print(f"    [ESCROW] Refunded {escrow.amount} MNEE to {escrow.customer_agent}")
                except Exception as e:
                    print(f"    [ESCROW] Refund failed: {e}")
            else:
                escrow.release_tx_hash = f"0x{uuid.uuid4().hex}"
                print(f"    [ESCROW] Simulated refund to {escrow.customer_agent}")
        
        return escrow
    
    def raise_dispute(self, escrow_id: str, reason: str) -> EscrowRecord:
        """
        Raise a dispute for manual/oracle resolution.
        
        This freezes the escrow until the dispute is resolved
        by a third party (AI verifier network or human arbitration).
        """
        escrow = self.escrows.get(escrow_id)
        if not escrow:
            raise ValueError(f"Escrow {escrow_id} not found")
        
        escrow.status = "disputed"
        escrow.dispute_reason = reason
        print(f"    [ESCROW] Dispute raised for {escrow_id}: {reason}")
        return escrow
    
    def resolve_dispute(
        self,
        escrow_id: str,
        resolution: str,
        release_to_merchant: bool
    ) -> EscrowRecord:
        """
        Resolve a dispute and settle funds.
        
        In production, this would be called by:
        - AI Verifier Network (Autonolas Mech)
        - UMA Optimistic Oracle
        - Human arbitration panel
        """
        escrow = self.escrows.get(escrow_id)
        if not escrow or escrow.status != "disputed":
            raise ValueError(f"Invalid escrow or status for resolution")
        
        escrow.dispute_resolution = resolution
        
        if release_to_merchant:
            escrow.status = "released"
            print(f"    [ESCROW] Dispute resolved: Release to merchant")
        else:
            escrow.status = "refunded"
            print(f"    [ESCROW] Dispute resolved: Refund to customer")
        
        return escrow
    
    def get_escrow(self, escrow_id: str) -> Optional[EscrowRecord]:
        return self.escrows.get(escrow_id)


# Singleton instance
_escrow_manager: Optional[EscrowManager] = None


def get_escrow_manager(a2a_client=None) -> EscrowManager:
    global _escrow_manager
    if _escrow_manager is None:
        _escrow_manager = EscrowManager(a2a_client)
    return _escrow_manager


def escrow_lock_node(state: GraphState, escrow_manager: EscrowManager = None) -> GraphState:
    """
    LangGraph node: Lock funds in escrow before execution.
    
    This node runs after Guardian approval and before Executor.
    It creates escrow records for each step that involves payment.
    """
    print(f"\n[ESCROW_LOCK_NODE] Locking funds for {len(state.plan)} steps")
    
    if escrow_manager is None:
        escrow_manager = get_escrow_manager()
    
    for step in state.plan:
        if step.max_mnee_cost > 0:
            escrow = escrow_manager.create_escrow(
                task_id=state.task_id,
                customer_agent=state.active_agent,
                merchant_agent=step.agent_id,
                amount=step.max_mnee_cost,
                requirement_hash=step.description
            )
            
            state.escrow_records.append(escrow)
            print(f"  > Created escrow {escrow.escrow_id}: {escrow.amount} MNEE")
    
    return state


def escrow_release_node(state: GraphState, escrow_manager: EscrowManager = None) -> GraphState:
    """
    LangGraph node: Release or refund escrow based on execution results.
    
    This node runs after Verifier and before Summarizer.
    It settles all escrow transactions based on verification outcomes.
    """
    print(f"\n[ESCROW_RELEASE_NODE] Settling {len(state.escrow_records)} escrows")
    
    if escrow_manager is None:
        escrow_manager = get_escrow_manager()
    
    # Match escrows to step results
    for escrow in state.escrow_records:
        if escrow.status in ["released", "refunded"]:
            continue  # Already settled
        
        # Find matching step result
        matching_step = None
        for step in state.steps:
            if step.agent_id == escrow.merchant_agent:
                matching_step = step
                break
        
        if matching_step:
            # Determine verification outcome
            if matching_step.status == "success":
                verification_score = 1.0
                passed = True
            elif matching_step.status == "failed":
                verification_score = 0.0
                passed = False
            else:
                verification_score = 0.5
                passed = False
            
            # Submit work evidence
            if matching_step.output:
                escrow_manager.submit_work(
                    escrow.escrow_id,
                    work_data=matching_step.output
                )
            
            # Verify and release/refund
            updated_escrow = escrow_manager.verify_and_release(
                escrow.escrow_id,
                verification_score,
                passed
            )
            
            # Update the escrow record in state
            escrow.status = updated_escrow.status
            escrow.verification_score = updated_escrow.verification_score
            escrow.verification_passed = updated_escrow.verification_passed
            escrow.release_tx_hash = updated_escrow.release_tx_hash
            
            print(f"  > Settled escrow {escrow.escrow_id}: {escrow.status}")
    
    return state

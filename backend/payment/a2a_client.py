"""
A2A (Agent-to-Agent) Payment Client

Handles real on-chain payments between agents using MNEEAgentWallet contract.
"""

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from web3 import Web3
from eth_account import Account

# Load contract ABI
ABI_PATH = os.path.join(os.path.dirname(__file__), "abi", "MNEEAgentWallet.json")

@dataclass
class A2ATransfer:
    """Record of an A2A payment"""
    transfer_id: int
    from_agent: str
    to_agent: str
    amount: float
    task_description: str
    tx_hash: str
    timestamp: datetime


class A2APaymentClient:
    """
    Client for Agent-to-Agent payments via MNEEAgentWallet contract.
    
    Features:
    - Execute A2A payments on-chain
    - Query agent balances
    - Get transfer history for visualization
    """
    
    def __init__(self):
        self.rpc_url = os.getenv("ETH_RPC_URL", "http://127.0.0.1:8545")
        self.wallet_address = os.getenv("AGENT_WALLET_ADDRESS", "")
        self.private_key = os.getenv("TREASURY_PRIVATE_KEY", "")
        
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Load ABI
        self.abi = self._load_abi()
        
        if self.wallet_address and self.abi:
            self.contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(self.wallet_address),
                abi=self.abi
            )
        else:
            self.contract = None
            print("[A2A_CLIENT] Warning: AgentWallet contract not configured")
        
        # Local cache of transfers for quick access
        self.transfer_cache: List[A2ATransfer] = []
    
    def _load_abi(self) -> list:
        """Load contract ABI from file or use embedded"""
        if os.path.exists(ABI_PATH):
            with open(ABI_PATH) as f:
                return json.load(f)
        
        # Embedded minimal ABI for core functions
        return [
            {
                "inputs": [
                    {"name": "fromAgentId", "type": "string"},
                    {"name": "toAgentId", "type": "string"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "taskDescription", "type": "string"}
                ],
                "name": "a2aPayment",
                "outputs": [{"name": "transferId", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [{"name": "agentId", "type": "string"}],
                "name": "getAgentBalance",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"name": "agentId", "type": "string"}],
                "name": "getAgentInfo",
                "outputs": [
                    {"name": "registered", "type": "bool"},
                    {"name": "name", "type": "string"},
                    {"name": "balance", "type": "uint256"},
                    {"name": "totalReceived", "type": "uint256"},
                    {"name": "totalSpent", "type": "uint256"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getTransferCount",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
    
    def execute_a2a_payment(
        self,
        from_agent: str,
        to_agent: str,
        amount: float,
        task_description: str
    ) -> Dict[str, Any]:
        """
        Execute an A2A payment on-chain.
        
        Args:
            from_agent: Agent ID paying for the task
            to_agent: Agent ID receiving payment
            amount: Amount in MNEE
            task_description: Description of the delegated task
            
        Returns:
            Dict with tx_hash, transfer_id, success status
        """
        if not self.contract:
            return {"success": False, "error": "Contract not configured"}
        
        try:
            # Convert amount to wei (18 decimals)
            amount_wei = self.web3.to_wei(amount, 'ether')
            
            # Get account from private key
            account = Account.from_key(self.private_key)
            
            # Build transaction
            tx = self.contract.functions.a2aPayment(
                from_agent,
                to_agent,
                amount_wei,
                task_description
            ).build_transaction({
                'from': account.address,
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'gas': 200000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            # Sign and send
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash_hex = self.web3.to_hex(tx_hash)
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Parse transfer ID from logs (simplified)
            transfer_id = self.get_transfer_count() - 1
            
            # Cache the transfer
            transfer = A2ATransfer(
                transfer_id=transfer_id,
                from_agent=from_agent,
                to_agent=to_agent,
                amount=amount,
                task_description=task_description,
                tx_hash=tx_hash_hex,
                timestamp=datetime.now()
            )
            self.transfer_cache.append(transfer)
            
            print(f"[A2A_CLIENT] Payment successful: {from_agent} -> {to_agent} ({amount} MNEE)")
            print(f"[A2A_CLIENT] TX: {tx_hash_hex}")
            
            return {
                "success": True,
                "tx_hash": tx_hash_hex,
                "transfer_id": transfer_id,
                "from_agent": from_agent,
                "to_agent": to_agent,
                "amount": amount
            }
            
        except Exception as e:
            print(f"[A2A_CLIENT] Payment failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_agent_balance(self, agent_id: str) -> float:
        """Get agent's MNEE balance"""
        if not self.contract:
            return 0.0
        
        try:
            balance_wei = self.contract.functions.getAgentBalance(agent_id).call()
            return float(self.web3.from_wei(balance_wei, 'ether'))
        except Exception as e:
            print(f"[A2A_CLIENT] Error getting balance: {e}")
            return 0.0
    
    def get_agent_info(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed agent info from contract"""
        if not self.contract:
            return {}
        
        try:
            result = self.contract.functions.getAgentInfo(agent_id).call()
            return {
                "registered": result[0],
                "name": result[1],
                "balance": float(self.web3.from_wei(result[2], 'ether')),
                "total_received": float(self.web3.from_wei(result[3], 'ether')),
                "total_spent": float(self.web3.from_wei(result[4], 'ether'))
            }
        except Exception as e:
            print(f"[A2A_CLIENT] Error getting agent info: {e}")
            return {}
    
    def get_transfer_count(self) -> int:
        """Get total number of A2A transfers"""
        if not self.contract:
            return 0
        
        try:
            return self.contract.functions.getTransferCount().call()
        except:
            return len(self.transfer_cache)
    
    def get_recent_transfers(self, count: int = 20) -> List[Dict[str, Any]]:
        """Get recent A2A transfers for visualization"""
        # Return from cache (most recent first)
        transfers = self.transfer_cache[-count:][::-1]
        
        return [
            {
                "transfer_id": t.transfer_id,
                "from_agent": t.from_agent,
                "to_agent": t.to_agent,
                "amount": t.amount,
                "task_description": t.task_description,
                "tx_hash": t.tx_hash,
                "timestamp": t.timestamp.isoformat()
            }
            for t in transfers
        ]
    
    def get_all_agent_balances(self) -> Dict[str, float]:
        """Get balances for all known agents"""
        agents = ["user-agent", "startup-designer", "startup-analyst", "startup-archivist"]
        return {agent: self.get_agent_balance(agent) for agent in agents}


# Global instance
_a2a_client: Optional[A2APaymentClient] = None

def get_a2a_client() -> A2APaymentClient:
    """Get or create the global A2A client instance"""
    global _a2a_client
    if _a2a_client is None:
        _a2a_client = A2APaymentClient()
    return _a2a_client

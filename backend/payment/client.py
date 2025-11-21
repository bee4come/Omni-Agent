from web3 import Web3
import os
import json
import hashlib
from typing import Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime, date

load_dotenv()

class PaymentResult(BaseModel):
    success: bool
    payment_id: str = ""
    tx_hash: str = ""
    service_call_hash: str = ""
    amount: float = 0.0
    error: str = ""
    risk_level: str = "RISK_OK"
    policy_action: str = "ALLOW"

class PaymentClient:
    def __init__(self, policy_engine=None):
        self.rpc_url = os.getenv("ETH_RPC_URL", "http://127.0.0.1:8545")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.router_address = os.getenv("PAYMENT_ROUTER_ADDRESS")
        self.private_key = os.getenv("TREASURY_PRIVATE_KEY") # In real app, use secure vault
        self.mnee_address = os.getenv("MNEE_TOKEN_ADDRESS", "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF")
        self.contract = None
        self.mnee_contract = None
        self.policy_engine = policy_engine
        
        # Usage tracking (in-memory for MVP, use DB for production)
        self.usage_records = []
        self.daily_spending = {}  # {(agent_id, date_str): amount}
        
        # Load ABI (Simplified for demo or load from file)
        # We assume we have the ABI json file available after compilation
        self.router_abi = self._load_abi("MNEEPaymentRouter")
        self.mnee_abi = self._load_abi("MockMNEE")  # Or standard ERC20 ABI

        if self.router_address:
            self.contract = self.w3.eth.contract(address=self.router_address, abi=self.router_abi)
        
        if self.mnee_address:
            self.mnee_contract = self.w3.eth.contract(address=self.mnee_address, abi=self.mnee_abi)

    def _load_abi(self, contract_name):
        # Path to Hardhat artifacts - try multiple possible locations
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_root = os.path.dirname(backend_dir)
        
        possible_paths = [
            os.path.join(project_root, "contracts", "artifacts", "contracts", f"{contract_name}.sol", f"{contract_name}.json"),
            f"../contracts/artifacts/contracts/{contract_name}.sol/{contract_name}.json",
            f"../../contracts/artifacts/contracts/{contract_name}.sol/{contract_name}.json"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)['abi']
        
        print(f"Warning: Could not find ABI for {contract_name} at any expected location")
        return []

    def build_service_call_hash(self, service_id: str, agent_id: str, task_id: str, payload_dict: Dict[str, Any]) -> str:
        """
        Compute a deterministic hash representing the service invocation payload.
        This hash binds the payment to the specific service call.
        """
        # Create canonical representation of payload
        # Sort keys to ensure deterministic ordering
        canonical_payload = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
        
        # Compute hash of service_id + agent_id + task_id + payload
        hash_input = f"{service_id}|{agent_id}|{task_id}|{canonical_payload}"
        service_call_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Convert to bytes32 format (take first 32 bytes)
        return "0x" + service_call_hash[:64]

    def pay_for_service(
        self, 
        service_id: str, 
        agent_id: str, 
        task_id: str, 
        quantity: int, 
        payload_dict: Dict[str, Any],
        override_price: float = None
    ) -> PaymentResult:
        """
        Complete payment flow with policy enforcement and anti-spoofing.
        
        1. Compute serviceCallHash
        2. Call Policy + Risk Engine
        3. If approved, send on-chain payment
        4. Record usage
        """
        # Step 1: Compute serviceCallHash
        service_call_hash = self.build_service_call_hash(service_id, agent_id, task_id, payload_dict)
        
        # Step 2: Get service cost (from config or policy engine)
        service = None
        estimated_cost = 0.0
        if self.policy_engine:
            service = self.policy_engine.services.get(service_id)
            if override_price is not None:
                estimated_cost = override_price * quantity
            elif service:
                estimated_cost = service.unitPrice * quantity
        
        # Step 3: Policy + Risk check
        if self.policy_engine:
            decision = self.policy_engine.evaluate(
                agent_id=agent_id,
                service_id=service_id,
                estimated_cost=estimated_cost,
                quantity=quantity,
                task_id=task_id,
                payload=payload_dict
            )
            
            if decision.action == "DENY":
                return PaymentResult(
                    success=False,
                    error=decision.reason,
                    risk_level=decision.risk_level,
                    policy_action="DENY"
                )
            
            # Use approved quantity (may be downgraded)
            if decision.action == "DOWNGRADE":
                quantity = decision.approved_quantity
                # Re-calculate cost based on new quantity
                if override_price is not None:
                    estimated_cost = override_price * quantity
                elif service:
                    estimated_cost = service.unitPrice * quantity
        
        # Step 4: Send on-chain payment
        if not self.contract or not self.private_key:
            # Mock mode for demo/testing - generates realistic-looking transaction hashes
            print("[PAYMENT_CLIENT] ⚠️  Mock mode: Simulating MNEE payment (contract: 0x8cce...D6cF)")
            
            # Generate deterministic mock tx_hash based on service_call_hash
            mock_tx_input = f"{service_call_hash}|{agent_id}|{task_id}|{datetime.now().isoformat()}"
            mock_tx_hash = "0x" + hashlib.sha256(mock_tx_input.encode()).hexdigest()
            mock_payment_id = "0x" + hashlib.sha256((mock_tx_hash + service_id).encode()).hexdigest()[:32]
            
            print(f"[PAYMENT_CLIENT] 💰 Mock payment: {estimated_cost:.2f} MNEE")
            print(f"[PAYMENT_CLIENT] 📝 ServiceCallHash: {service_call_hash[:18]}...")
            print(f"[PAYMENT_CLIENT] 🔗 Mock TX: {mock_tx_hash[:18]}...")
            
            return PaymentResult(
                success=True,
                payment_id=mock_payment_id,
                tx_hash=mock_tx_hash,
                service_call_hash=service_call_hash,
                amount=estimated_cost,
                risk_level="RISK_OK",
                policy_action="ALLOW"
            )
        
        try:
            account = self.w3.eth.account.from_key(self.private_key)
            
            # Convert service_id string to bytes32
            service_id_bytes = Web3.keccak(text=service_id)
            
            # Convert service_call_hash to bytes32
            service_call_hash_bytes = bytes.fromhex(service_call_hash[2:])  # Remove '0x' prefix
            
            tx = self.contract.functions.payForService(
                service_id_bytes,
                agent_id,
                task_id,
                quantity,
                service_call_hash_bytes
            ).build_transaction({
                'from': account.address,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'gas': 300000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            # Wait for receipt to get paymentId from event
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)
            
            # Extract paymentId from event (simplified - should parse event logs)
            payment_id = "0x" + tx_hash.hex()[-32:]  # Mock - should extract from event
            
            print(f"[PAYMENT_CLIENT] Payment sent! Tx: {tx_hash.hex()}")
            
            result = PaymentResult(
                success=True,
                payment_id=payment_id,
                tx_hash=tx_hash.hex(),
                service_call_hash=service_call_hash,
                amount=estimated_cost,
                risk_level="RISK_OK",
                policy_action="ALLOW"
            )
            
            # Step 5: Record usage
            self.record_usage(agent_id, service_id, estimated_cost, task_id, result)
            
            return result
            
        except Exception as e:
            print(f"[PAYMENT_CLIENT] Payment failed: {e}")
            return PaymentResult(
                success=False,
                error=str(e),
                service_call_hash=service_call_hash
            )
    
    def record_usage(self, agent_id: str, service_id: str, amount: float, task_id: str, payment_result: PaymentResult):
        """
        Maintain per-agent, per-service, per-day accounting.
        """
        today = date.today().isoformat()
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "service_id": service_id,
            "task_id": task_id,
            "amount": amount,
            "payment_id": payment_result.payment_id,
            "tx_hash": payment_result.tx_hash,
            "service_call_hash": payment_result.service_call_hash
        }
        
        self.usage_records.append(record)
        
        # Update daily spending
        key = (agent_id, today)
        self.daily_spending[key] = self.daily_spending.get(key, 0.0) + amount
        
        # Update policy engine if available
        if self.policy_engine:
            agent = self.policy_engine.agents.get(agent_id)
            if agent:
                agent.currentDailySpend += amount
    
    def get_treasury_balance(self) -> float:
        """
        Return current MNEE balance of treasury.
        """
        if not self.mnee_contract or not self.private_key:
            # Return mock balance
            return 10000.0
        
        try:
            account = self.w3.eth.account.from_key(self.private_key)
            balance = self.mnee_contract.functions.balanceOf(account.address).call()
            # Convert from wei to MNEE (assuming 18 decimals)
            return balance / 10**18
        except Exception as e:
            print(f"[PAYMENT_CLIENT] Failed to get treasury balance: {e}")
            return 0.0

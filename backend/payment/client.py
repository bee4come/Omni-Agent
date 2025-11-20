from web3 import Web3
import os
import json
from dotenv import load_dotenv

load_dotenv()

class PaymentClient:
    def __init__(self):
        self.rpc_url = os.getenv("ETH_RPC_URL", "http://127.0.0.1:8545")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.router_address = os.getenv("PAYMENT_ROUTER_ADDRESS")
        self.private_key = os.getenv("TREASURY_PRIVATE_KEY") # In real app, use secure vault
        self.contract = None
        
        # Load ABI (Simplified for demo or load from file)
        # We assume we have the ABI json file available after compilation
        self.router_abi = self._load_abi("MNEEPaymentRouter")

        if self.router_address:
            self.contract = self.w3.eth.contract(address=self.router_address, abi=self.router_abi)

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

    def pay_for_service(self, service_id: str, agent_id: str, task_id: str, quantity: int = 1):
        if not self.contract or not self.private_key:
            print("Warning: Payment Client not fully configured (missing address or key). Skipping on-chain payment.")
            return "0xMOCK_TX_HASH"

        account = self.w3.eth.account.from_key(self.private_key)
        
        # Convert service_id string to bytes32
        service_id_bytes = Web3.keccak(text=service_id)

        tx = self.contract.functions.payForService(
            service_id_bytes,
            agent_id,
            task_id,
            quantity
        ).build_transaction({
            'from': account.address,
            'nonce': self.w3.eth.get_transaction_count(account.address),
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        print(f"Payment sent! Tx: {tx_hash.hex()}")
        return tx_hash.hex()

import os
import json
from typing import List, Dict, Any
from web3 import Web3
from eth_account import Account

class TransferResponse:
    def __init__(self, ticketId: str, rawtx: str = None):
        self.ticketId = ticketId
        self.rawtx = rawtx

class Mnee:
    """
    Python Wrapper for MNEE Payment Router interaction via Web3.
    """
    def __init__(self, config: Dict[str, str]):
        self.rpc_url = os.getenv("ETH_RPC_URL", "http://127.0.0.1:8545")
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        self.router_address = os.getenv("PAYMENT_ROUTER_ADDRESS")
        self.token_address = os.getenv("MNEE_TOKEN_ADDRESS")
        
        # Standard ERC20 ABI
        self.token_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]

        # MNEEPaymentRouter ABI (Simplified to essential functions)
        self.router_abi = [
            {
                "inputs": [
                    {"internalType": "bytes32", "name": "serviceId", "type": "bytes32"},
                    {"internalType": "string", "name": "agentId", "type": "string"},
                    {"internalType": "string", "name": "taskId", "type": "string"},
                    {"internalType": "uint256", "name": "quantity", "type": "uint256"},
                    {"internalType": "bytes32", "name": "serviceCallHash", "type": "bytes32"}
                ],
                "name": "payForService",
                "outputs": [{"internalType": "bytes32", "name": "paymentId", "type": "bytes32"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
             {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "internalType": "bytes32", "name": "paymentId", "type": "bytes32"},
                    {"indexed": True, "internalType": "address", "name": "payer", "type": "address"},
                    {"indexed": True, "internalType": "address", "name": "provider", "type": "address"},
                    {"indexed": False, "internalType": "bytes32", "name": "serviceId", "type": "bytes32"},
                    {"indexed": False, "internalType": "string", "name": "agentId", "type": "string"},
                    {"indexed": False, "internalType": "string", "name": "taskId", "type": "string"},
                    {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
                    {"indexed": False, "internalType": "uint256", "name": "quantity", "type": "uint256"},
                    {"indexed": False, "internalType": "bytes32", "name": "serviceCallHash", "type": "bytes32"},
                    {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
                ],
                "name": "PaymentExecuted",
                "type": "event"
            }
        ]

        if self.token_address:
            self.token_address = Web3.to_checksum_address(self.token_address)
            self.token = self.web3.eth.contract(address=self.token_address, abi=self.token_abi)
        
        if self.router_address:
            self.router_address = Web3.to_checksum_address(self.router_address)
            self.router = self.web3.eth.contract(address=self.router_address, abi=self.router_abi)

    def balance(self, address: str) -> Dict[str, Any]:
        if not self.token:
            return {"address": address, "amount": 0, "decimalAmount": 0.0}
        
        checksum_address = Web3.to_checksum_address(address)
        raw_balance = self.token.functions.balanceOf(checksum_address).call()
        return {
            "address": address,
            "amount": raw_balance,
            "decimalAmount": raw_balance / 1e18
        }

    def ensure_approval(self, owner_private_key: str, amount_wei: int = 2**256 - 1):
        """
        Ensures the router is approved to spend tokens.
        """
        if not self.token or not self.router_address:
            print("Warning: Token or Router address not set. Skipping approval.")
            return

        account = Account.from_key(owner_private_key)
        owner_address = account.address

        current_allowance = self.token.functions.allowance(owner_address, self.router_address).call()
        
        if current_allowance < amount_wei:
            print(f"Approving Router ({self.router_address}) to spend {amount_wei}...")
            nonce = self.web3.eth.get_transaction_count(owner_address)
            
            tx = self.token.functions.approve(self.router_address, amount_wei).build_transaction({
                'from': owner_address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': self.web3.eth.gas_price
            })
            
            signed_tx = self.web3.eth.account.sign_transaction(tx, owner_private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            self.web3.eth.wait_for_transaction_receipt(tx_hash)
            print("Approval successful.")

    def pay_for_service(
        self, 
        service_id: str, 
        agent_id: str, 
        task_id: str, 
        quantity: int, 
        service_call_hash: str, 
        private_key: str
    ) -> TransferResponse:
        
        if not self.router:
            raise Exception("Payment Router not configured.")

        account = Account.from_key(private_key)
        payer_address = account.address

        # Convert service_id to bytes32 if it's a string
        if isinstance(service_id, str):
            service_id_bytes = Web3.keccak(text=service_id)
        else:
            service_id_bytes = service_id

        # Convert service_call_hash to bytes32
        if isinstance(service_call_hash, str):
            # Assuming it's a hex string from SHA256
            if service_call_hash.startswith("0x"):
                service_call_hash_bytes = bytes.fromhex(service_call_hash[2:])
            else:
                service_call_hash_bytes = bytes.fromhex(service_call_hash)
        else:
            service_call_hash_bytes = service_call_hash

        print(f"Executing payForService on Router: {self.router_address}")
        
        nonce = self.web3.eth.get_transaction_count(payer_address)
        
        # Estimate gas? Or use safe default.
        tx = self.router.functions.payForService(
            service_id_bytes,
            agent_id,
            task_id,
            quantity,
            service_call_hash_bytes
        ).build_transaction({
            'from': payer_address,
            'nonce': nonce,
            'gas': 500000, # Should be sufficient
            'gasPrice': self.web3.eth.gas_price
        })

        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
        tx_hash_bytes = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash = self.web3.to_hex(tx_hash_bytes)
        
        print(f"Transaction sent: {tx_hash}")
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Find PaymentExecuted event to get paymentId
        # (Simplified: just returning tx hash as ticketId for now, 
        # but ideally we parse the logs)
        
        payment_id = tx_hash # Fallback
        
        # Try to parse logs
        try:
            logs = self.router.events.PaymentExecuted().process_receipt(receipt)
            if logs:
                payment_id = self.web3.to_hex(logs[0]['args']['paymentId'])
        except Exception as e:
            print(f"Error parsing logs: {e}")

        return TransferResponse(ticketId=payment_id, rawtx=tx_hash)
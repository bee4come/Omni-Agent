import uuid
import time
import json
from typing import List, Dict, Any, Optional, Union

# Mock Data Structures based on SDK Docs

class MNEEUtxo:
    def __init__(self, txid: str, vout: int, satoshis: int, script: str, address: str):
        self.txid = txid
        self.vout = vout
        self.outpoint = f"{txid}_{vout}"
        self.satoshis = satoshis
        self.accSats = satoshis
        self.script = script
        self.owners = [address]
        self.data = {}  # Can hold serviceCallHash here

class TransferResponse:
    def __init__(self, ticketId: str, rawtx: Optional[str] = None):
        self.ticketId = ticketId
        self.rawtx = rawtx

class Mnee:
    """
    Python Mock implementation of the @mnee/ts-sdk
    Simulates a UTXO-based ledger in memory.
    Synchronous version for compatibility with existing backend.
    """
    def __init__(self, config: Dict[str, str]):
        self.environment = config.get('environment', 'sandbox')
        self.api_key = config.get('apiKey')
        
        # 1 MNEE = 100,000 atomic units
        self.ATOMIC_UNIT_FACTOR = 100000
        
        # In-memory Ledger: { address: [MNEEUtxo] }
        self.utxo_set: Dict[str, List[MNEEUtxo]] = {}
        self.transaction_history = []
        
        # Initialize Treasury with funds (e.g., 1,000,000 MNEE)
        self._mint("treasury-wallet-address", 1_000_000.0)

    def toAtomicAmount(self, amount: float) -> int:
        return int(amount * self.ATOMIC_UNIT_FACTOR)

    def fromAtomicAmount(self, amount: int) -> float:
        return amount / self.ATOMIC_UNIT_FACTOR

    def _mint(self, address: str, amount_mnee: float):
        """Internal helper to fund an address"""
        if address not in self.utxo_set:
            self.utxo_set[address] = []
            
        atomic_amount = self.toAtomicAmount(amount_mnee)
        txid = uuid.uuid4().hex
        
        utxo = MNEEUtxo(
            txid=txid,
            vout=0,
            satoshis=atomic_amount,
            script="mock-script-mint",
            address=address
        )
        self.utxo_set[address].append(utxo)

    def config(self):
        return {
            "approver": "mock-approver-key",
            "feeAddress": "mock-fee-address",
            "burnAddress": "mock-burn-address",
            "mintAddress": "mock-mint-address",
            "fees": [{"min": 0, "max": 999999999, "fee": 100}] # 100 atomic units fee
        }

    def balance(self, address: str):
        utxos = self.utxo_set.get(address, [])
        total_atomic = sum(u.satoshis for u in utxos)
        
        return {
            "address": address,
            "amount": total_atomic,
            "decimalAmount": self.fromAtomicAmount(total_atomic)
        }

    def getUtxos(self, address: str):
        return self.utxo_set.get(address, [])

    def transfer(self, recipients: List[Dict[str, Any]], wif: str, options: Dict[str, Any] = None) -> TransferResponse:
        """
        Simulates a transfer:
        1. Identifies sender from WIF (Mock: WIF acts as the sender ID for simplicity)
        2. Selects UTXOs
        3. Creates new UTXOs for recipients
        4. Creates change UTXO
        """
        sender_address = "treasury-wallet-address" # In mock, we assume WIF unlocks the treasury
        
        if sender_address not in self.utxo_set:
            raise Exception("Insufficient funds: Sender has no UTXOs")
            
        # Calculate total needed
        total_out_atomic = 0
        for r in recipients:
            total_out_atomic += self.toAtomicAmount(r['amount'])
            
        # Select UTXOs (Simple FIFO)
        inputs = []
        input_sum = 0
        sender_utxos = self.utxo_set[sender_address]
        
        remaining_utxos = []
        
        for utxo in sender_utxos:
            if input_sum < total_out_atomic:
                inputs.append(utxo)
                input_sum += utxo.satoshis
            else:
                remaining_utxos.append(utxo)
        
        if input_sum < total_out_atomic:
             raise Exception(f"Insufficient funds. Have {self.fromAtomicAmount(input_sum)}, need {self.fromAtomicAmount(total_out_atomic)}")

        # Execute Transfer (Update Ledger)
        txid = uuid.uuid4().hex
        
        # 1. Remove consumed UTXOs
        # (We effectively reconstruct the sender's UTXO set with only the remaining ones)
        self.utxo_set[sender_address] = remaining_utxos
        
        # 2. Create Output UTXOs
        vout_counter = 0
        
        # Recipients
        for r in recipients:
            r_addr = r['address']
            r_amt = self.toAtomicAmount(r['amount'])
            
            if r_addr not in self.utxo_set:
                self.utxo_set[r_addr] = []
                
            new_utxo = MNEEUtxo(txid, vout_counter, r_amt, f"script-pub-key-{r_addr}", r_addr)
            
            self.utxo_set[r_addr].append(new_utxo)
            vout_counter += 1
            
        # Change
        change = input_sum - total_out_atomic
        if change > 0:
            change_utxo = MNEEUtxo(txid, vout_counter, change, f"script-pub-key-{sender_address}", sender_address)
            self.utxo_set[sender_address].append(change_utxo)
            
        # Log History
        self.transaction_history.append({
            "id": txid,
            "status": "SUCCESS",
            "sender": sender_address,
            "recipients": recipients,
            "timestamp": time.time()
        })
            
        return TransferResponse(ticketId=txid)

    def getTxStatus(self, ticketId: str):
        tx = next((t for t in self.transaction_history if t['id'] == ticketId), None)
        if tx:
            return {
                "id": ticketId,
                "tx_id": ticketId,
                "status": "SUCCESS",
                "action_requested": "transfer",
                "createdAt": tx['timestamp']
            }
        return {"status": "UNKNOWN"}
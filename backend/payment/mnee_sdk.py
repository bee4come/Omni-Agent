import subprocess
import json
import os
from typing import List, Dict, Any

class TransferResponse:
    def __init__(self, ticketId: str, rawtx: str = None):
        self.ticketId = ticketId
        self.rawtx = rawtx

class Mnee:
    """
    Python Wrapper for the Real @mnee/ts-sdk (via Node.js bridge).
    """
    def __init__(self, config: Dict[str, str]):
        self.environment = config.get('environment', 'sandbox')
        self.api_key = config.get('apiKey')
        
        # Resolve path to bridge.js
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.bridge_path = os.path.join(current_dir, "bridge.js")

    def _call_bridge(self, command: str, args: List[str]) -> Any:
        try:
            cmd = ["node", self.bridge_path, command] + args
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Bridge Error: {e.stderr}")
            raise Exception(f"SDK Bridge Failed: {e.stderr}")
        except json.JSONDecodeError:
             raise Exception(f"Invalid JSON from bridge: {result.stdout}")

    def balance(self, address: str):
        return self._call_bridge("balance", [address])

    def transfer(self, recipients: List[Dict[str, Any]], wif: str, options: Dict[str, Any] = None) -> TransferResponse:
        recipients_json = json.dumps(recipients)
        # We pass WIF to the bridge, though the bridge currently mocks the usage
        res = self._call_bridge("transfer", [recipients_json, wif])
        return TransferResponse(ticketId=res['ticketId'], rawtx=res.get('rawtx'))

    def config(self):
        return self._call_bridge("config", [])

    # Helper (kept in Python for convenience)
    def toAtomicAmount(self, amount: float) -> int:
        return int(amount * 100000)

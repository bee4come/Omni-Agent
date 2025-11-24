"""
Swarm Architecture - Multi-Agent Coordination

This module implements the Swarm pattern with specialized agents:
- Manager: Plans and decomposes user requests
- Customer: Executes purchases and manages payments
- Merchant: Provides services and quotes
- Treasurer: Records and audits all transactions
"""

from .manager_agent import ManagerAgent
from .customer_agent import CustomerAgent
from .merchant_agent import MerchantAgent
from .treasurer_agent import TreasurerAgent
from .orchestrator import SwarmOrchestrator

__all__ = [
    'ManagerAgent',
    'CustomerAgent',
    'MerchantAgent',
    'TreasurerAgent',
    'SwarmOrchestrator'
]

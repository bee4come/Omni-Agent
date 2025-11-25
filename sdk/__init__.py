"""
MNEE Nexus SDK - Easy Integration for AI Agents

This SDK provides a simple interface for integrating MNEE-based
payments into AI agent systems.

Quick Start:
    from sdk import MNEEAgent

    agent = MNEEAgent(
        agent_id="my-agent",
        config_path="config/agents.yaml"
    )

    result = agent.request_service("Generate an image")
"""

from .mnee_agent import MNEEAgent
from .payment_sdk import PaymentSDK
from .swarm_sdk import SwarmSDK

__version__ = "0.1.0"

__all__ = [
    'MNEEAgent',
    'PaymentSDK',
    'SwarmSDK',
]

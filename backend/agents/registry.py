"""
Agent Registry - Dynamic Agent Discovery and Capability Management

This module implements the AgentCard system for the decentralized Agent labor market.
Each Agent registers its capabilities, pricing, and reputation for discovery by customers.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import yaml
from pathlib import Path


class AgentCard(BaseModel):
    """
    Agent capability and pricing declaration.
    
    This is the core primitive for the Agent labor market - each Agent
    advertises what it can do, how much it costs, and its track record.
    """
    agent_id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., description="Human-readable agent name")
    description: str = Field("", description="Agent description and specialization")
    
    # Capabilities
    capabilities: List[str] = Field(
        default_factory=list,
        description="List of service capabilities (e.g., 'image_gen', 'price_oracle')"
    )
    
    # Pricing model
    pricing: Dict[str, float] = Field(
        default_factory=dict,
        description="Price per capability in MNEE (e.g., {'image_gen': 1.0})"
    )
    base_fee: float = Field(0.01, description="Minimum fee for any task")
    
    # Reputation metrics
    reputation_score: float = Field(0.0, ge=0.0, le=5.0, description="Average rating (0-5)")
    success_rate: float = Field(1.0, ge=0.0, le=1.0, description="Task success rate")
    total_tasks_completed: int = Field(0, ge=0, description="Total completed tasks")
    total_tasks_failed: int = Field(0, ge=0, description="Total failed tasks")
    total_earnings: float = Field(0.0, ge=0.0, description="Total MNEE earned")
    
    # Availability
    is_available: bool = Field(True, description="Whether agent is accepting tasks")
    max_concurrent_tasks: int = Field(5, description="Max parallel tasks")
    current_load: int = Field(0, description="Current active tasks")
    
    # Metadata
    registered_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    wallet_address: Optional[str] = None
    
    def can_handle(self, capability: str) -> bool:
        """Check if agent can handle a specific capability."""
        return capability in self.capabilities
    
    def get_price(self, capability: str, quantity: int = 1) -> float:
        """Get price for a capability."""
        base = self.pricing.get(capability, self.base_fee)
        return max(base * quantity, self.base_fee)
    
    def update_reputation(self, success: bool, rating: Optional[float] = None):
        """Update agent reputation after task completion."""
        if success:
            self.total_tasks_completed += 1
        else:
            self.total_tasks_failed += 1
        
        total = self.total_tasks_completed + self.total_tasks_failed
        self.success_rate = self.total_tasks_completed / max(total, 1)
        
        if rating is not None and 0 <= rating <= 5:
            # Weighted average with existing score
            if self.reputation_score == 0:
                self.reputation_score = rating
            else:
                weight = min(self.total_tasks_completed, 100) / 100
                self.reputation_score = (
                    self.reputation_score * weight + rating * (1 - weight)
                )
        
        self.last_active = datetime.now()


class Quote(BaseModel):
    """
    Price quote from a Merchant Agent for a task.
    Used in the RFQ (Request for Quote) auction process.
    """
    quote_id: str
    agent_id: str
    task_id: str
    price: float = Field(..., description="Quoted price in MNEE")
    estimated_time: int = Field(..., description="Estimated completion time in seconds")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Agent's confidence level")
    expires_at: datetime
    accepted: bool = False
    
    def is_valid(self) -> bool:
        return datetime.now() < self.expires_at and not self.accepted


class AgentRegistry:
    """
    Central registry for Agent discovery and management.
    
    In a fully decentralized system, this would be backed by a smart contract.
    For the hackathon MVP, we use an in-memory registry with YAML persistence.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.agents: Dict[str, AgentCard] = {}
        self.quotes: Dict[str, List[Quote]] = {}  # task_id -> quotes
        
        if config_path:
            self._load_from_config(config_path)
        else:
            self._load_default_agents()
    
    def _load_from_config(self, config_path: str):
        """Load agents from YAML configuration."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            for agent_id, data in config.get('agents', {}).items():
                card = AgentCard(
                    agent_id=agent_id,
                    name=data.get('name', agent_id),
                    description=data.get('description', ''),
                    capabilities=data.get('capabilities', []),
                    pricing=data.get('pricing', {}),
                    base_fee=data.get('base_fee', 0.01),
                    reputation_score=data.get('reputation_score', 4.0),
                    success_rate=data.get('success_rate', 0.95),
                    wallet_address=data.get('wallet_address'),
                    registered_at=datetime.now()
                )
                self.agents[agent_id] = card
                
        except Exception as e:
            print(f"[REGISTRY] Failed to load config: {e}")
            self._load_default_agents()
    
    def _load_default_agents(self):
        """Initialize with default agent cards."""
        default_agents = [
            AgentCard(
                agent_id="user-agent",
                name="User Agent",
                description="Primary user-facing agent that coordinates tasks",
                capabilities=["coordination", "task_routing"],
                pricing={"coordination": 0.01},
                reputation_score=5.0,
                success_rate=1.0,
                registered_at=datetime.now()
            ),
            AgentCard(
                agent_id="startup-designer",
                name="Designer Agent",
                description="Specializes in image generation and visual design",
                capabilities=["image_gen", "design", "logo_creation"],
                pricing={"image_gen": 1.0, "design": 2.0, "logo_creation": 3.0},
                reputation_score=4.5,
                success_rate=0.92,
                total_tasks_completed=150,
                registered_at=datetime.now()
            ),
            AgentCard(
                agent_id="startup-analyst",
                name="Analyst Agent",
                description="Market analysis, pricing intelligence, and data processing",
                capabilities=["price_oracle", "market_analysis", "batch_compute", "data_analysis"],
                pricing={"price_oracle": 0.05, "market_analysis": 0.5, "batch_compute": 3.0},
                reputation_score=4.8,
                success_rate=0.98,
                total_tasks_completed=320,
                registered_at=datetime.now()
            ),
            AgentCard(
                agent_id="startup-archivist",
                name="Archivist Agent",
                description="Data storage, logging, and record keeping",
                capabilities=["log_archive", "data_storage", "audit_trail"],
                pricing={"log_archive": 0.02, "data_storage": 0.1},
                reputation_score=4.9,
                success_rate=0.99,
                total_tasks_completed=500,
                registered_at=datetime.now()
            ),
        ]
        
        for agent in default_agents:
            self.agents[agent.agent_id] = agent
    
    def register(self, card: AgentCard) -> bool:
        """Register a new agent or update existing."""
        card.registered_at = datetime.now()
        self.agents[card.agent_id] = card
        print(f"[REGISTRY] Registered agent: {card.agent_id}")
        return True
    
    def unregister(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False
    
    def get(self, agent_id: str) -> Optional[AgentCard]:
        """Get agent card by ID."""
        return self.agents.get(agent_id)
    
    def find_by_capability(self, capability: str) -> List[AgentCard]:
        """Find all agents that can handle a specific capability."""
        return [
            agent for agent in self.agents.values()
            if agent.can_handle(capability) and agent.is_available
        ]
    
    def select_best_agent(
        self,
        capability: str,
        price_weight: float = 0.4,
        reputation_weight: float = 0.4,
        success_weight: float = 0.2
    ) -> Optional[AgentCard]:
        """
        Select the best agent for a capability based on weighted scoring.
        
        Implements a simple reverse auction selection:
        - Lower price is better
        - Higher reputation is better
        - Higher success rate is better
        """
        candidates = self.find_by_capability(capability)
        if not candidates:
            return None
        
        # Normalize and score
        max_price = max(c.get_price(capability) for c in candidates) or 1
        
        scored = []
        for agent in candidates:
            price = agent.get_price(capability)
            price_score = 1 - (price / max_price)  # Lower price = higher score
            reputation_score = agent.reputation_score / 5.0
            success_score = agent.success_rate
            
            total_score = (
                price_score * price_weight +
                reputation_score * reputation_weight +
                success_score * success_weight
            )
            scored.append((total_score, agent))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1] if scored else None
    
    def submit_quote(self, quote: Quote):
        """Submit a quote for a task (RFQ market)."""
        if quote.task_id not in self.quotes:
            self.quotes[quote.task_id] = []
        self.quotes[quote.task_id].append(quote)
    
    def get_quotes(self, task_id: str) -> List[Quote]:
        """Get all quotes for a task."""
        return [q for q in self.quotes.get(task_id, []) if q.is_valid()]
    
    def select_winning_quote(self, task_id: str) -> Optional[Quote]:
        """Select the best quote for a task."""
        quotes = self.get_quotes(task_id)
        if not quotes:
            return None
        
        # Score quotes: lower price + agent reputation
        scored = []
        for quote in quotes:
            agent = self.get(quote.agent_id)
            if not agent:
                continue
            
            # Utility function: balance price and quality
            price_factor = 1 / (quote.price + 0.01)
            reputation_factor = agent.reputation_score / 5.0
            time_factor = 1 / (quote.estimated_time + 1)
            
            score = price_factor * 0.5 + reputation_factor * 0.3 + time_factor * 0.2
            scored.append((score, quote))
        
        if not scored:
            return None
        
        scored.sort(key=lambda x: x[0], reverse=True)
        winning_quote = scored[0][1]
        winning_quote.accepted = True
        return winning_quote
    
    def update_agent_stats(self, agent_id: str, success: bool, rating: Optional[float] = None):
        """Update agent statistics after task completion."""
        agent = self.get(agent_id)
        if agent:
            agent.update_reputation(success, rating)
    
    def get_all_agents(self) -> List[AgentCard]:
        """Get all registered agents."""
        return list(self.agents.values())
    
    def get_market_stats(self) -> Dict[str, Any]:
        """Get overall market statistics."""
        agents = list(self.agents.values())
        return {
            "total_agents": len(agents),
            "available_agents": len([a for a in agents if a.is_available]),
            "total_tasks_completed": sum(a.total_tasks_completed for a in agents),
            "total_earnings": sum(a.total_earnings for a in agents),
            "avg_success_rate": sum(a.success_rate for a in agents) / len(agents) if agents else 0,
            "capabilities": list(set(cap for a in agents for cap in a.capabilities))
        }


# Singleton instance
_registry_instance: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get or create the singleton registry instance."""
    global _registry_instance
    if _registry_instance is None:
        # Try to load from config
        config_path = Path(__file__).parent.parent.parent / "config" / "agents_registry.yaml"
        if config_path.exists():
            _registry_instance = AgentRegistry(str(config_path))
        else:
            _registry_instance = AgentRegistry()
    return _registry_instance

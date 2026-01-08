# MNEE Nexus API Reference

Base URL: `http://localhost:8000`

---

## Table of Contents

- [Health & Status](#health--status)
- [Treasury](#treasury)
- [Agents](#agents)
- [Services](#services)
- [Transactions](#transactions)
- [Policy](#policy)
- [A2A Payments](#a2a-payments)
- [Escrow](#escrow)
- [Registry](#registry)
- [WebSocket](#websocket)

---

## Health & Status

### GET /
Root endpoint - health check.

**Response:**
```json
{
  "name": "MNEE Nexus / Omni-Agent",
  "version": "1.0.0",
  "status": "running"
}
```

---

## Treasury

### GET /treasury
Get overall treasury status.

**Response:**
```json
{
  "agents": {
    "user-agent": {
      "id": "user-agent",
      "priority": "HIGH",
      "dailyBudget": 100.0,
      "maxPerCall": 50.0,
      "currentDailySpend": 15.5,
      "remainingBudget": 84.5
    }
  },
  "totalAllocated": 205.0,
  "totalSpent": 25.5
}
```

### POST /reset
Reset all agents' daily spending to 0.

**Response:**
```json
{
  "message": "All agents' daily spending has been reset to 0"
}
```

---

## Agents

### GET /agents
List all configured agents.

**Response:**
```json
{
  "agents": [
    {
      "id": "user-agent",
      "priority": "HIGH",
      "dailyBudget": 100.0,
      "maxPerCall": 50.0,
      "currentDailySpend": 15.5
    }
  ]
}
```

### GET /agents/{agent_id}
Get detailed info about a specific agent.

**Response:**
```json
{
  "id": "user-agent",
  "priority": "HIGH",
  "dailyBudget": 100.0,
  "maxPerCall": 50.0,
  "currentDailySpend": 15.5,
  "remainingBudget": 84.5,
  "transactions": [...],
  "totalSpent": 150.0
}
```

### PUT /agents/{agent_id}/budget
Update an agent's budget configuration.

**Request:**
```json
{
  "daily_budget": 150.0,
  "max_per_call": 25.0
}
```

**Response:**
```json
{
  "message": "Budget updated successfully",
  "agent": {
    "id": "user-agent",
    "dailyBudget": 150.0,
    "maxPerCall": 25.0
  }
}
```

---

## Services

### GET /services
List all configured services.

**Response:**
```json
{
  "services": [
    {
      "id": "IMAGE_GEN_PREMIUM",
      "unitPrice": 1.0,
      "providerAddress": "0x...",
      "active": true,
      "isVerified": true,
      "metadataURI": "ipfs://..."
    }
  ]
}
```

### GET /services/{service_id}
Get detailed info about a specific service.

---

## Transactions

### GET /transactions
Get recent transaction history.

**Query Parameters:**
- `limit` (int, default: 50): Maximum number of transactions

**Response:**
```json
{
  "transactions": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "agent_id": "user-agent",
      "service_id": "IMAGE_GEN_PREMIUM",
      "task_id": "task-123",
      "amount": 1.0,
      "tx_hash": "0x...",
      "status": "SUCCESS",
      "service_call_hash": "abc123..."
    }
  ]
}
```

---

## Policy

### GET /policy/logs
Get recent policy decision logs.

**Query Parameters:**
- `limit` (int, default: 50): Maximum number of logs

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-15T10:30:00",
      "agent_id": "user-agent",
      "service_id": "IMAGE_GEN_PREMIUM",
      "action": "ALLOW",
      "reason": "Within budget",
      "cost": 1.0,
      "risk_level": "RISK_OK"
    }
  ]
}
```

### GET /stats
Get overall system statistics.

**Response:**
```json
{
  "transactions": {
    "total": 150,
    "successful": 145,
    "failed": 5
  },
  "policyActions": {
    "ALLOW": 145,
    "DENY": 10
  },
  "totalAllocatedBudget": 205.0,
  "totalSpent": 75.5,
  "serviceCount": 4,
  "agentCount": 4
}
```

---

## A2A Payments

### POST /a2a/pay
Execute an Agent-to-Agent payment.

**Request:**
```json
{
  "from_agent": "startup-designer",
  "to_agent": "startup-analyst",
  "amount": 5.0,
  "task_description": "Analyze market trends"
}
```

**Response:**
```json
{
  "success": true,
  "tx_hash": "0x...",
  "from_agent": "startup-designer",
  "to_agent": "startup-analyst",
  "amount": 5.0
}
```

### GET /a2a/transfers
Get recent A2A transfers.

**Query Parameters:**
- `count` (int, default: 20): Maximum number of transfers

**Response:**
```json
{
  "transfers": [...],
  "total_count": 50
}
```

### GET /a2a/balances
Get all agent wallet balances.

**Response:**
```json
{
  "balances": {
    "startup-designer": 45.0,
    "startup-analyst": 55.0
  },
  "total": 100.0
}
```

### GET /a2a/agent/{agent_id}
Get detailed wallet info for an agent.

---

## Escrow

### GET /escrow/list
List all escrow transactions.

**Response:**
```json
{
  "escrows": [
    {
      "escrow_id": "escrow-abc123",
      "payer_agent_id": "startup-designer",
      "payee_agent_id": "startup-analyst",
      "amount": 10.0,
      "status": "created",
      "task_description": "Complete logo design",
      "created_at": "2024-01-15T10:00:00"
    }
  ],
  "total_count": 5,
  "by_status": {
    "created": 1,
    "submitted": 1,
    "verifying": 1,
    "released": 2,
    "refunded": 0,
    "disputed": 0
  }
}
```

### GET /escrow/{escrow_id}
Get details of a specific escrow.

### POST /escrow/{escrow_id}/dispute
Raise a dispute for an escrow transaction.

**Request:**
```json
{
  "reason": "Task was not completed as specified"
}
```

**Response:**
```json
{
  "message": "Dispute raised successfully",
  "escrow": {...}
}
```

---

## Registry

### GET /registry/agents
List all agents in the decentralized registry.

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "image-generator-1",
      "capabilities": ["image_generation", "logo_design"],
      "pricing": {"image_generation": 1.0},
      "reputation_score": 4.8,
      "success_rate": 0.95
    }
  ],
  "market_stats": {
    "total_agents": 10,
    "total_capabilities": 15
  }
}
```

### GET /registry/find
Find agents by capability.

**Query Parameters:**
- `capability` (string, required): Capability to search for

**Response:**
```json
{
  "capability": "image_generation",
  "agents": [...],
  "count": 3
}
```

### GET /registry/select
Select the best agent for a capability.

**Query Parameters:**
- `capability` (string, required): Capability needed
- `price_weight` (float, default: 0.4): Weight for price in selection
- `reputation_weight` (float, default: 0.4): Weight for reputation

---

## WebSocket

### WS /ws
WebSocket endpoint for real-time dashboard updates.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

**Server Messages:**

1. **Dashboard Update** (sent every 3 seconds):
```json
{
  "type": "dashboard_update",
  "timestamp": "2024-01-15T10:30:00",
  "data": {
    "treasury": {...},
    "agents": [...],
    "transactions": [...],
    "stats": {...},
    "escrows": [...]
  }
}
```

2. **Event Notification**:
```json
{
  "type": "event",
  "event_type": "transaction",
  "timestamp": "2024-01-15T10:30:00",
  "data": {
    "amount": 5.0,
    "agent_id": "user-agent"
  }
}
```

**Client Messages:**

1. **Ping** (keep-alive):
```json
{"type": "ping"}
```

2. **Refresh** (request immediate update):
```json
{"type": "refresh"}
```

---

## Error Responses

All endpoints may return error responses:

**400 Bad Request:**
```json
{
  "detail": "Invalid request parameters"
}
```

**404 Not Found:**
```json
{
  "detail": "Agent user-agent-xyz not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error message"
}
```

---

## Rate Limits

- Default: No rate limits (hackathon demo)
- Recommended for production: 100 requests/minute per IP

---

## Authentication

Currently no authentication required (hackathon demo).

For production, recommend:
- API key authentication
- JWT tokens for agent identity
- Wallet signature verification

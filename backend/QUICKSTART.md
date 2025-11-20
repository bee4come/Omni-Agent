# Backend Quick Start Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit `.env` and configure:
- AWS credentials (if using Bedrock) OR OpenAI API key
- Ethereum RPC URL (default: local hardhat node)
- Contract addresses (after deploying contracts)

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Or use the provided script:
```bash
./start_backend.sh
```

### Step 3: Start the Server

The server will start on http://localhost:8000

```bash
uvicorn app.main:app --reload
```

### Step 4: Test the API

Open another terminal:
```bash
python test_api.py
```

Or visit the interactive docs:
http://localhost:8000/docs

## 📋 What Just Happened?

The backend initialized:
1. ✅ **Policy Engine** - Loaded agent budgets and service prices from YAML configs
2. ✅ **Payment Client** - Connected to Ethereum (mock mode if no contracts deployed)
3. ✅ **System Logger** - Ready to track all transactions and policy decisions
4. ✅ **Omni Agent** - LLM-powered agent with 4 paid tools wrapped in payment logic

## 🔧 Main Components

### 1. FastAPI Server (`app/main.py`)
- Exposes REST API for chat, treasury, agents, services, transactions, logs
- CORS enabled for frontend integration
- Auto-generated docs at `/docs`

### 2. Omni Agent (`agents/omni_agent.py`)
- Orchestrates tool calls based on user messages
- Wraps every tool with payment + policy enforcement
- Supports AWS Bedrock or OpenAI LLMs (or mock mode)

### 3. Policy Engine (`policy/engine.py`)
- Checks budgets and priorities before allowing tool calls
- Can reject or downgrade requests based on rules
- Tracks daily spending per agent

### 4. Payment Wrapper (`payment/wrapper.py`)
- Wraps every tool call with:
  1. Policy check
  2. On-chain payment (via MNEE)
  3. Logging
  4. Tool execution

### 5. System Logger (`policy/logger.py`)
- Records all policy decisions (ALLOWED, REJECTED, DOWNGRADED)
- Records all transactions (SUCCESS, FAILED, MOCK)
- Provides analytics endpoints

## 🎯 Example Usage

### Chat with an Agent

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "user-agent",
    "message": "Generate a cyberpunk avatar"
  }'
```

### Check Treasury Status

```bash
curl http://localhost:8000/treasury
```

### View Transaction History

```bash
curl http://localhost:8000/transactions?limit=10
```

### View Policy Logs

```bash
curl http://localhost:8000/policy/logs?limit=10
```

## 🧪 Testing Scenarios

The test script (`test_api.py`) will run these scenarios:

1. ✅ **Normal Request**: user-agent generates an image (1.0 MNEE)
2. ✅ **Data Query**: user-agent queries ETH price (0.05 MNEE)
3. ⚠️ **Policy Rejection**: batch-agent tries expensive job (may exceed maxPerCall)
4. 📊 **Stats Check**: View overall system statistics

## 🐛 Troubleshooting

### "Agent not found" error
- Check `../config/agents.yaml` exists and is valid
- Ensure POLICY_CONFIG_PATH in .env points to correct location

### "Service not found" error
- Check `../config/services.yaml` exists and is valid
- Ensure SERVICE_CONFIG_PATH in .env points to correct location

### "No LLM credentials" warning
- The system will work in mock mode (keyword matching)
- For full LLM capabilities, add AWS or OpenAI credentials to .env

### Payment client warnings
- If contracts aren't deployed yet, payments will use MOCK mode
- The rest of the system (policy, logging, agents) still works normally

## 📚 Next Steps

1. **Deploy Contracts**: Deploy the smart contracts and update .env with addresses
2. **Start Providers**: Start the 4 service provider servers (ports 8001-8004)
3. **Connect Frontend**: Point your frontend to http://localhost:8000
4. **Customize**: Add more agents/services in the YAML config files

## 🔗 API Documentation

Full interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📦 Project Structure

```
backend/
├── app/              # FastAPI application
├── agents/           # Agent orchestration + tools
├── payment/          # Payment client + wrapper
├── policy/           # Policy engine + logger
├── .env              # Configuration (git-ignored)
├── requirements.txt  # Dependencies
├── start_backend.sh  # Startup script
├── test_api.py       # Test suite
├── README.md         # Full documentation
└── QUICKSTART.md     # This file
```

## 🎓 Learning Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **LangChain Docs**: https://python.langchain.com/
- **Web3.py Docs**: https://web3py.readthedocs.io/

---

**Need Help?** Check the full README.md for detailed documentation.

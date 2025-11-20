# MNEE Nexus Quick Reference Card

## 🚀 Getting Started (Choose One)

### Option A: Automated (Fastest)
```bash
python scripts/validate_config.py && ./start_all.sh
```

### Option B: Docker
```bash
docker-compose up -d
```

### Option C: Manual
See `README.md` for step-by-step instructions

---

## 📡 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Backend API | http://localhost:8000 | Main API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Hardhat Node | http://localhost:8545 | Ethereum RPC |
| ImageGen | http://localhost:8001 | Image generation |
| PriceOracle | http://localhost:8002 | Price data |
| BatchCompute | http://localhost:8003 | Batch jobs |
| LogArchive | http://localhost:8004 | Log storage |

---

## 🎮 Common Commands

### Service Management
```bash
./start_all.sh          # Start all services
./start_all.sh stop     # Stop all services
./start_all.sh restart  # Restart all services
./start_all.sh status   # Check service status
./start_all.sh logs <service>  # View logs
```

### Docker Commands
```bash
docker-compose up -d              # Start
docker-compose down               # Stop
docker-compose logs -f backend    # View logs
docker-compose restart backend    # Restart service
```

### Configuration
```bash
python scripts/validate_config.py  # Validate config
cat backend/.env                   # View environment
vim config/agents.yaml             # Edit agent config
```

### Backend API
```bash
curl http://localhost:8000/                  # Health check
curl http://localhost:8000/treasury         # Treasury status
curl http://localhost:8000/agents           # List agents
curl http://localhost:8000/transactions     # Transactions
python backend/test_api.py                  # Run tests
```

### Contracts
```bash
cd contracts
npx hardhat node                                    # Start node
npx hardhat run scripts/deploy.js --network localhost  # Deploy
cat deployments.json                                # View deployment
```

---

## 📂 Project Structure

```
MNEE-Agent/
├── backend/          # FastAPI backend + policy engine
├── contracts/        # Solidity smart contracts
├── providers/        # 4 service provider servers
├── config/           # YAML configuration files
├── scripts/          # Utility scripts
├── logs/             # Service logs (auto-created)
├── pids/             # Process IDs (auto-created)
├── start_all.sh      # Master startup script
└── docker-compose.yml # Docker orchestration
```

---

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `backend/.env` | Environment variables |
| `config/agents.yaml` | Agent budgets & priorities |
| `config/services.yaml` | Service pricing |
| `contracts/deployments.json` | Deployed contract addresses |

---

## 📊 Key Endpoints

### Chat
```bash
POST /chat
{
  "agent_id": "user-agent",
  "message": "Generate a cyberpunk avatar"
}
```

### Treasury
```bash
GET /treasury           # Overall status
GET /agents             # List all agents
GET /agents/{id}        # Agent details
GET /services           # List services
GET /services/{id}      # Service details
```

### Transactions & Logs
```bash
GET /transactions?limit=50    # Transaction history
GET /policy/logs?limit=50     # Policy decisions
GET /stats                    # System statistics
```

### Management
```bash
PUT /agents/{id}/budget       # Update budget
POST /reset                   # Reset daily spending
```

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check status
./start_all.sh status

# View logs
./start_all.sh logs <service_name>

# Restart specific service
./start_all.sh restart
```

### Configuration Issues
```bash
# Validate configuration
python scripts/validate_config.py

# Check .env file exists
ls -la backend/.env

# Copy template if missing
cp backend/.env.example backend/.env
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different ports in .env
```

### Docker Issues
```bash
# View all containers
docker-compose ps

# View logs
docker-compose logs -f

# Rebuild
docker-compose build --no-cache

# Clean restart
docker-compose down -v && docker-compose up -d
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| `README.md` | Main project documentation |
| `COMPLETED_OPTIMIZATIONS.md` | What's been optimized |
| `OPTIMIZATION_SUMMARY.md` | Detailed optimization report |
| `backend/README.md` | Backend architecture |
| `backend/QUICKSTART.md` | 5-minute backend setup |
| `scripts/README.md` | Scripts documentation |

---

## 🎯 Agent IDs

- `user-agent` - High priority, interactive tasks
- `batch-agent` - Low priority, batch processing
- `ops-agent` - Medium priority, operations

---

## 💰 Service IDs

- `IMAGE_GEN_PREMIUM` - 1.0 MNEE/call
- `PRICE_ORACLE` - 0.05 MNEE/query
- `BATCH_COMPUTE` - 3.0 MNEE/job
- `LOG_ARCHIVE` - 0.01 MNEE/log

---

## ✅ Health Checks

```bash
# Quick health check
curl http://localhost:8000/ && \
curl http://localhost:8001/docs && \
curl http://localhost:8002/docs && \
curl http://localhost:8003/docs && \
curl http://localhost:8004/docs && \
curl http://localhost:8545 && \
echo "✅ All services healthy"

# Or use the status command
./start_all.sh status
```

---

## 🔐 Environment Variables

### Required
- `ETH_RPC_URL` - Ethereum RPC endpoint
- `MNEE_TOKEN_ADDRESS` - MNEE contract address
- `POLICY_CONFIG_PATH` - Path to agents.yaml
- `SERVICE_CONFIG_PATH` - Path to services.yaml

### Optional (for full functionality)
- `PAYMENT_ROUTER_ADDRESS` - PaymentRouter contract
- `TREASURY_PRIVATE_KEY` - Treasury wallet key
- `AWS_ACCESS_KEY_ID` - AWS credentials (or)
- `OPENAI_API_KEY` - OpenAI credentials

---

## 💡 Tips

1. **Always validate config first:**
   ```bash
   python scripts/validate_config.py
   ```

2. **Use automated startup for demos:**
   ```bash
   ./start_all.sh
   ```

3. **Check logs when debugging:**
   ```bash
   ls -la logs/
   tail -f logs/backend.log
   ```

4. **Monitor system status:**
   ```bash
   watch -n 2 './start_all.sh status'
   ```

5. **Quick API test:**
   ```bash
   python backend/test_api.py
   ```

---

## 📞 Getting Help

1. Check service status: `./start_all.sh status`
2. View logs: `./start_all.sh logs <service>`
3. Validate config: `python scripts/validate_config.py`
4. Read documentation in `/backend/` and `/scripts/`
5. Check API docs: http://localhost:8000/docs

---

**Print this page for quick reference during development!** 📄

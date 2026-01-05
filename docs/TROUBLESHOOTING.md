# Troubleshooting Guide

This document provides solutions to common issues you may encounter when running MNEE Nexus.

## Table of Contents

- [Service Startup Issues](#service-startup-issues)
- [WebSocket Connection Issues](#websocket-connection-issues)
- [Contract Deployment Issues](#contract-deployment-issues)
- [Policy Engine Issues](#policy-engine-issues)
- [Frontend Issues](#frontend-issues)
- [Demo Day Checklist](#demo-day-checklist)

---

## Service Startup Issues

### Services fail to start

**Symptom:** Running `./start_all.sh` results in errors or services not starting.

**Solutions:**

1. **Check if ports are already in use:**
   ```bash
   lsof -i :8000   # Backend
   lsof -i :8100   # Guardian
   lsof -i :8545   # Hardhat
   lsof -i :3000   # Frontend
   ```

2. **Kill existing processes:**
   ```bash
   # Kill specific port
   kill $(lsof -t -i:8000)

   # Or stop all services
   ./start_all.sh stop
   ```

3. **Check service status:**
   ```bash
   ./start_all.sh status
   ```

4. **View service logs:**
   ```bash
   ./start_all.sh logs backend
   ./start_all.sh logs guardian
   ./start_all.sh logs hardhat
   ```

### Missing dependencies

**Symptom:** Import errors or module not found.

**Solutions:**

1. **Backend dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Frontend dependencies:**
   ```bash
   cd frontend
   npm install
   ```

3. **Contract dependencies:**
   ```bash
   cd contracts
   npm install
   ```

---

## WebSocket Connection Issues

### WebSocket disconnects or fails to connect

**Symptom:** Frontend shows "Disconnected" or real-time updates don't work.

**Causes:**
- Backend not running
- Firewall blocking port 8000
- CORS misconfiguration

**Solutions:**

1. **Verify backend is running:**
   ```bash
   curl http://localhost:8000/
   ```

2. **Check WebSocket URL in frontend:**
   - Ensure `NEXT_PUBLIC_WS_URL` in `.env` matches backend address
   - Default: `ws://localhost:8000/ws`

3. **The frontend automatically falls back to polling:**
   - If WebSocket fails, the UI will use HTTP polling every 5 seconds
   - Check browser console for connection status

---

## Contract Deployment Issues

### Contracts fail to deploy

**Symptom:** `npx hardhat run scripts/deploy.js` fails.

**Solutions:**

1. **Ensure Hardhat node is running:**
   ```bash
   cd contracts
   npx hardhat node
   ```

2. **Verify RPC connection:**
   ```bash
   curl -X POST http://127.0.0.1:8545 \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
   ```

3. **Redeploy contracts:**
   ```bash
   cd contracts
   npx hardhat run scripts/deploy.js --network localhost
   ```

4. **Update backend .env with new addresses:**
   - After deployment, copy contract addresses to `backend/.env`

### MNEE token issues

**Symptom:** Payments fail with "insufficient balance".

**Solutions:**

1. **Check treasury balance:**
   ```bash
   curl http://localhost:8000/treasury
   ```

2. **The Hardhat fork uses impersonation to get MNEE tokens.**
   - This is automatic during deployment
   - If issues persist, restart Hardhat node and redeploy

---

## Policy Engine Issues

### Agent denied - budget exceeded

**Symptom:** Policy logs show "DENY" with "Daily budget exceeded".

**Solutions:**

1. **Reset daily spending:**
   ```bash
   curl -X POST http://localhost:8000/reset
   ```

2. **Increase agent budget:**
   ```bash
   curl -X PUT http://localhost:8000/agents/{agent_id}/budget \
     -H "Content-Type: application/json" \
     -d '{"daily_budget": 200.0}'
   ```

3. **Check agent status (may be paused):**
   ```bash
   curl http://localhost:8000/agents/{agent_id}
   ```

### Agent is paused

**Symptom:** All calls from an agent are denied with "Agent is paused".

**Solution:**

Resume the agent:
```bash
curl -X PUT http://localhost:8000/agents/{agent_id}/resume
```

---

## Frontend Issues

### Build fails

**Symptom:** `npm run build` shows TypeScript errors.

**Solutions:**

1. **Clear cache and rebuild:**
   ```bash
   cd frontend
   rm -rf .next node_modules
   npm install
   npm run build
   ```

2. **Check TypeScript errors:**
   ```bash
   npm run lint
   ```

### Demo mode not working

**Symptom:** Frontend shows empty state despite demo mode enabled.

**Solution:**

Verify environment variable:
```bash
# In frontend/.env
NEXT_PUBLIC_DEMO_MODE=true

# Then restart the dev server
npm run dev
```

---

## Demo Day Checklist

Before starting your demo, verify the following:

### Pre-Demo Verification

```bash
# 1. Start all services
./start_all.sh

# 2. Wait 30 seconds, then check status
./start_all.sh status

# 3. Verify backend health
curl http://localhost:8000/

# 4. Verify treasury has balance
curl http://localhost:8000/treasury

# 5. Verify agents are not paused
curl http://localhost:8000/agents

# 6. Reset budgets for fresh demo
curl -X POST http://localhost:8000/reset

# 7. Open frontend
open http://localhost:3000
```

### Quick Recovery Commands

If something goes wrong during demo:

```bash
# Reset all agent budgets
curl -X POST http://localhost:8000/reset

# Resume a paused agent
curl -X PUT http://localhost:8000/agents/{agent_id}/resume

# Restart backend only
./start_all.sh restart backend

# Use demo mode (no backend required)
NEXT_PUBLIC_DEMO_MODE=true npm run dev
```

### Emergency Fallback

If live backend fails, enable demo mode:

1. Stop the frontend
2. Set `NEXT_PUBLIC_DEMO_MODE=true` in `frontend/.env`
3. Restart: `npm run dev`
4. Demo continues with simulated data

---

## Getting Help

If you encounter issues not covered here:

1. Check the logs: `./start_all.sh logs [service]`
2. Review API documentation: `docs/API.md`
3. Check architecture: `docs/ARCHITECTURE.md`
4. File an issue on GitHub

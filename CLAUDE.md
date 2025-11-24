# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**MNEE Nexus / Omni-Agent** 是一个为 AI Agent 设计的可编程支付编排系统，基于 MNEE 稳定币。该系统允许多个 AI Agent 共享一个 MNEE 资金池，通过预算、策略和优先级管理，以按任务付费的方式调用不同的服务提供商。

**核心特性：**
- 基于真实 MNEE 合约 (`0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF`) 的 Hardhat 主网 fork
- 链下策略引擎强制执行预算和优先级
- 四类服务提供商：ImageGen、PriceOracle、BatchCompute、LogArchive
- LangChain 驱动的 Omni-Agent 协调器

## 架构概览

### 四层架构

1. **智能合约层** (`contracts/`)
   - `MNEEServiceRegistry.sol` - 注册服务商、定价和状态
   - `MNEEPaymentRouter.sol` - 处理 MNEE 支付和事件发射
   - 使用 Hardhat fork 连接真实 MNEE 合约（零成本测试）

2. **后端编排层** (`backend/`)
   - **Guardian Service** (`guardian/service.py`) - Isolated key management (Port 8100)
   - **Policy Engine** (`policy/engine.py`) - 强制执行预算、优先级和支出限制
   - **Payment Client** (`payment/client.py`) - Calls Guardian for payments (no longer holds private keys)
   - **PaidToolWrapper** (`payment/wrapper.py`) - 包装所有工具调用：策略检查 → 支付 → 执行
   - **Omni-Agent** (`agents/omni_agent.py`) - LangChain/LangGraph 驱动的主协调器

3. **服务提供商层** (`providers/`)
   - `imagegen/` - 图像生成服务 (1.0 MNEE/调用)
   - `price_oracle/` - 价格数据查询 (0.05 MNEE/查询)
   - `batch_compute/` - 批量计算任务 (3.0 MNEE/任务)
   - `log_archive/` - 日志存储服务 (0.01 MNEE/日志)
   - 每个提供商是独立的 FastAPI 服务，验证链上支付事件

4. **前端层** (`frontend/`)
   - Next.js + React + TailwindCSS
   - 实时聊天界面、资金池仪表板、交易流和策略日志

## 常用开发命令

### 快速启动（推荐）

```bash
# 验证配置
python scripts/validate_config.py

# 启动所有服务（Hardhat + 合约 + 提供商 + 后端）
./start_all.sh

# 检查状态
./start_all.sh status

# 查看日志
./start_all.sh logs backend
./start_all.sh logs imagegen

# 停止所有服务
./start_all.sh stop
```

### 分步启动

```bash
# 1. 启动 Hardhat fork (Terminal 1)
cd contracts
npx hardhat node

# 2. 部署合约 (Terminal 2)
cd contracts
npx hardhat run scripts/deploy.js --network localhost

# 3. 启动后端 (Terminal 3)
cd backend
uvicorn app.main:app --reload --port 8000

# 4. 启动服务提供商 (Terminal 4-7)
cd providers/imagegen && python main.py
cd providers/price_oracle && python main.py
cd providers/batch_compute && python main.py
cd providers/log_archive && python main.py

# 5. 启动前端 (Terminal 8)
cd frontend
npm run dev
```

### 智能合约开发

```bash
cd contracts

# 编译合约
npx hardhat compile

# 运行测试
npx hardhat test

# 部署到本地 fork
npx hardhat run scripts/deploy.js --network localhost

# Hardhat console 交互
npx hardhat console --network localhost
```

### Guardian Service Development

```bash
cd backend

# Start Guardian standalone
python -m guardian.service

# Or use startup script
cd guardian
./start_guardian.sh

# Test Guardian endpoints
curl http://localhost:8100/
curl http://localhost:8100/guardian/balance

# Check Guardian logs
tail -f ../logs/guardian.log
```

**Important:** Guardian Service is the ONLY service that holds `TREASURY_PRIVATE_KEY`. Never access private keys directly in Payment Client or other services.

### 后端开发

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行后端（开发模式）
uvicorn app.main:app --reload --port 8000

# 运行 API 测试
python test_api.py

# 健康检查
./health_check.sh
```

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 开发服务器
npm run dev

# 构建生产版本
npm run build

# 启动生产服务器
npm start
```

### 测试命令

```bash
# 后端 API 测试
curl http://localhost:8000/
curl http://localhost:8000/treasury
curl http://localhost:8000/agents

# 测试聊天接口
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"user-agent","message":"Generate a cyberpunk avatar"}'

# 验证所有服务健康
curl http://localhost:8000/ && \
curl http://localhost:8001/docs && \
curl http://localhost:8002/docs && \
curl http://localhost:8003/docs && \
curl http://localhost:8004/docs && \
echo "✅ All services healthy"
```

## 关键配置文件

### Agent 配置 (`config/agents.yaml`)

定义 Agent 的预算、优先级和每次调用限制：

```yaml
agents:
  - id: "user-agent"
    priority: "HIGH"        # 最高优先级
    dailyBudget: 100.0      # 每日预算
    maxPerCall: 10.0        # 单次调用最大金额

  - id: "batch-agent"
    priority: "LOW"         # 低优先级
    dailyBudget: 50.0
    maxPerCall: 20.0

  - id: "ops-agent"
    priority: "MEDIUM"
    dailyBudget: 30.0
    maxPerCall: 5.0
```

### 服务配置 (`config/services.yaml`)

定义服务提供商的定价和地址：

```yaml
services:
  - id: "IMAGE_GEN_PREMIUM"
    unitPrice: 1.0          # 1.0 MNEE/调用
    providerAddress: "0x..."
    active: true

  - id: "PRICE_ORACLE"
    unitPrice: 0.05
    providerAddress: "0x..."
    active: true
```

### 环境变量 (`backend/.env`)

```bash
# Ethereum 配置
ETH_RPC_URL=http://127.0.0.1:8545
MNEE_TOKEN_ADDRESS=0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF

# 智能合约地址（从部署输出复制）
PAYMENT_ROUTER_ADDRESS=0x...
SERVICE_REGISTRY_ADDRESS=0x...

# 资金池配置（Hardhat Account #1）
TREASURY_PRIVATE_KEY=0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d

# 配置文件路径
POLICY_CONFIG_PATH=../config/agents.yaml
SERVICE_CONFIG_PATH=../config/services.yaml

# LLM API Keys (至少需要一个)
OPENAI_API_KEY=sk-...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

## 核心工作流

### 添加新服务提供商

1. **合约注册**：在 `ServiceRegistry` 合约中注册新服务
2. **配置**：在 `config/services.yaml` 中添加服务定义
3. **实现提供商**：在 `providers/` 中创建新的 HTTP 服务
4. **定义工具**：在 `backend/agents/tools/definitions.py` 中创建工具函数
5. **注册工具**：在 `backend/agents/omni_agent.py` 的 `create_agent()` 中注册

### 修改策略逻辑

所有策略逻辑集中在 `backend/policy/engine.py`：

- **预算检查**：`check_policy()` 方法验证每日预算和单次调用限制
- **优先级管理**：基于 Agent 优先级（HIGH/MEDIUM/LOW）做决策
- **降级逻辑**：当预算不足时自动降级服务（例如：全量日志 → 摘要日志）

**重要**：不要在智能合约中实现复杂策略逻辑。合约应保持简单，只处理基本支付路由。

### 支付流程

Every tool call goes through the Payment Client's secure flow:

1. **Policy Check** - Policy Engine decides ALLOW/DENY/DOWNGRADE
2. **Guardian Quote** - Pre-check with Guardian Service (fast, no blockchain)
3. **Guardian Pay** - Guardian signs and executes on-chain payment
4. **Service Execution** - Call service provider's HTTP API
5. **Record Usage** - Log transaction and policy decisions

**Security Note:** Payment Client NEVER holds private keys. All signing happens in isolated Guardian Service (port 8100).

## 技术细节

### Hardhat Fork 架构

- 使用真实 MNEE 合约 `0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF`
- Fork 自 Ethereum 主网区块 #21000000
- 通过 `impersonateAccount` 获取 MNEE 代币（无需真实资金）
- 所有 ERC-20 交互与主网完全一致
- 配置：`contracts/hardhat.config.ts` 中的 `forking` 部分

### LangChain Agent 集成

- 主协调器：`backend/agents/omni_agent.py`
- 使用 LangGraph 的 `create_react_agent()`
- 所有工具通过 `PaidToolWrapper` 自动强制执行支付
- 支持 OpenAI 和 AWS Bedrock LLM

### Web3 交互

- 库：`web3.py`
- 主客户端：`backend/payment/client.py`
- 监听 `PaymentExecuted` 事件以进行审计
- 自动处理 gas 估算和交易重试

## 服务端口

| 服务 | 端口 | 用途 |
|------|------|------|
| Hardhat Node | 8545 | Ethereum RPC |
| Backend API | 8000 | 主 API 和 Swagger 文档 |
| **Guardian Service** | **8100** | **Secure key management** |
| ImageGen | 8001 | 图像生成服务 |
| PriceOracle | 8002 | 价格数据服务 |
| BatchCompute | 8003 | 批量计算服务 |
| LogArchive | 8004 | 日志存储服务 |
| Frontend | 3000 | Next.js 开发服务器 |

## 故障排查

### 服务无法启动

```bash
# 检查状态
./start_all.sh status

# 查看特定服务日志
./start_all.sh logs <service_name>

# 检查端口占用
lsof -i :8000
```

### 合约交互失败

- 确认 Hardhat node 正在运行
- 验证 `backend/.env` 中的合约地址正确
- 检查 Treasury 有足够的 MNEE 余额（通过 Hardhat console）

### 策略拒绝

- 检查 `config/agents.yaml` 中的预算配置
- 查看策略日志：`curl http://localhost:8000/policy/logs`
- 重置每日支出：`curl -X POST http://localhost:8000/reset`

## 开发最佳实践

1. **修改配置后**：重启后端服务以加载新配置
2. **修改合约后**：需要重新部署并更新后端 `.env` 文件
3. **本地测试**：使用 Hardhat fork 而不是真实网络
4. **日志查看**：所有日志保存在 `logs/` 目录
5. **策略优先**：先在链下实现和测试策略，而不是在合约中

## 相关文档

- **完整说明**：`FINAL_PROJECT_OVERVIEW.md` - 项目的"为什么"和架构
- **快速参考**：`QUICK_REFERENCE.md` - 命令和端点速查表
- **后端文档**：`backend/README.md` - API 端点详细说明
- **Fork 指南**：`HARDHAT_FORK_GUIDE.md` - Hardhat fork 设置步骤
- **项目规范**：`project_spec.md` - 完整的中文技术规范

## 项目目标

这是一个 Hackathon MVP，展示：
- ✅ 多 Agent 共享预算协调
- ✅ 基于 MNEE 的链上支付
- ✅ 链下策略强制执行（预算、优先级）
- ✅ 服务提供商经济模型
- ✅ 透明的交易和策略审计

重点是展示**架构和工作流**，而不是生产级别的完善。

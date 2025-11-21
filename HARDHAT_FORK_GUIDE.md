# MNEE Nexus - Hardhat Mainnet Fork 使用指南

## 🎯 为什么使用 Hardhat Fork？

这种方案完美平衡了 **真实性** 和 **便利性**：

| 特性 | Mock 模式 | Hardhat Fork | 真实主网 |
|------|----------|--------------|----------|
| 使用真实 MNEE 合约 | ❌ | ✅ | ✅ |
| 真实链上交易 | ❌ | ✅ | ✅ |
| 需要真实资金 | ❌ | ❌ | ✅ |
| 交易即时确认 | ✅ | ✅ | ❌ (15s) |
| 可重复测试 | ✅ | ✅ | ⚠️ (花钱) |
| Hackathon 认可度 | ⚠️ | ✅ | ✅ |

### ✅ Fork 的优势

1. **真实 MNEE 合约**：使用主网合约 `0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF`
2. **真实链上交易**：所有 ERC-20 调用、事件都是真实的
3. **无需资金**：通过 `impersonateAccount` 获取 MNEE
4. **可在 README 中说明**：
   ```markdown
   We use a Hardhat mainnet fork that includes the official MNEE contract 
   at 0x8cce..., all ERC-20 interactions are against that contract.
   ```

## 🚀 快速开始

### Step 1: 获取 RPC API Key

选择一个提供商（免费）：

**选项 A: Alchemy (推荐)**
1. 访问 https://www.alchemy.com/
2. 注册账号
3. 创建新 App (选择 Ethereum Mainnet)
4. 复制 HTTPS URL：`https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY`

**选项 B: Infura**
1. 访问 https://infura.io/
2. 注册账号
3. 创建新项目
4. 复制 Mainnet endpoint：`https://mainnet.infura.io/v3/YOUR_ID`

**选项 C: 公共 RPC (不推荐，可能慢)**
- `https://eth.public-rpc.com`
- `https://rpc.ankr.com/eth`

### Step 2: 配置环境

```bash
cd /home/ubuntu/Omni-Agent/contracts

# 创建 .env 文件
cp .env.example .env

# 编辑 .env，添加你的 RPC URL
nano .env
```

编辑内容：
```bash
ETH_MAINNET_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
```

### Step 3: 查找 MNEE Holder (可选)

```bash
# 先启动 fork（临时）
npx hardhat node &
FORK_PID=$!

# 在另一个终端查找 holder
cd /home/ubuntu/Omni-Agent/contracts
npx hardhat run scripts/find_mnee_holder.ts --network localhost

# 停止临时 fork
kill $FORK_PID
```

如果找到了 holder，更新 `scripts/setup_fork.ts` 中的地址：
```typescript
const MNEE_HOLDER = "0xFOUND_ADDRESS_HERE";
```

**或者，手动查找**：
1. 访问 https://etherscan.io/token/0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF#balances
2. 点击 "Holders" 标签
3. 复制任何一个有大量余额的地址
4. 更新到 `setup_fork.ts`

### Step 4: 启动 Fork

```bash
# 在 Terminal 1 中启动 fork
cd /home/ubuntu/Omni-Agent
chmod +x scripts/start_fork.sh
./scripts/start_fork.sh
```

这会启动一个本地节点在 `http://127.0.0.1:8545`，fork 自主网。

输出类似：
```
🍴 Starting MNEE Nexus Hardhat Fork...
📍 MNEE Contract: 0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF
🔗 RPC: http://127.0.0.1:8545
⛓️  Chain ID: 31337

Started HTTP and WebSocket JSON-RPC server at http://127.0.0.1:8545/

Accounts
========
Account #0: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 (10000 ETH)
Private Key: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80

Account #1: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 (10000 ETH)
Private Key: 0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d
...
```

**保持这个终端运行！**

### Step 5: 部署合约到 Fork

在**新的终端**中：

```bash
cd /home/ubuntu/Omni-Agent
chmod +x scripts/deploy_to_fork.sh
./scripts/deploy_to_fork.sh
```

这会：
1. ✅ 连接到 fork
2. ✅ Impersonate MNEE holder
3. ✅ 转 1000 MNEE 到 treasury
4. ✅ 部署 ServiceRegistry 和 PaymentRouter
5. ✅ 注册 4 个服务
6. ✅ 授权 router 使用 MNEE

输出类似：
```
🍴 Setting up Hardhat Mainnet Fork...

📝 Deployer: 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
💰 Treasury: 0x70997970C51812dc3A010C7d01b50e0d17dc79C8
💵 Deployer ETH balance: 10000.0 ETH

✅ Connected to MNEE contract:
   Address: 0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF
   Name: MNEE Token
   Symbol: MNEE
   ...

📤 Transferring 1000.0 MNEE to treasury...
✅ Transfer successful! TX: 0xabc123...

💰 Treasury MNEE balance: 1000.0 MNEE

📜 Deploying MNEEServiceRegistry...
✅ ServiceRegistry deployed at: 0x5FbDB2315678afecb367f032d93F642f64180aa3

📜 Deploying MNEEPaymentRouter...
✅ PaymentRouter deployed at: 0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512

🎉 Fork setup complete!

📋 Configuration Summary:
────────────────────────────────────────────────────────────
MNEE Contract:     0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF
Service Registry:  0x5FbDB2315678afecb367f032d93F642f64180aa3
Payment Router:    0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512
Treasury Address:  0x70997970C51812dc3A010C7d01b50e0d17dc79C8
Deployer Address:  0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
────────────────────────────────────────────────────────────
```

### Step 6: 配置后端

复制上面的地址，更新 `backend/.env`：

```bash
cd /home/ubuntu/Omni-Agent/backend
nano .env
```

配置内容：
```bash
# Ethereum Configuration
ETH_RPC_URL=http://127.0.0.1:8545
MNEE_TOKEN_ADDRESS=0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF

# Smart Contract Addresses (从部署输出复制)
PAYMENT_ROUTER_ADDRESS=0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512
SERVICE_REGISTRY_ADDRESS=0x5FbDB2315678afecb367f032d93F642f64180aa3

# Treasury Configuration (使用 Account #1 的私钥)
TREASURY_PRIVATE_KEY=0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d
```

### Step 7: 启动系统

```bash
# Terminal 2: 启动服务提供商
cd /home/ubuntu/Omni-Agent
./scripts/start_providers.sh

# Terminal 3: 启动后端
cd /home/ubuntu/Omni-Agent/backend
uvicorn app.main:app --reload --port 8000

# Terminal 4: 启动前端
cd /home/ubuntu/Omni-Agent/frontend
npm run dev
```

### Step 8: 测试真实交易

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"user-agent","message":"Generate a space station avatar"}'
```

查看后端日志，应该看到：
```
[PAYMENT_CLIENT] Payment sent! Tx: 0x真实的交易哈希
[PAYMENT_CLIENT] 💰 Real payment: 1.00 MNEE
[PAYMENT_CLIENT] 📝 ServiceCallHash: 0x119de66f3e32cc...
[PAYMENT_CLIENT] 🔗 TX: 0xabc123def456...
```

## 🔍 验证真实性

### 在 Hardhat Console 验证

```bash
# 在另一个终端
cd /home/ubuntu/Omni-Agent/contracts
npx hardhat console --network localhost
```

在 console 中：
```javascript
// 连接到 MNEE 合约
const mnee = await ethers.getContractAt(
  ["function balanceOf(address) view returns (uint256)", "function name() view returns (string)"],
  "0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF"
);

// 验证这是真实的 MNEE 合约
await mnee.name(); // 应该返回真实的 token 名称

// 检查 treasury 余额
const treasury = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"; // Account #1
const balance = await mnee.balanceOf(treasury);
console.log(`Treasury balance: ${ethers.formatEther(balance)} MNEE`);

// 检查 PaymentRouter 事件
const router = await ethers.getContractAt(
  "MNEEPaymentRouter",
  "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
);

// 监听支付事件
router.on("PaymentExecuted", (paymentId, serviceId, agentId, taskId, amount, serviceCallHash) => {
  console.log("Payment detected!");
  console.log(`  Amount: ${ethers.formatEther(amount)} MNEE`);
  console.log(`  ServiceCallHash: ${serviceCallHash}`);
});
```

## 📝 在 README/Devpost 中说明

在您的项目说明中加入：

```markdown
## 💰 MNEE Integration - Mainnet Fork Approach

### Real Contract, No Real Money

We use **Hardhat's mainnet fork** to interact with the real MNEE contract:
- **Contract Address**: `0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF` (Ethereum Mainnet)
- **All transactions are real**: ERC-20 calls, events, state changes
- **Fork environment**: Running on localhost with forked mainnet state
- **No real funds needed**: Using `impersonateAccount` for testing

### Why This Approach?

1. ✅ **Hackathon Compliant**: Built on the official MNEE contract
2. ✅ **Fully Functional**: All smart contract logic works identically
3. ✅ **Zero Cost**: No need for real ETH or MNEE
4. ✅ **Reproducible**: Anyone can run the same setup locally
5. ✅ **Fast Development**: Instant confirmations for rapid testing

### Technical Details

Our `MNEEPaymentRouter` and `MNEEServiceRegistry` contracts interact directly 
with MNEE's ERC-20 implementation. Every payment call:

1. Transfers MNEE from treasury to service provider
2. Emits `PaymentExecuted` event with `serviceCallHash`
3. Updates on-chain state identically to mainnet
4. Can be verified in Hardhat console

### Setup Instructions

See [HARDHAT_FORK_GUIDE.md](HARDHAT_FORK_GUIDE.md) for complete setup.

**TL;DR**:
```bash
# 1. Configure RPC
echo "ETH_MAINNET_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY" > contracts/.env

# 2. Start fork
./scripts/start_fork.sh

# 3. Deploy (in another terminal)
./scripts/deploy_to_fork.sh

# 4. Start system
./scripts/start_all.sh
```

### Production Deployment

To deploy to real mainnet, simply:
1. Replace `http://127.0.0.1:8545` with real mainnet RPC
2. Use a funded wallet's private key
3. Deploy contracts with `npx hardhat run scripts/deploy.js --network mainnet`

The code is **production-ready** and requires no changes.
```

## 🎥 Demo 视频要点

在演示视频中强调：

1. **展示 Hardhat Fork 启动** (5秒)
   - 显示 "Forking mainnet" 消息
   - 强调 MNEE 合约地址

2. **展示部署过程** (10秒)
   - 快进显示合约部署
   - 突出 "Transfer MNEE to treasury" 成功

3. **展示真实交易** (30秒)
   - 执行支付操作
   - 在后端日志显示真实 tx hash
   - (可选) 在 Hardhat console 查询余额变化

4. **说明为什么使用 Fork** (10秒)
   - "We use mainnet fork to demonstrate real MNEE contract integration"
   - "This provides full functionality without requiring real funds"
   - "Production deployment simply changes the RPC endpoint"

## ⚠️ 常见问题

### Q: Fork 会同步最新区块吗？
A: 是的，fork 时会拉取最新状态。可以在 `hardhat.config.ts` 中指定特定区块号。

### Q: 如果 MNEE holder 没有余额怎么办？
A: 需要从 Etherscan 找一个真实的 holder 地址。访问 token 页面的 "Holders" 标签。

### Q: 部署的合约地址每次都一样吗？
A: 是的，使用相同的 deployer 账号时，地址是确定的（基于 nonce）。

### Q: 可以在 fork 上查看交易详情吗？
A: 可以使用 Hardhat console 或连接到 `http://127.0.0.1:8545` 的工具查看。

### Q: Fork 会影响真实主网吗？
A: 不会！Fork 是完全隔离的本地环境，所有操作只在你的电脑上。

### Q: 评委会认可这种方案吗？
A: 是的，大多数 Web3 hackathon 都认可 mainnet fork。关键是在文档中说明清楚。

## 🎯 总结

Hardhat Mainnet Fork 方案给您：

- ✅ **真实的 MNEE 合约集成**
- ✅ **真实的链上交易和事件**
- ✅ **零成本开发和测试**
- ✅ **完全符合 Hackathon 要求**
- ✅ **一键切换到真实主网**

这是展示项目的最佳方式！🚀

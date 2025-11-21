# 真实 MNEE 合约集成指南

## 🎯 目标
将 Mock 模式切换到真实的 MNEE 链上支付

## 📋 前置要求

### 1. 获取 MNEE 代币
MNEE 合约地址: `0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF`

**选项 A: 从交易所购买**
- 查看 [MNEE Resources](https://mnee-eth.devpost.com/resources)
- 使用 swap/bridge 获取 MNEE

**选项 B: 测试网获取**
- 如果有 Sepolia/Goerli 测试网版本
- 使用 faucet 获取测试 MNEE

### 2. 准备钱包
```bash
# 生成新钱包（或使用现有）
# 方法1: 使用 MetaMask 导出私钥
# 方法2: 使用 Python 生成
python3 << 'EOF'
from eth_account import Account
account = Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
EOF
```

### 3. 获取 ETH（用于 Gas）
- 主网: 购买少量 ETH (~$10-20)
- 测试网: 使用 faucet

## 🔧 配置步骤

### Step 1: 更新 .env 文件

```bash
cd /home/ubuntu/Omni-Agent/backend
cp .env.example .env
```

编辑 `.env`:
```bash
# Ethereum Configuration
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY  # 或 Infura
MNEE_TOKEN_ADDRESS=0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF

# Treasury Configuration
TREASURY_PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE  # ⚠️ 保密！不要提交到 Git

# Smart Contract Addresses (部署后填写)
PAYMENT_ROUTER_ADDRESS=0xYOUR_DEPLOYED_ROUTER_ADDRESS
SERVICE_REGISTRY_ADDRESS=0xYOUR_DEPLOYED_REGISTRY_ADDRESS
```

### Step 2: 获取免费 RPC 节点

**Alchemy (推荐)**:
1. 访问 https://www.alchemy.com/
2. 创建免费账户
3. 创建新 App (Ethereum Mainnet)
4. 复制 HTTPS URL

**Infura**:
1. 访问 https://infura.io/
2. 创建免费账户
3. 创建新项目
4. 复制 Mainnet endpoint

### Step 3: 部署自定义智能合约（可选）

如果需要部署自己的 PaymentRouter 和 ServiceRegistry:

```bash
cd /home/ubuntu/Omni-Agent/contracts

# 安装依赖
npm install

# 配置 Hardhat
# 编辑 hardhat.config.ts，添加主网配置

# 部署
npx hardhat run scripts/deploy_contracts.ts --network mainnet
```

### Step 4: 给 Treasury 钱包充值

```bash
# 1. 发送 ETH 到 Treasury 地址（用于 gas）
#    建议: 0.01 ETH (~$30)

# 2. 发送 MNEE 到 Treasury 地址
#    建议: 100-1000 MNEE（根据测试需求）
```

### Step 5: 验证配置

```python
# 运行测试脚本
python3 << 'EOF'
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

# 连接到网络
rpc_url = os.getenv("ETH_RPC_URL")
w3 = Web3(Web3.HTTPProvider(rpc_url))

print(f"✅ Connected to Ethereum: {w3.is_connected()}")
print(f"📊 Latest block: {w3.eth.block_number}")

# 检查 Treasury 余额
private_key = os.getenv("TREASURY_PRIVATE_KEY")
if private_key:
    from eth_account import Account
    account = Account.from_key(private_key)
    
    eth_balance = w3.eth.get_balance(account.address)
    print(f"💰 Treasury Address: {account.address}")
    print(f"💰 ETH Balance: {w3.from_wei(eth_balance, 'ether')} ETH")
    
    # 检查 MNEE 余额
    mnee_address = os.getenv("MNEE_TOKEN_ADDRESS")
    if mnee_address:
        # 简化的 ERC20 ABI
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
        mnee_contract = w3.eth.contract(address=mnee_address, abi=erc20_abi)
        mnee_balance = mnee_contract.functions.balanceOf(account.address).call()
        print(f"💵 MNEE Balance: {mnee_balance / 10**18} MNEE")
else:
    print("⚠️  No private key configured")
EOF
```

## 🚀 启动真实支付模式

```bash
# 确保 .env 配置正确
cd /home/ubuntu/Omni-Agent/backend

# 启动后端
uvicorn app.main:app --reload --port 8000
```

系统会自动检测配置：
- ✅ 如果 `PAYMENT_ROUTER_ADDRESS` 和 `TREASURY_PRIVATE_KEY` 都配置 → 真实支付
- ⚠️ 否则 → Mock 模式

## 📊 监控真实交易

### 在 Etherscan 查看
```
https://etherscan.io/address/YOUR_TREASURY_ADDRESS
https://etherscan.io/token/0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF
```

### 在后端日志查看
```bash
# 真实交易日志示例
[PAYMENT_CLIENT] Payment sent! Tx: 0xabc123...
[PAYMENT_CLIENT] 💰 Real payment: 1.00 MNEE
[PAYMENT_CLIENT] 📝 ServiceCallHash: 0x119de66f3e32cc...
[PAYMENT_CLIENT] 🔗 TX: 0xabc123def456...
```

## ⚠️ 安全注意事项

1. **永远不要提交私钥到 Git**
   ```bash
   # 确保 .env 在 .gitignore 中
   echo "backend/.env" >> .gitignore
   ```

2. **使用专用测试钱包**
   - 不要使用主钱包
   - 只存放必要的资金

3. **限制 Gas Price**
   ```python
   # 在 client.py 中设置最大 gas price
   max_gas_price = w3.to_wei('50', 'gwei')
   current_gas = w3.eth.gas_price
   gas_price = min(current_gas, max_gas_price)
   ```

4. **监控支出**
   - 定期检查 Treasury 余额
   - 设置告警阈值

## 🎬 Demo 建议

### 对于 Hackathon 提交

**推荐: Mock 模式** ✅
- 演示速度快
- 无需真实资金
- 所有逻辑完整展示
- 在视频中说明："Production-ready code with mock mode for demo"

**可选: 真实交易** 💎
- 如果想展示真实链上交易
- 准备 1-2 笔小额交易（0.1-1 MNEE）
- 在 Etherscan 上展示交易记录
- 增加项目可信度

### 混合策略（最佳）
1. **主要 Demo**: 使用 Mock 模式（快速演示所有功能）
2. **真实性证明**: 准备 1-2 笔真实交易截图
3. **在视频中说明**: 
   - "System supports real MNEE payments on Ethereum mainnet"
   - "Using mock mode for demo speed"
   - "Here's a real transaction we executed: [show Etherscan]"

## 📝 Devpost 描述建议

```markdown
## 💰 MNEE Integration

Our system is built on the official MNEE stablecoin contract:
**Contract**: `0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF` (Ethereum Mainnet)

### Payment Flow
1. Agent requests service
2. PolicyEngine + RiskEngine evaluate
3. PaymentClient calls MNEE contract
4. ServiceCallHash binds payment to service
5. Provider verifies and executes

### Demo Mode
For demonstration purposes, we use mock transactions to:
- Speed up the demo
- Avoid requiring testnet setup
- Show all features without delays

**Production Ready**: The code fully supports real MNEE payments. 
Simply configure `.env` with RPC URL and private key to enable live transactions.

### Real Transaction Example
[Optional: Include Etherscan screenshot of a real test transaction]
```

## 🔄 切换模式

### Mock → Real
```bash
# 配置 .env
PAYMENT_ROUTER_ADDRESS=0xYourDeployedRouter
TREASURY_PRIVATE_KEY=0xYourPrivateKey

# 重启后端
# 系统自动使用真实支付
```

### Real → Mock
```bash
# 清空配置
PAYMENT_ROUTER_ADDRESS=
TREASURY_PRIVATE_KEY=

# 或直接注释掉
# PAYMENT_ROUTER_ADDRESS=
# TREASURY_PRIVATE_KEY=

# 重启后端
# 系统自动回退到 Mock 模式
```

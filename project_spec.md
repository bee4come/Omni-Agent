**MNEE Nexus / Omni-Agent – 项目说明与开发任务（Coding Agent 专用 Spec）**

---

## 1. 项目总目标（What you must build）

你需要实现一个最小可用的系统，名字叫：

> **MNEE Nexus / Omni-Agent**

它是一个 **“给 AI Agent 用的支付中枢”**：

* 有一个共享的钱包（Treasury），持有 **MNEE 稳定币**；
* 多个 Agent（如 user-agent / batch-agent / ops-agent）通过你提供的后端接口发起“我要调用某个服务”的请求；
* 系统根据事先配置的 **预算 / 策略 / 优先级**：

  * 决定是否允许这次调用；
  * 决定应支付多少 MNEE；
  * 在链上调用合约用 MNEE 支付给对应服务商；
* 服务商（Service Provider）通过你定义的协议验证付款，再返回结果；
* 前端展示：

  * 对话式交互（和 Omni-Agent 聊天）；
  * 实时 MNEE 支付流水；
  * 各 Agent、各服务的消费情况；
  * 策略层的“拒绝 / 降级”决策日志。

> 这个系统不需要做到生产级，只要整个闭环“能跑起来 + 看得懂钱怎么流 + 看得见策略在发挥作用”。

---

## 2. 业务角色与对象（Actors）

你需要在代码中明确建模以下主体：

1. **Treasury（资金池地址）**

   * 这是一个持有 MNEE 的钱包（EOA 或合约）。
   * 提前对 PaymentRouter 合约做 `approve`。
   * 所有支付都从这个地址扣款。

2. **Agents（花钱的一方）**

   * `user-agent`：处理用户实时对话请求（优先级最高）。
   * `batch-agent`：处理批量计算任务（重任务，容易超预算）。
   * `ops-agent`：负责日志归档等运维行为。

3. **Service Providers（收钱 & 提供能力的一方）**
   必须至少包含四类服务商：

   * `ImageGen Provider`（IMAGE_GEN）

     * 输入：prompt
     * 输出：image URL（可以是 mock）
     * 计费：例如 1.0 MNEE / 调用
   * `PriceOracle Provider`（PRICE_ORACLE）

     * 输入：token pair（例如 ETH/MNEE）
     * 输出：价格数据（可以 mock / 固定波动）
     * 计费：例如 0.05 MNEE / 查询
   * `BatchCompute Provider`（BATCH_COMPUTE）

     * 输入：批量任务参数（比如 N 个子任务）
     * 输出：jobId + 最终结果（可以用 sleep 模拟耗时）
     * 计费：例如 3.0 MNEE / 任务
   * `LogArchive Provider`（LOG_ARCHIVE）

     * 输入：某次操作/任务的日志内容
     * 输出：归档确认信息
     * 计费：例如 0.01 MNEE / 条

4. **Omni-Agent（统筹大脑）**

   * 一个 LLM-based Agent（LangChain / 其他框架均可），
   * 能根据用户自然语言请求：

     * 决定调用哪个工具（ImageGen / PriceOracle / BatchCompute / LogArchive）；
     * 通过统一的付费包装（PaymentWrapper）发起服务调用。

---

## 3. 必须实现的功能模块（MVP Scope）

### 3.1 链上合约层（Smart Contracts）

你需要用 Solidity 实现两个最小可用合约：

#### 3.1.1 `MNEEServiceRegistry`

**职责：** 注册服务商信息。

* 记录字段：

  * `serviceId`：`bytes32`，例如 `"IMAGE_GEN"`, `"PRICE_ORACLE"` 等对应的 hash。
  * `provider`：`address`，服务商地址。
  * `unitPrice`：`uint256`，每单位服务的 MNEE 金额（按 token 最小单位）。
  * `active`：`bool`，当前服务是否可用。

**核心函数（示意）：**

* `registerService(bytes32 serviceId, address provider, uint256 unitPrice)`
* `updateService(bytes32 serviceId, address provider, uint256 unitPrice, bool active)`
* `getService(bytes32 serviceId) view returns (address provider, uint256 unitPrice, bool active)`

要求：

* 基本访问控制（简化处理：可以允许 deployer 管理）。
* 不需要复杂权限系统，只保证基本安全与正确性。

#### 3.1.2 `MNEEPaymentRouter`

**职责：**

* 从 Treasury 地址转 MNEE 到对应 Provider；
* 生成可供服务商校验的支付事件。

**假设：**

* 已知 MNEE 合约地址：
  `0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF`
* Treasury 地址对 `MNEEPaymentRouter` 做了 `approve`。

**接口示意：**

```solidity
function payForService(
    bytes32 serviceId,
    string calldata agentId,
    string calldata taskId,
    uint256 quantity
) external returns (bytes32 paymentId);
```

内部逻辑：

1. 从 `MNEEServiceRegistry` 读取服务单价 `unitPrice`。
2. 计算真实 `amount = unitPrice * quantity`。
3. 调用 MNEE 合约 `transferFrom(treasury, provider, amount)`。
4. 生成一个 `paymentId`（例如 keccak(serviceId, agentId, taskId, block.timestamp, amount)）。
5. 触发事件：

```solidity
event PaymentExecuted(
    bytes32 indexed paymentId,
    address indexed payer,
    address indexed provider,
    bytes32 serviceId,
    string agentId,
    string taskId,
    uint256 amount,
    uint256 quantity,
    uint256 timestamp
);
```

**要求：**

* 合约尽量简单，所有复杂策略不要放到链上。
* 合约需要有基本的参数检查，防止 0 地址 / 未注册 serviceId 等。

---

### 3.2 策略与支付后端（Policy + Payment Backend）

用 Python 实现一个后端服务，包含：

#### 3.2.1 Policy Engine

负责根据配置决定：

* 是否允许某 Agent 调用某 Service；
* 允许的调用次数或金额（可能比原请求少）；
* 拒绝 / 降级的原因（用于前端展示）。

**输入：**

* `agentId`（如 `"user-agent"`、`"batch-agent"`）
* `serviceId`（如 `"IMAGE_GEN_PREMIUM"`）
* `estimatedCost` 或 `quantity`
* `taskId`
* 当前状态（Treasury 余额、今日已花费用等）

**输出：**

* `action`: `"ALLOW"` / `"DENY"` / `"DOWNGRADE"`
* 可选：`approvedQuantity`
* `reason`: 字符串

**配置来源：**

用一个 JSON / YAML：

* 每个 Agent：

  ```yaml
  agents:
    - id: "user-agent"
      priority: "HIGH"
      dailyBudget: 100.0
      maxPerCall: 10.0

    - id: "batch-agent"
      priority: "LOW"
      dailyBudget: 50.0
      maxPerCall: 20.0

    - id: "ops-agent"
      priority: "MEDIUM"
      dailyBudget: 30.0
      maxPerCall: 5.0
  ```

* 每个 Service：

  ```yaml
  services:
    - id: "IMAGE_GEN_PREMIUM"
      unitPrice: 1.0
    - id: "PRICE_ORACLE"
      unitPrice: 0.05
    - id: "BATCH_COMPUTE"
      unitPrice: 3.0
    - id: "LOG_ARCHIVE"
      unitPrice: 0.01
  ```

#### 3.2.2 Payment Client

* 和以太坊节点交互（web3.py / ethers.js 均可）；
* 提供一个函数：

```python
def pay_for_service(service_id: str, agent_id: str, task_id: str, quantity: int) -> PaymentResult:
    """
    1. 调用本地 PolicyEngine 检查预算与策略，决定 ALLOW / DENY / DOWNGRADE。
    2. 若允许，调用 MNEEPaymentRouter 合约的 payForService。
    3. 监听 / 轮询交易结果，返回 paymentId / txHash。
    4. 若拒绝，返回带 reason 的错误结果。
    """
```

* 同时维护一个简单的账本（可以是内存 + 本地文件 / 简单 DB）：

  * 记录每次调用：agentId, serviceId, amount, timestamp。

#### 3.2.3 PaidToolWrapper（工具付费包装）

* 封装所有对服务商的调用：

  * 先调用 Policy Engine；
  * 再调用链上付款；
  * 然后调用对应 Provider 的 HTTP API；
  * 最后返回业务结果。

伪代码：

```python
class PaidToolWrapper:
    def __init__(self, agent_id, service_id, quantity, base_tool_func, payment_client, policy_client):
        ...

    def __call__(self, *args, **kwargs):
        task_id = generate_task_id()
        # 1. 策略检查
        decision = policy_client.check(...)
        if decision.action == "DENY":
            return {"status": "DENIED", "reason": decision.reason}

        # 2. 支付
        payment = payment_client.pay_for_service(...)
        if not payment.success:
            return {"status": "PAYMENT_FAILED", "reason": payment.error}

        # 3. 调用服务商
        result = base_tool_func(*args, task_id=task_id, **kwargs)

        # 4. 记录账本
        payment_client.record_usage(...)

        return {"status": "OK", "result": result, "paymentId": payment.payment_id}
```

---

### 3.3 Service Providers（四类服务商）

实现四个 HTTP 服务，API 可以很简单：

1. **ImageGen Provider**

   * `POST /image/generate`
   * 输入：`prompt`, `taskId`
   * 内部用于演示即可：

     * 可以始终返回同一张图片 URL 或从一个数组随机挑选。
   * 返回：

     ```json
     { "imageUrl": "https://example.com/mock_cyberpunk_avatar.png" }
     ```

2. **PriceOracle Provider**

   * `GET /price?base=ETH&quote=MNEE`
   * 可以使用写死的模拟价格，并在一定范围内随机波动。
   * 返回：

     ```json
     { "base": "ETH", "quote": "MNEE", "price": 1234.56 }
     ```

3. **BatchCompute Provider**

   * `POST /batch/submit`

     * 输入：任务参数，如 `jobSize`
     * 返回：`jobId`
   * `GET /batch/status?jobId=xxx`

     * 模拟异步：前几次 status=running，之后 status=finished + result。
   * 返回示例：

     ```json
     { "jobId": "job-123", "status": "finished", "result": "processed 20 items" }
     ```

4. **LogArchive Provider**

   * `POST /logs/archive`

     * 输入：`taskId`, `agentId`, `serviceId`, `payload`
   * 返回：

     ```json
     { "archived": true, "storageId": "log-xyz" }
     ```

> 服务商是否真的去链上验证 `PaymentExecuted` 事件，可以视时间决定：如果时间紧，可以在代码里假装校验通过；如果时间充足，可以用 web3 读取最近事件做简单验证。

---

### 3.4 前端 UI（Dashboard + Chat）

实现一个最小可用的 Web UI（推荐 Next.js / React），包含：

1. **Chat 面板**

   * 左侧：类似 ChatGPT 的对话框，用户输入自然语言请求；
   * 后端调用 Omni-Agent，Agent 内部调用各种 Paid Tool。

2. **Treasury & Spending 面板**

   * 显示：

     * 当前 Treasury 余额（可以由后端返回模拟值）；
     * 今日总支出；
     * 按 Agent 的支出汇总；
     * 按 Service 的支出汇总。

3. **Transaction Stream（实时流水）**

   * 列表展示每一笔支付：

     * 时间
     * Agent
     * Service
     * 金额
     * taskId / paymentId（简略即可）

4. **System Log / Policy Console**

   * 明确展示：

     * `[POLICY_REJECTED]` 某次请求被拒绝的条目；
     * `[POLICY_DOWNGRADED]` 某次调用被降配的条目；
   * 每条日志包含：

     * agentId
     * serviceId
     * 原始请求量 / 审核后量
     * 原因（来自 Policy Engine）

> 重点：评委/观众一眼就能看出“多 Agent 在抢预算，策略在做决策”。

---

## 4. 必须支持的典型场景（Test Scenarios）

Coding Agent 在实现完后，应确保以下场景可以跑通：

### 场景 1：生成赛博朋克头像（ImageGen）

* 用户在前端输入：

  > “帮我生成一张赛博朋克风格的 Twitter 头像。”
* 流程：

  * Omni-Agent 决定调用 ImageGen Provider。
  * PaidToolWrapper → Policy Engine（通过）→ PaymentRouter 支付 → ImageGen Provider 返回图片 URL。
* 前端表现：

  * Chat 显示图片；
  * 流水出现一条：`user-agent / IMAGE_GEN / -1.0 MNEE`。

### 场景 2：查询 ETH 价格 & 换算 MNEE（PriceOracle）

* 用户输入：

  > “现在 ETH 什么价格？100 MNEE 大约多少 ETH？”
* 流程：

  * Omni-Agent 调用 PriceOracle。
  * Policy 检查通过，支付 0.05 MNEE。
  * 返回价格，Agent 计算换算结果。
* 前端显示结果 + 流水记录。

### 场景 3：BatchCompute 被策略拒绝（Coordination）

* `batch-agent` 发起大额批量任务（例如 50 MNEE）。
* 当前 Treasury 余额不多，策略要求保留足够额度给 `user-agent`。
* Policy Engine 拒绝或将请求降至更小的数量。
* System Log 面板显示：

  ```text
  [POLICY_REJECTED] agent=batch-agent service=BATCH_COMPUTE reason="would consume reserved budget for user-agent"
  ```

### 场景 4：LogArchive 自动降级

* 模拟 Treasury 余额下降到某个阈值；
* Policy 自动把 LogArchive 从“全量日志”模式切换为“只存摘要”；
* System Log 显示：

  ```text
  [POLICY_DOWNGRADED] service=LOG_ARCHIVE mode=SUMMARY_ONLY reason="low treasury balance"
  ```

---

## 5. 非功能性要求（Non-functional Requirements）

Coding Agent 实现时应遵守：

1. **结构清晰**

   * 合约、后端、providers、前端分目录存放；
   * 有基础 README / 注释说明关键模块。

2. **可本地运行**

   * 可以只用本地链（Hardhat / Anvil），不强制连公共测试网；
   * 有基本启动命令（例如 `npm run dev`, `uvicorn app.main:app --reload` 等）。

3. **可扩展**

   * 当需要增加新服务商时：

     * 只需在 ServiceRegistry 注册；
     * 在配置文件中增加 service；
     * 实现一个新的 Provider + Tool 即可。

4. **尽量避免过度复杂度**

   * 智能合约保持极简；
   * 复杂策略逻辑全部放在后端 Policy Engine 中实现。


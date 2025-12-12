# Frontend Design Prompt for Gemini

## Project Overview

You are building the frontend for **MNEE Agent Cost & Billing Hub** - a financial operating system for AI agent teams.

**Core Problem**: Teams with multiple AI agents calling expensive APIs have no centralized budget control, leading to runaway spending and zero accountability.

**Solution**: Real-time dashboard showing project/agent budgets, policy enforcement decisions, and complete transaction audit trail.

---

## Tech Stack

**Required:**
- Next.js 14+ (App Router or Pages Router)
- React 18+
- TypeScript
- TailwindCSS
- Axios for API calls

**Optional but Recommended:**
- Recharts or Chart.js for visualizations
- Framer Motion for animations
- Lucide React for icons

---

## Backend API Reference

**Base URL**: `http://localhost:8000`

### Main Endpoints

```typescript
// 1. Chat with agent (executes task with budget enforcement)
POST /chat
Request: { agent_id: string, message: string }
Response: {
  response: string,
  agent_id: string,
  task_id: string,
  steps: StepRecord[]
}

// 2. Get treasury status
GET /treasury
Response: {
  agents: Record<string, AgentInfo>,
  totalAllocated: number,
  totalSpent: number
}

// 3. Get all agents
GET /agents
Response: {
  agents: AgentInfo[]
}

// 4. Get agent details
GET /agents/{agent_id}
Response: {
  id: string,
  priority: "HIGH" | "MEDIUM" | "LOW",
  dailyBudget: number,
  maxPerCall: number,
  currentDailySpend: number,
  remainingBudget: number,
  transactions: Transaction[]
}

// 5. Get recent transactions
GET /transactions?limit=20
Response: {
  transactions: Transaction[]
}

// 6. Get policy decision logs
GET /policy/logs?limit=20
Response: {
  logs: PolicyLog[]
}

// 7. Get system statistics
GET /stats
Response: {
  transactions: { total: number, successful: number, failed: number },
  policyActions: Record<string, number>,
  totalAllocatedBudget: number,
  totalSpent: number
}
```

### Data Types

```typescript
interface StepRecord {
  step_id: string
  agent_id: string
  service_id: string
  tool_name: string
  input_params: Record<string, any>
  output: any
  payment_id?: string
  tx_hash?: string
  amount_mnee?: number
  policy_action?: "ALLOW" | "DENY" | "DOWNGRADE"
  risk_level?: "RISK_OK" | "RISK_REVIEW" | "RISK_BLOCK"
  status: "pending" | "executing" | "success" | "failed" | "denied"
  error?: string
}

interface AgentInfo {
  id: string
  priority: "HIGH" | "MEDIUM" | "LOW"
  dailyBudget: number
  maxPerCall: number
  currentDailySpend: number
  remainingBudget: number
}

interface Transaction {
  agent_id: string
  service_id: string
  task_id: string
  amount: number
  tx_hash: string
  status: "PENDING" | "SUCCESS" | "FAILED"
  timestamp: string
}

interface PolicyLog {
  timestamp: string
  agent_id: string
  service_id: string
  action: "ALLOW" | "DENY" | "DOWNGRADE"
  reason: string
  cost: number
  risk_level: string
}
```

---

## UI Design Requirements

### Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│ Header: MNEE Agent Cost & Billing Hub                  │
│ [Treasury Status] [Active Agents] [System Health]      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Left Panel (40%)        │  Right Panel (60%)          │
│                          │                              │
│  [Chat Interface]        │  [Live Execution View]      │
│  - Input box             │  - Current task graph       │
│  - Message history       │  - Step-by-step timeline    │
│  - Agent selector        │                              │
│                          │  [Audit Log]                │
│                          │  - Recent transactions      │
│                          │  - Policy decisions         │
│                          │  - Budget alerts            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Key Components to Build

#### 1. Dashboard Overview (Home Page)

**Purpose**: High-level view of system health and spending

**Sections**:

A. **Treasury Card**
   - Total allocated budget
   - Total spent today
   - Remaining budget
   - Visual progress bar

B. **Agent Fleet Grid**
   - Cards for each agent showing:
     - Agent ID + priority badge (HIGH/MEDIUM/LOW)
     - Budget: spent / total (with color coding)
     - Progress bar
     - Transaction count today
   - Color coding:
     - Green: <50% used
     - Yellow: 50-80% used
     - Red: >80% used

C. **Spending Chart**
   - Line chart showing hourly spending over last 24h
   - Breakdown by agent (different colored lines)

D. **Top Services**
   - Bar chart of most expensive services
   - Shows total MNEE spent per service

#### 2. Chat Interface

**Purpose**: Send commands to agents, see real-time execution

**Features**:

A. **Agent Selector**
   - Dropdown to choose which agent to use
   - Show agent's remaining budget next to name

B. **Message Input**
   - Text area for natural language commands
   - Example prompts:
     - "Generate a marketing logo"
     - "Check ETH price"
     - "Analyze our spending this week"

C. **Message History**
   - User messages (right-aligned, blue)
   - Agent responses (left-aligned, gray)
   - Show budget impact: "Cost: 1.5 MNEE"

D. **Quick Actions**
   - Preset buttons:
     - "Check Budget Status"
     - "List Recent Transactions"
     - "Generate Report"

#### 3. Live Execution View

**Purpose**: Show what the agent is doing right now

**Real-time Flow Visualization**:

```
[Planner] → [Guardian] → [Executor] → [Provider]
   ↓            ↓            ↓            ↓
 Planning    Checking     Paying      Delivering
              Budget
```

**Implementation**:
- Horizontal timeline with 4 nodes
- Highlight current step with animated pulse
- Show status:
  - Gray: pending
  - Blue: in progress
  - Green: success
  - Red: failed/denied

**Step Details Panel**:
- When step completes, show expandable card:
  - Service called
  - Cost (MNEE)
  - Policy decision (ALLOW/DENY with reason)
  - Transaction hash (if paid)
  - Output preview

#### 4. Audit Log

**Purpose**: Real-time feed of all policy decisions and transactions

**Design**:

- Reverse chronological list
- Each entry is a card with:
  - Timestamp
  - Agent ID badge
  - Service called
  - Action badge (ALLOW/DENY/DOWNGRADE)
  - Risk level indicator
  - Amount (if paid)
  - Expandable details

**Visual Indicators**:
- ALLOW: Green checkmark
- DENY: Red X
- DOWNGRADE: Yellow warning triangle

**Filters**:
- By agent
- By action (ALLOW/DENY/DOWNGRADE)
- By risk level
- By date range

#### 5. Budget Management Page

**Purpose**: Detailed budget configuration and monitoring

**Sections**:

A. **Project Overview**
   - Card for default project showing:
     - Total daily budget
     - Current spending
     - Number of agents
     - Allowed/blocked services

B. **Agent Budget Table**
   - Sortable table with columns:
     - Agent ID
     - Priority
     - Daily Budget
     - Spent Today
     - Remaining
     - Max Per Call
     - Actions (Edit button)

C. **Budget Alert Settings**
   - Set thresholds for notifications:
     - Warning at 75% budget
     - Critical at 90% budget

D. **Service Allowlist**
   - Table of services:
     - Service ID
     - Unit Price
     - Status (Active/Inactive)
     - Toggle to enable/disable

#### 6. Transaction History Page

**Purpose**: Detailed transaction explorer

**Features**:

A. **Filter Bar**
   - Date range picker
   - Agent filter (multi-select)
   - Service filter (multi-select)
   - Status filter (Success/Failed/Pending)

B. **Transaction Table**
   - Columns:
     - Timestamp
     - Agent ID
     - Service ID
     - Amount (MNEE)
     - Status badge
     - TX Hash (truncated, copyable)
     - Actions (View Details)

C. **Transaction Detail Modal**
   - Full transaction info:
     - Complete step record
     - Policy decision
     - Risk assessment
     - Blockchain transaction link
     - Service response data

D. **Export Button**
   - Download as CSV for accounting

---

## Color Scheme & Design System

### Colors

```css
/* Background */
--bg-primary: #0B0E14;
--bg-secondary: #0F1219;
--bg-tertiary: #1A1F2E;

/* Text */
--text-primary: #E2E8F0;
--text-secondary: #94A3B8;
--text-muted: #64748B;

/* Accent */
--accent-primary: #6366F1;   /* Indigo */
--accent-success: #10B981;   /* Green */
--accent-warning: #F59E0B;   /* Yellow */
--accent-danger: #EF4444;    /* Red */

/* Status */
--status-allowed: #10B981;
--status-denied: #EF4444;
--status-downgrade: #F59E0B;
--status-risk-ok: #10B981;
--status-risk-review: #F59E0B;
--status-risk-block: #EF4444;
```

### Typography

```css
/* Fonts */
--font-sans: 'Inter', system-ui, sans-serif;
--font-mono: 'Fira Code', 'Courier New', monospace;

/* Sizes */
--text-xs: 0.75rem;
--text-sm: 0.875rem;
--text-base: 1rem;
--text-lg: 1.125rem;
--text-xl: 1.25rem;
--text-2xl: 1.5rem;
```

---

## Key Features & Interactions

### 1. Real-Time Updates

Implement polling (every 2 seconds) for:
- Treasury status
- Active transactions
- Policy logs

Use React Query or SWR for efficient data fetching.

### 2. Budget Warnings

Show toasts/notifications when:
- Agent reaches 75% of daily budget (yellow)
- Agent reaches 90% of daily budget (orange)
- Agent hits budget limit (red)
- Any DENY action from policy engine

### 3. Responsive Design

- Desktop (1920x1080): Full layout with panels
- Tablet (768-1024px): Stack panels vertically
- Mobile (< 768px): Simplified single-column layout

### 4. Loading States

- Skeleton screens for data loading
- Spinner for chat responses
- Progress indicators for long operations

### 5. Error Handling

- Toast notifications for API errors
- Fallback UI for failed requests
- Retry buttons

---

## Implementation Checklist

### Phase 1: Core Structure (2-3 hours)
- [ ] Setup Next.js project with TypeScript
- [ ] Configure TailwindCSS
- [ ] Create layout component (header, sidebar)
- [ ] Setup Axios instance with base URL
- [ ] Create API service layer

### Phase 2: Dashboard (2-3 hours)
- [ ] Treasury status card
- [ ] Agent fleet grid
- [ ] Spending chart component
- [ ] Top services component
- [ ] Connect to real API endpoints

### Phase 3: Chat Interface (2-3 hours)
- [ ] Chat message component
- [ ] Message input with agent selector
- [ ] POST /chat integration
- [ ] Message history rendering
- [ ] Cost display per message

### Phase 4: Live Execution (2-3 hours)
- [ ] Flow visualization component
- [ ] Step timeline with status
- [ ] Step detail cards
- [ ] Real-time status updates

### Phase 5: Audit Log (1-2 hours)
- [ ] Log entry component
- [ ] Filtering controls
- [ ] GET /policy/logs integration
- [ ] Auto-refresh

### Phase 6: Budget Management (2-3 hours)
- [ ] Agent budget table
- [ ] Edit agent budget form
- [ ] PUT /agents/{id}/budget integration
- [ ] Service allowlist management

### Phase 7: Transaction History (2-3 hours)
- [ ] Transaction table with filters
- [ ] Transaction detail modal
- [ ] GET /transactions integration
- [ ] CSV export functionality

### Phase 8: Polish (2-3 hours)
- [ ] Add loading states
- [ ] Add error boundaries
- [ ] Implement toasts/notifications
- [ ] Responsive design tweaks
- [ ] Dark mode optimization

---

## Sample Code Snippets

### API Service Layer

```typescript
// lib/api.ts
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
})

export const apiService = {
  chat: (agent_id: string, message: string) =>
    api.post('/chat', { agent_id, message }),

  getTreasury: () => api.get('/treasury'),

  getAgents: () => api.get('/agents'),

  getAgent: (agent_id: string) => api.get(`/agents/${agent_id}`),

  getTransactions: (limit = 20) =>
    api.get(`/transactions?limit=${limit}`),

  getPolicyLogs: (limit = 20) =>
    api.get(`/policy/logs?limit=${limit}`),

  getStats: () => api.get('/stats')
}
```

### Budget Progress Component

```tsx
// components/BudgetProgress.tsx
interface BudgetProgressProps {
  spent: number
  total: number
  agentId: string
}

export function BudgetProgress({ spent, total, agentId }: BudgetProgressProps) {
  const percentage = (spent / total) * 100
  const color =
    percentage < 50 ? 'bg-green-500' :
    percentage < 80 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">{agentId}</span>
        <span className="text-slate-200 font-mono">
          {spent.toFixed(2)} / {total.toFixed(2)} MNEE
        </span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} transition-all duration-500`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  )
}
```

### Status Badge Component

```tsx
// components/StatusBadge.tsx
interface StatusBadgeProps {
  action: "ALLOW" | "DENY" | "DOWNGRADE"
}

export function StatusBadge({ action }: StatusBadgeProps) {
  const styles = {
    ALLOW: 'bg-green-500/10 text-green-400 border-green-500/20',
    DENY: 'bg-red-500/10 text-red-400 border-red-500/20',
    DOWNGRADE: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
  }

  const icons = {
    ALLOW: '✓',
    DENY: '✗',
    DOWNGRADE: '⚠'
  }

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium border ${styles[action]}`}>
      {icons[action]} {action}
    </span>
  )
}
```

---

## Testing Requirements

### Manual Testing Checklist

1. **Chat Flow**
   - [ ] Send message "Generate a logo"
   - [ ] Verify execution timeline appears
   - [ ] Check policy decision in audit log
   - [ ] Confirm transaction appears in history

2. **Budget Enforcement**
   - [ ] Use agent until 90% budget
   - [ ] Verify warning notification
   - [ ] Use agent past 100% budget
   - [ ] Confirm DENY appears in audit log

3. **Real-Time Updates**
   - [ ] Send chat message
   - [ ] Watch audit log update automatically
   - [ ] Check treasury balance decrements

---

## Deliverables

1. **Complete Next.js project** with all components
2. **README.md** with setup instructions
3. **Environment config** (.env.example)
4. **API integration** fully working
5. **Responsive design** tested on desktop/tablet/mobile

---

## Tips for Implementation

1. **Start Simple**: Build dashboard first, then add chat, then audit log
2. **Use TypeScript**: Strongly type all API responses
3. **Component Reuse**: Create shared components for badges, cards, progress bars
4. **Mock Data First**: Test UI with hardcoded data, then connect real API
5. **Test Each Feature**: Verify each component works before moving to next

---

## Questions to Clarify

Before starting, confirm:
- Should use Next.js App Router or Pages Router?
- Any specific charting library preference?
- Need dark mode toggle or always dark?
- Should include user authentication (future)?

---

Good luck! Build a clean, functional, and professional frontend that makes budget monitoring intuitive and actionable.

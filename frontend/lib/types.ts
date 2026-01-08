export interface AgentStatus {
  id: string;
  priority: string;
  dailyBudget: number;
  maxPerCall: number;
  currentDailySpend: number;
  remainingBudget: number;
  paused?: boolean;
}

export interface StepRecord {
  step_id: string;
  agent_id: string;
  project_id?: string;
  service_id?: string;
  tool_name?: string;
  status: string;
  amount_mnee?: number;
  tx_hash?: string;
  error?: string;
}

export interface GuardianAudit {
  reasoning: string;
  risk_score: number;
  blocked: boolean;
}

export interface A2ATransfer {
  from_agent: string;
  to_agent: string;
  amount: number;
  task_description: string;
  tx_hash?: string;
  success: boolean;
}

export type EscrowStatus = 'created' | 'submitted' | 'verifying' | 'released' | 'refunded' | 'disputed';

export interface EscrowRecord {
  escrow_id: string;
  task_id: string;
  customer_agent: string;
  merchant_agent: string;
  amount: number;
  fee: number;
  status: EscrowStatus;
  created_at?: string;
  submitted_at?: string;
  verified_at?: string;
  released_at?: string;
  verification_score?: number;
  verification_passed?: boolean;
  lock_tx_hash?: string;
  release_tx_hash?: string;
  dispute_reason?: string;
}

export interface ChatResponse {
  response: string;
  agent_id: string;
  steps: StepRecord[];
  a2a_transfers?: A2ATransfer[];
  escrow_records?: EscrowRecord[];
  guardian: GuardianAudit;
}

export interface Transaction {
  timestamp: string;
  agent_id: string;
  service_id: string;
  amount: number;
  status: string;
  tx_hash?: string;
}

export interface PolicyLog {
  timestamp: string;
  agent_id: string;
  service_id: string;
  action: string;
  reason: string;
  risk_level: string;
  cost?: number;
}

export interface Stats {
  totalAllocatedBudget: number;
  totalSpent: number;
  transactions: {
    total: number;
    successful: number;
    failed: number;
  };
  agentCount: number;
  serviceCount?: number;
  policyActions?: Record<string, number>;
}

// Treasury state from API
export interface TreasuryAgent {
  id: string;
  priority: string;
  dailyBudget: number;
  maxPerCall: number;
  currentDailySpend: number;
  remainingBudget: number;
  paused?: boolean;
}

export interface Treasury {
  totalAllocated: number;
  totalSpent: number;
  agents: Record<string, TreasuryAgent>;
}

// Simplified Escrow from API (matches mockData and backend response)
export interface EscrowSimple {
  escrow_id: string;
  payer_agent_id: string;
  payee_agent_id: string;
  amount: number;
  status: string;
  task_description: string;
  created_at?: string;
}

// Workflow types for multi-agent collaboration
export type WorkflowStepStatusType = 'pending' | 'running' | 'completed' | 'failed';

export interface WorkflowStepDef {
  step_id: string;
  role: string;
  agent_id: string;
  capability: string;
  estimated_cost: number;
  depends_on: string[];
}

export interface WorkflowTemplate {
  workflow_id: string;
  name: string;
  description: string;
  total_cost: number;
  step_count: number;
  steps: WorkflowStepDef[];
}

// Agent bid information for coordination visualization
export interface AgentBid {
  agent_id: string;
  agent_name: string;
  price: number;
  estimated_time: number;
  reputation_score: number;
  success_rate: number;
  total_tasks: number;
  current_load: number;
  capability_match: boolean;
  score: number;
  score_breakdown: {
    price_score: number;
    reputation_score: number;
    success_score: number;
  };
}

export interface BidInfo {
  capability: string;
  bids: AgentBid[];
  selected_agent: string | null;
  selection_reason: string;
  weights?: {
    price: number;
    reputation: number;
    success: number;
  };
}

export interface WorkflowStepStatus {
  step_id: string;
  role: string;
  agent_id: string;
  status: WorkflowStepStatusType;
  cost: number;
  escrow_id?: string;
  escrow_status?: string;
  tx_hash?: string;
  selection_reason?: string;
  bid_info?: BidInfo;
  output_data?: Record<string, unknown>;
  started_at?: string;
  completed_at?: string;
}

export interface WorkflowInstance {
  instance_id: string;
  workflow_id: string;
  name: string;
  customer_agent: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  current_step_index: number;
  total_steps: number;
  progress_percent: number;
  total_cost: number;
  spent_so_far: number;
  created_at: string;
  completed_at?: string;
  steps: WorkflowStepStatus[];
  escrow_ids: string[];
}

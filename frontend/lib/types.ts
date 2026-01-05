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

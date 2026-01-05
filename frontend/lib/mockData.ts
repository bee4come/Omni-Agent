/**
 * Mock data for demo mode when backend is unavailable.
 * Enable by setting NEXT_PUBLIC_DEMO_MODE=true
 */

export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === 'true';

export const mockTreasury = {
  totalAllocated: 205.0,
  totalSpent: 47.35,
  agents: {
    'user-agent': {
      id: 'user-agent',
      priority: 'HIGH',
      dailyBudget: 100.0,
      maxPerCall: 50.0,
      currentDailySpend: 23.5,
      remainingBudget: 76.5,
    },
    'startup-designer': {
      id: 'startup-designer',
      priority: 'MEDIUM',
      dailyBudget: 50.0,
      maxPerCall: 5.0,
      currentDailySpend: 12.0,
      remainingBudget: 38.0,
    },
    'startup-analyst': {
      id: 'startup-analyst',
      priority: 'MEDIUM',
      dailyBudget: 50.0,
      maxPerCall: 10.0,
      currentDailySpend: 9.85,
      remainingBudget: 40.15,
    },
    'startup-archivist': {
      id: 'startup-archivist',
      priority: 'LOW',
      dailyBudget: 5.0,
      maxPerCall: 0.5,
      currentDailySpend: 2.0,
      remainingBudget: 3.0,
    },
  },
};

export const mockAgents = [
  {
    id: 'user-agent',
    priority: 'HIGH',
    dailyBudget: 100.0,
    maxPerCall: 50.0,
    currentDailySpend: 23.5,
  },
  {
    id: 'startup-designer',
    priority: 'MEDIUM',
    dailyBudget: 50.0,
    maxPerCall: 5.0,
    currentDailySpend: 12.0,
  },
  {
    id: 'startup-analyst',
    priority: 'MEDIUM',
    dailyBudget: 50.0,
    maxPerCall: 10.0,
    currentDailySpend: 9.85,
  },
  {
    id: 'startup-archivist',
    priority: 'LOW',
    dailyBudget: 5.0,
    maxPerCall: 0.5,
    currentDailySpend: 2.0,
  },
];

export const mockTransactions = [
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
    agent_id: 'user-agent',
    service_id: 'IMAGE_GEN_PREMIUM',
    task_id: 'task-001',
    amount: 1.0,
    tx_hash: '0x1a2b3c4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890',
    status: 'SUCCESS',
  },
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    agent_id: 'startup-designer',
    service_id: 'IMAGE_GEN_PREMIUM',
    task_id: 'task-002',
    amount: 1.0,
    tx_hash: '0x2b3c4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890ab',
    status: 'SUCCESS',
  },
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
    agent_id: 'startup-analyst',
    service_id: 'BATCH_COMPUTE',
    task_id: 'task-003',
    amount: 3.0,
    tx_hash: '0x3c4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890abcd',
    status: 'SUCCESS',
  },
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    agent_id: 'startup-archivist',
    service_id: 'LOG_ARCHIVE',
    task_id: 'task-004',
    amount: 0.05,
    tx_hash: '0x4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    status: 'SUCCESS',
  },
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 20).toISOString(),
    agent_id: 'user-agent',
    service_id: 'PRICE_ORACLE',
    task_id: 'task-005',
    amount: 0.05,
    tx_hash: '0x5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890abcdef12',
    status: 'SUCCESS',
  },
];

export const mockStats = {
  transactions: {
    total: 156,
    successful: 149,
    failed: 7,
  },
  policyActions: {
    ALLOW: 149,
    DENY: 12,
    DOWNGRADE: 3,
  },
  totalAllocatedBudget: 205.0,
  totalSpent: 47.35,
  serviceCount: 4,
  agentCount: 4,
};

export const mockEscrows = [
  {
    escrow_id: 'escrow-001',
    payer_agent_id: 'startup-designer',
    payee_agent_id: 'startup-analyst',
    amount: 10.0,
    status: 'released',
    task_description: 'Market research analysis',
    created_at: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
  },
  {
    escrow_id: 'escrow-002',
    payer_agent_id: 'user-agent',
    payee_agent_id: 'startup-designer',
    amount: 15.0,
    status: 'verifying',
    task_description: 'Logo design for PayFlow',
    created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
  },
  {
    escrow_id: 'escrow-003',
    payer_agent_id: 'startup-analyst',
    payee_agent_id: 'startup-archivist',
    amount: 2.0,
    status: 'created',
    task_description: 'Archive analysis reports',
    created_at: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
  },
];

export const mockPolicyLogs = [
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 1).toISOString(),
    agent_id: 'user-agent',
    service_id: 'IMAGE_GEN_PREMIUM',
    action: 'ALLOW',
    reason: 'Within budget limits',
    cost: 1.0,
    risk_level: 'RISK_OK',
  },
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 3).toISOString(),
    agent_id: 'startup-archivist',
    service_id: 'BATCH_COMPUTE',
    action: 'DENY',
    reason: 'Exceeds single call limit (0.5 MNEE)',
    cost: 3.0,
    risk_level: 'RISK_BLOCK',
  },
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    agent_id: 'startup-designer',
    service_id: 'IMAGE_GEN_PREMIUM',
    action: 'ALLOW',
    reason: 'Within budget limits',
    cost: 1.0,
    risk_level: 'RISK_OK',
  },
  {
    timestamp: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
    agent_id: 'startup-analyst',
    service_id: 'BATCH_COMPUTE',
    action: 'ALLOW',
    reason: 'Within budget limits',
    cost: 3.0,
    risk_level: 'RISK_REVIEW',
  },
];

/**
 * Helper to simulate API delay in demo mode
 */
export function simulateDelay(ms: number = 300): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Get mock data with simulated delay
 */
export async function getMockData<T>(data: T, delayMs: number = 300): Promise<T> {
  await simulateDelay(delayMs);
  return data;
}

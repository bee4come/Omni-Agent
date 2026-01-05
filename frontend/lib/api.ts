import axios, { AxiosError, AxiosRequestConfig } from 'axios';
import {
  DEMO_MODE,
  mockTreasury,
  mockAgents,
  mockTransactions,
  mockStats,
  mockEscrows,
  mockPolicyLogs,
  getMockData,
} from './mockData';

// Environment-based API configuration
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// Check if demo mode is enabled
export const isDemoMode = () => DEMO_MODE;

// Retry logic with exponential backoff
async function withRetry<T>(
  fn: () => Promise<T>,
  retries: number = MAX_RETRIES,
  delay: number = RETRY_DELAY
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    const axiosError = error as AxiosError;

    // Don't retry on client errors (4xx) except 429 (rate limit)
    if (axiosError.response?.status &&
        axiosError.response.status >= 400 &&
        axiosError.response.status < 500 &&
        axiosError.response.status !== 429) {
      throw error;
    }

    if (retries > 0) {
      await new Promise(resolve => setTimeout(resolve, delay));
      return withRetry(fn, retries - 1, delay * 2);
    }
    throw error;
  }
}

// API error handler
export function handleApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response) {
      const detail = error.response.data?.detail;
      if (detail) return detail;
      return `Server error: ${error.response.status}`;
    }
    if (error.request) {
      return 'Network error: Unable to reach the server';
    }
  }
  return 'An unexpected error occurred';
}

// Core API functions with retry and demo mode fallback
export const fetchTreasury = () => {
  if (DEMO_MODE) return getMockData(mockTreasury);
  return withRetry(async () => (await api.get('/treasury')).data);
};

export const fetchAgents = () => {
  if (DEMO_MODE) return getMockData({ agents: mockAgents });
  return withRetry(async () => (await api.get('/agents')).data);
};

export const fetchTransactions = () => {
  if (DEMO_MODE) return getMockData({ transactions: mockTransactions });
  return withRetry(async () => (await api.get('/transactions')).data);
};

export const fetchPolicyLogs = () => {
  if (DEMO_MODE) return getMockData({ logs: mockPolicyLogs });
  return withRetry(async () => (await api.get('/policy/logs')).data);
};

export const fetchStats = () => {
  if (DEMO_MODE) return getMockData(mockStats);
  return withRetry(async () => (await api.get('/stats')).data);
};

// A2A API functions
export const fetchA2ATransfers = () => withRetry(async () => (await api.get('/a2a/transfers')).data);
export const fetchA2ABalances = () => withRetry(async () => (await api.get('/a2a/balances')).data);
export const executeA2APayment = (fromAgent: string, toAgent: string, amount: number, taskDescription: string) =>
  withRetry(async () => (await api.post('/a2a/pay', { from_agent: fromAgent, to_agent: toAgent, amount, task_description: taskDescription })).data);

// Escrow API functions
export const fetchEscrows = () => {
  if (DEMO_MODE) return getMockData({ escrows: mockEscrows });
  return withRetry(async () => (await api.get('/escrow/list')).data);
};

export const fetchEscrow = (escrowId: string) => {
  if (DEMO_MODE) {
    const escrow = mockEscrows.find(e => e.escrow_id === escrowId);
    return getMockData(escrow || null);
  }
  return withRetry(async () => (await api.get(`/escrow/${escrowId}`)).data);
};
export const raiseDispute = (escrowId: string, reason: string) =>
  withRetry(async () => (await api.post(`/escrow/${escrowId}/dispute`, { reason })).data);

// Registry API functions
export const fetchRegistryAgents = () => withRetry(async () => (await api.get('/registry/agents')).data);
export const findAgentsByCapability = (capability: string) =>
  withRetry(async () => (await api.get(`/registry/find?capability=${encodeURIComponent(capability)}`)).data);

// Agent management
export const updateAgentBudget = async (agentId: string, dailyBudget: number) => {
  return (await api.put(`/agents/${encodeURIComponent(agentId)}/budget`, { daily_budget: dailyBudget })).data;
};

export const pauseAgent = async (agentId: string) => {
  return (await api.put(`/agents/${encodeURIComponent(agentId)}/pause`)).data;
};

export const resumeAgent = async (agentId: string) => {
  return (await api.put(`/agents/${encodeURIComponent(agentId)}/resume`)).data;
};

// Chat command (no retry for user actions - show error immediately)
export const sendCommand = async (agentId: string, message: string) => {
  return (await api.post('/chat', { agent_id: agentId, message })).data;
};

// Health check
export const checkHealth = async (): Promise<boolean> => {
  try {
    await api.get('/');
    return true;
  } catch {
    return false;
  }
};

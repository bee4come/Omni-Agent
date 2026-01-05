import React, { useState, useEffect, useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import { AppShell } from '../components/AppShell';
import { AgentFleet } from '../components/AgentFleet';
import { LiveOps } from '../components/LiveOps';
import { Ledger } from '../components/Ledger';
import { StatsCards } from '../components/StatsCards';
import { SpendingChart } from '../components/SpendingChart';
import { PolicyLogs } from '../components/PolicyLogs';
import { BudgetAlertsContainer } from '../components/BudgetAlert';
import { A2ANetwork } from '../components/A2ANetwork';
import { EscrowManager } from '../components/EscrowManager';
import { OnboardingModal, useOnboarding } from '../components/OnboardingModal';
import { StatsCardsSkeleton, AgentCardSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import { fetchTreasury, fetchAgents, fetchTransactions, fetchStats, fetchEscrows, handleApiError } from '../lib/api';
import { useWebSocket } from '../lib/useWebSocket';
import { AgentStatus, Transaction, Stats, Treasury, EscrowSimple } from '../lib/types';

export default function Home() {
  const [tab, setTab] = useState('overview');
  const [treasury, setTreasury] = useState<Treasury | null>(null);
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [escrows, setEscrows] = useState<EscrowSimple[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { showOnboarding, completeOnboarding } = useOnboarding();

  // WebSocket connection for real-time updates
  const { data: wsData, status: wsStatus, isConnected, refresh: wsRefresh } = useWebSocket({
    enabled: true,
    onEvent: (eventType, data) => {
      // Handle real-time events (e.g., new transaction, budget alert)
      if (eventType === 'transaction') {
        toast.success(`New transaction: ${data?.amount} MNEE`);
      } else if (eventType === 'budget_alert') {
        toast.error(`Budget alert: ${data?.message}`);
      }
    },
  });

  // Track if we've received WebSocket data
  const hasWsData = useRef(false);

  // Update state from WebSocket data
  useEffect(() => {
    if (wsData) {
      hasWsData.current = true;
      setTreasury(wsData.treasury);
      setAgents(wsData.agents || []);
      setTransactions(wsData.transactions || []);
      setStats(wsData.stats);
      setEscrows(wsData.escrows || []);
      setLoading(false);
    }
  }, [wsData]);

  // Fallback to polling if WebSocket is not connected
  const loadData = useCallback(async (showToast = false) => {
    try {
      const [t, a, tx, s, e] = await Promise.all([
        fetchTreasury(),
        fetchAgents(),
        fetchTransactions(),
        fetchStats(),
        fetchEscrows().catch(() => ({ escrows: [] }))
      ]);

      setTreasury(t);
      setAgents(a.agents || []);
      setTransactions(tx.transactions || []);
      setStats(s);
      setEscrows(e.escrows || []);

      if (showToast) {
        toast.success('Data refreshed successfully');
      }
    } catch (error) {
      console.error(error);
      if (showToast) {
        toast.error(handleApiError(error));
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    if (isConnected) {
      wsRefresh();
      setTimeout(() => setRefreshing(false), 500);
    } else {
      loadData(true);
    }
  }, [loadData, isConnected, wsRefresh]);

  // Initial load and fallback polling when WebSocket is not connected
  useEffect(() => {
    // Initial load via API
    loadData();

    // Only poll if WebSocket is not connected after initial delay
    const pollInterval = setInterval(() => {
      if (!isConnected && !hasWsData.current) {
        loadData(false);
      }
    }, 5000); // Slower polling as fallback (5s instead of 3s)

    return () => clearInterval(pollInterval);
  }, [loadData, isConnected]);

  // Check for budget alerts
  useEffect(() => {
    agents.forEach(agent => {
      const percentage = (agent.currentDailySpend / agent.dailyBudget) * 100;
      if (percentage >= 90 && percentage < 100) {
        toast.error(`⚠️ ${agent.id} is at ${percentage.toFixed(0)}% budget!`, {
          id: `budget-alert-${agent.id}`,
        });
      }
    });
  }, [agents]);

  const treasuryBalance = (treasury?.totalAllocated ?? 0) - (treasury?.totalSpent ?? 0);

  return (
    <AppShell
      activeTab={tab}
      setActiveTab={setTab}
      treasuryBalance={treasuryBalance}
      onRefresh={handleRefresh}
      loading={refreshing}
      connectionStatus={wsStatus}
    >
      {/* Overview Tab */}
      {tab === 'overview' && (
        <div className="space-y-8">
          {/* Budget Alerts */}
          <BudgetAlertsContainer agents={agents} />

          {/* Stats Cards */}
          {loading ? (
            <StatsCardsSkeleton />
          ) : (
            <StatsCards
              totalAllocated={treasury?.totalAllocated || 0}
              totalSpent={treasury?.totalSpent || 0}
              agentCount={stats?.agentCount || agents.length}
              transactionStats={stats?.transactions || { total: 0, successful: 0, failed: 0 }}
              policyActions={stats?.policyActions}
            />
          )}

          {/* Charts */}
          <SpendingChart transactions={transactions} agents={agents} />

          {/* Fleet Status */}
          <div>
            <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">Fleet Status</h3>
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map(i => <AgentCardSkeleton key={i} />)}
              </div>
            ) : (
              <AgentFleet agents={agents} />
            )}
          </div>

          {/* Recent Activity Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">Recent Transactions</h3>
              {loading ? <TableSkeleton rows={3} /> : <Ledger transactions={transactions.slice(0, 5)} />}
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-500 uppercase tracking-wider mb-4">Policy Decisions</h3>
              <PolicyLogs compact />
            </div>
          </div>
        </div>
      )}

      {/* Fleet Tab */}
      {tab === 'fleet' && (
        <div className="space-y-6">
          <BudgetAlertsContainer agents={agents} />
          <AgentFleet agents={agents} />
        </div>
      )}

      {/* Live Ops Tab */}
      {tab === 'ops' && (
        <LiveOps onAction={loadData} />
      )}

      {/* Ledger Tab */}
      {tab === 'ledger' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-200">Transaction History</h2>
            <div className="text-sm text-slate-500">
              {transactions.length} transactions
            </div>
          </div>
          {loading ? <TableSkeleton rows={10} /> : <Ledger transactions={transactions} />}
        </div>
      )}

      {/* A2A Network Tab */}
      {tab === 'a2a' && (
        <A2ANetwork />
      )}

      {/* Escrow Manager Tab */}
      {tab === 'escrow' && (
        <EscrowManager escrows={escrows} onRefresh={handleRefresh} />
      )}

      {/* Policy Logs Tab */}
      {tab === 'policy' && (
        <div className="space-y-6">
          <h2 className="text-lg font-bold text-slate-200">Policy Audit Log</h2>
          <PolicyLogs />
        </div>
      )}

      {/* Onboarding Modal for first-time users */}
      {showOnboarding && (
        <OnboardingModal onComplete={completeOnboarding} />
      )}
    </AppShell>
  );
}

import React, { useState, useEffect, useCallback } from 'react';
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
import { StatsCardsSkeleton, AgentCardSkeleton, TableSkeleton } from '../components/LoadingSkeleton';
import { fetchTreasury, fetchAgents, fetchTransactions, fetchStats } from '../lib/api';
import { AgentStatus, Transaction, Stats } from '../lib/types';

export default function Home() {
  const [tab, setTab] = useState('overview');
  const [treasury, setTreasury] = useState<any>(null);
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  const loadData = useCallback(async (showToast = false) => {
    try {
      const [t, a, tx, s] = await Promise.all([
        fetchTreasury(),
        fetchAgents(),
        fetchTransactions(),
        fetchStats()
      ]);
      
      setTreasury(t);
      setAgents(a.agents || []);
      setTransactions(tx.transactions || []);
      setStats(s);
      
      if (showToast) {
        toast.success('Data refreshed successfully');
      }
    } catch (e) {
      console.error(e);
      if (showToast) {
        toast.error('Failed to refresh data');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    loadData(true);
  }, [loadData]);

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(false), 3000);
    return () => clearInterval(interval);
  }, [loadData]);

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

  const treasuryBalance = treasury?.totalAllocated - treasury?.totalSpent || 0;

  return (
    <AppShell 
      activeTab={tab} 
      setActiveTab={setTab} 
      treasuryBalance={treasuryBalance}
      onRefresh={handleRefresh}
      loading={refreshing}
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
        <EscrowManager />
      )}

      {/* Policy Logs Tab */}
      {tab === 'policy' && (
        <div className="space-y-6">
          <h2 className="text-lg font-bold text-slate-200">Policy Audit Log</h2>
          <PolicyLogs />
        </div>
      )}
    </AppShell>
  );
}

import React from 'react';
import { Wallet, TrendingUp, TrendingDown, Shield, AlertTriangle, CheckCircle, XCircle, Activity } from 'lucide-react';
import clsx from 'clsx';

interface StatsCardsProps {
  totalAllocated: number;
  totalSpent: number;
  agentCount: number;
  transactionStats: {
    total: number;
    successful: number;
    failed: number;
  };
  policyActions?: Record<string, number>;
}

export const StatsCards = ({ 
  totalAllocated, 
  totalSpent, 
  agentCount,
  transactionStats,
  policyActions = {}
}: StatsCardsProps) => {
  const remaining = totalAllocated - totalSpent;
  const usagePercent = totalAllocated > 0 ? (totalSpent / totalAllocated) * 100 : 0;
  
  const allowCount = policyActions['ALLOW'] || 0;
  const denyCount = policyActions['DENY'] || 0;
  const downgradeCount = policyActions['DOWNGRADE'] || 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Treasury Card */}
      <div className="bg-gradient-to-br from-indigo-600/20 to-purple-600/20 border border-indigo-500/30 rounded-lg p-5 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="relative">
          <div className="flex items-center gap-2 text-indigo-400 text-xs uppercase font-bold mb-3">
            <Wallet className="w-4 h-4" />
            Treasury Balance
          </div>
          <div className="text-3xl font-mono font-bold text-white mb-2">
            {remaining.toFixed(2)} <span className="text-lg text-indigo-400">MNEE</span>
          </div>
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden mb-2">
            <div 
              className={clsx(
                "h-full rounded-full transition-all duration-500",
                usagePercent > 90 ? "bg-red-500" : usagePercent > 70 ? "bg-amber-500" : "bg-emerald-500"
              )}
              style={{ width: `${Math.min(usagePercent, 100)}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-slate-400">
            <span>Spent: {totalSpent.toFixed(2)}</span>
            <span>Budget: {totalAllocated.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Active Agents */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <div className="flex items-center gap-2 text-slate-400 text-xs uppercase font-bold mb-3">
          <Activity className="w-4 h-4" />
          Active Agents
        </div>
        <div className="text-3xl font-mono font-bold text-white mb-1">
          {agentCount}
        </div>
        <div className="text-sm text-slate-500">
          Agents in fleet
        </div>
      </div>

      {/* Transactions */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <div className="flex items-center gap-2 text-slate-400 text-xs uppercase font-bold mb-3">
          <TrendingUp className="w-4 h-4" />
          Transactions
        </div>
        <div className="text-3xl font-mono font-bold text-white mb-1">
          {transactionStats.total}
        </div>
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-1 text-emerald-400">
            <CheckCircle className="w-3 h-3" />
            {transactionStats.successful} OK
          </span>
          <span className="flex items-center gap-1 text-red-400">
            <XCircle className="w-3 h-3" />
            {transactionStats.failed} Failed
          </span>
        </div>
      </div>

      {/* Policy Decisions */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <div className="flex items-center gap-2 text-slate-400 text-xs uppercase font-bold mb-3">
          <Shield className="w-4 h-4" />
          Policy Decisions
        </div>
        <div className="flex gap-3 text-center">
          <div className="flex-1">
            <div className="text-xl font-mono font-bold text-emerald-400">{allowCount}</div>
            <div className="text-[10px] text-slate-500 uppercase">Allow</div>
          </div>
          <div className="flex-1">
            <div className="text-xl font-mono font-bold text-amber-400">{downgradeCount}</div>
            <div className="text-[10px] text-slate-500 uppercase">Downgrade</div>
          </div>
          <div className="flex-1">
            <div className="text-xl font-mono font-bold text-red-400">{denyCount}</div>
            <div className="text-[10px] text-slate-500 uppercase">Deny</div>
          </div>
        </div>
      </div>
    </div>
  );
};

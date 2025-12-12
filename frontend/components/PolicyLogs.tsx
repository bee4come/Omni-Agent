import React, { useState, useEffect } from 'react';
import { Shield, CheckCircle, XCircle, AlertTriangle, Filter, RefreshCw } from 'lucide-react';
import { PolicyLog } from '../lib/types';
import { fetchPolicyLogs } from '../lib/api';
import clsx from 'clsx';

interface PolicyLogsProps {
  initialLogs?: PolicyLog[];
  compact?: boolean;
}

export const PolicyLogs = ({ initialLogs, compact = false }: PolicyLogsProps) => {
  const [logs, setLogs] = useState<PolicyLog[]>(initialLogs || []);
  const [filter, setFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(false);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await fetchPolicyLogs();
      setLogs(data.logs || []);
    } catch (e) {
      console.error('Failed to load policy logs:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!initialLogs) {
      loadLogs();
      const interval = setInterval(loadLogs, 5000);
      return () => clearInterval(interval);
    }
  }, [initialLogs]);

  const filteredLogs = logs.filter(log => 
    filter === 'ALL' || log.action === filter
  );

  const displayLogs = compact ? filteredLogs.slice(0, 5) : filteredLogs;

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'ALLOW': return <CheckCircle className="w-4 h-4 text-emerald-400" />;
      case 'DENY': return <XCircle className="w-4 h-4 text-red-400" />;
      case 'DOWNGRADE': return <AlertTriangle className="w-4 h-4 text-amber-400" />;
      default: return <Shield className="w-4 h-4 text-slate-400" />;
    }
  };

  const getActionStyle = (action: string) => {
    switch (action) {
      case 'ALLOW': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'DENY': return 'bg-red-500/10 text-red-400 border-red-500/20';
      case 'DOWNGRADE': return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
    }
  };

  const getRiskStyle = (risk: string) => {
    if (risk.includes('BLOCK') || risk.includes('HIGH')) return 'text-red-400';
    if (risk.includes('REVIEW') || risk.includes('MEDIUM')) return 'text-amber-400';
    return 'text-emerald-400';
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-400">
          <Shield className="w-4 h-4" />
          <span className="text-sm font-bold uppercase tracking-wider">Policy Audit Log</span>
        </div>
        <div className="flex items-center gap-2">
          {!compact && (
            <div className="flex gap-1">
              {['ALL', 'ALLOW', 'DENY', 'DOWNGRADE'].map(f => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={clsx(
                    "px-2 py-1 text-[10px] rounded font-bold uppercase transition-colors",
                    filter === f 
                      ? "bg-indigo-600 text-white" 
                      : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                  )}
                >
                  {f}
                </button>
              ))}
            </div>
          )}
          <button 
            onClick={loadLogs}
            className="p-1 text-slate-500 hover:text-slate-300 transition-colors"
            disabled={loading}
          >
            <RefreshCw className={clsx("w-4 h-4", loading && "animate-spin")} />
          </button>
        </div>
      </div>

      {/* Logs */}
      <div className={clsx("divide-y divide-slate-800", compact ? "max-h-80" : "max-h-[500px]", "overflow-y-auto")}>
        {displayLogs.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            No policy decisions yet
          </div>
        ) : (
          displayLogs.map((log, index) => (
            <div key={index} className="p-4 hover:bg-slate-800/50 transition-colors">
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  {getActionIcon(log.action)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={clsx("px-2 py-0.5 rounded text-[10px] font-bold border", getActionStyle(log.action))}>
                      {log.action}
                    </span>
                    <span className="px-2 py-0.5 bg-slate-800 rounded text-[10px] text-slate-400 border border-slate-700">
                      {log.agent_id}
                    </span>
                    <span className="text-xs text-slate-500">→</span>
                    <span className="text-xs text-slate-400">{log.service_id}</span>
                  </div>
                  <p className="text-sm text-slate-300 mb-2">{log.reason}</p>
                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-slate-500 font-mono">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                    {log.cost !== undefined && log.cost > 0 && (
                      <span className="text-emerald-400 font-mono">
                        {log.cost.toFixed(2)} MNEE
                      </span>
                    )}
                    <span className={clsx("uppercase font-bold text-[10px]", getRiskStyle(log.risk_level))}>
                      {log.risk_level}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

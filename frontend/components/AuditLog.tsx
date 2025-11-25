import React from 'react';
import { Shield, AlertTriangle, CheckCircle, XCircle, DollarSign } from 'lucide-react';
import { Card } from './ui/Card';

interface LogEntry {
  timestamp: string;
  agent_id: string;
  service_id: string;
  action: string;
  risk_level: string;
  reason: string;
  cost?: number;
}

interface AuditLogProps {
  logs: LogEntry[];
}

export const AuditLog: React.FC<AuditLogProps> = ({ logs }) => {
  return (
    <Card className="flex flex-col h-[400px]">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-500/10 rounded-lg">
            <Shield className="w-5 h-5 text-emerald-500" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Guardian Audit Log</h2>
            <p className="text-sm text-slate-400">Real-time risk & budget enforcement</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-3">
        {logs.map((log, i) => (
          <div key={i} className="group p-4 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-indigo-500/30 transition-all">
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider ${
                  log.action === 'ALLOW' ? 'bg-emerald-500/10 text-emerald-400' : 
                  log.action === 'DENY' ? 'bg-red-500/10 text-red-400' : 'bg-amber-500/10 text-amber-400'
                }`}>
                  {log.action}
                </span>
                <span className="text-xs text-slate-500 font-mono">{new Date(log.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className="text-xs font-medium text-indigo-400">{log.agent_id}</div>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2 text-sm text-slate-300">
                <span>{log.service_id}</span>
              </div>
              {log.cost && (
                <div className="flex items-center gap-1 text-sm font-mono text-slate-400">
                  <DollarSign className="w-3 h-3" />
                  {log.cost.toFixed(2)} MNEE
                </div>
              )}
            </div>

            {log.reason && (
              <div className="mt-2 pt-2 border-t border-slate-800/50 text-xs text-slate-500 italic">
                {log.reason}
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

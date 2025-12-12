import React, { useState, useEffect } from 'react';
import { 
  Lock, 
  Unlock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  ArrowRight,
  ExternalLink,
  Clock,
  Shield,
  Loader2,
  RefreshCw
} from 'lucide-react';
import clsx from 'clsx';

// Escrow status types
type EscrowStatus = 'created' | 'submitted' | 'verifying' | 'released' | 'refunded' | 'disputed';

interface EscrowRecord {
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

interface EscrowManagerProps {
  escrows?: EscrowRecord[];
  onRefresh?: () => void;
}

const StatusIcon = ({ status }: { status: EscrowStatus }) => {
  switch (status) {
    case 'created':
      return <Lock className="w-4 h-4 text-amber-400" />;
    case 'submitted':
      return <Clock className="w-4 h-4 text-blue-400" />;
    case 'verifying':
      return <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />;
    case 'released':
      return <Unlock className="w-4 h-4 text-emerald-400" />;
    case 'refunded':
      return <RefreshCw className="w-4 h-4 text-orange-400" />;
    case 'disputed':
      return <AlertTriangle className="w-4 h-4 text-red-400" />;
    default:
      return <Shield className="w-4 h-4 text-slate-400" />;
  }
};

const StatusBadge = ({ status }: { status: EscrowStatus }) => {
  const colors: Record<EscrowStatus, string> = {
    created: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    submitted: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    verifying: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    released: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    refunded: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    disputed: 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  return (
    <span className={clsx(
      'px-2 py-0.5 text-[10px] font-bold uppercase rounded border',
      colors[status]
    )}>
      {status}
    </span>
  );
};

const EscrowCard = ({ escrow }: { escrow: EscrowRecord }) => {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg overflow-hidden">
      {/* Header */}
      <div 
        className="p-4 cursor-pointer hover:bg-slate-800/80 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <StatusIcon status={escrow.status} />
            <span className="font-mono text-sm text-slate-300">{escrow.escrow_id}</span>
          </div>
          <StatusBadge status={escrow.status} />
        </div>
        
        {/* Flow visualization */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-indigo-400 font-mono">{escrow.customer_agent.split('-')[0]}</span>
          <ArrowRight className="w-3 h-3 text-slate-500" />
          <div className="flex items-center gap-1 px-2 py-1 bg-slate-900 rounded border border-slate-700">
            <Lock className="w-3 h-3 text-amber-400" />
            <span className="font-mono font-bold text-emerald-400">{escrow.amount.toFixed(2)} MNEE</span>
          </div>
          <ArrowRight className="w-3 h-3 text-slate-500" />
          <span className="text-purple-400 font-mono">{escrow.merchant_agent.split('-')[0]}</span>
        </div>
      </div>
      
      {/* Expanded details */}
      {expanded && (
        <div className="border-t border-slate-700 p-4 bg-slate-900/50 space-y-3">
          {/* Timeline */}
          <div className="space-y-2">
            <div className="text-[10px] uppercase font-bold text-slate-500">Timeline</div>
            <div className="space-y-1 text-xs">
              {escrow.created_at && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-amber-400" />
                  <span className="text-slate-400">Created:</span>
                  <span className="text-slate-300">{new Date(escrow.created_at).toLocaleString()}</span>
                </div>
              )}
              {escrow.submitted_at && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-400" />
                  <span className="text-slate-400">Submitted:</span>
                  <span className="text-slate-300">{new Date(escrow.submitted_at).toLocaleString()}</span>
                </div>
              )}
              {escrow.verified_at && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-purple-400" />
                  <span className="text-slate-400">Verified:</span>
                  <span className="text-slate-300">{new Date(escrow.verified_at).toLocaleString()}</span>
                </div>
              )}
              {escrow.released_at && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="text-slate-400">Released:</span>
                  <span className="text-slate-300">{new Date(escrow.released_at).toLocaleString()}</span>
                </div>
              )}
            </div>
          </div>
          
          {/* Verification */}
          {escrow.verification_score !== undefined && (
            <div className="space-y-2">
              <div className="text-[10px] uppercase font-bold text-slate-500">Verification</div>
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div 
                    className={clsx(
                      'h-full rounded-full transition-all',
                      escrow.verification_passed ? 'bg-emerald-500' : 'bg-red-500'
                    )}
                    style={{ width: `${escrow.verification_score * 100}%` }}
                  />
                </div>
                <span className="text-sm font-mono">
                  {(escrow.verification_score * 100).toFixed(0)}%
                </span>
                {escrow.verification_passed ? (
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-400" />
                )}
              </div>
            </div>
          )}
          
          {/* Transaction Links */}
          <div className="space-y-2">
            <div className="text-[10px] uppercase font-bold text-slate-500">On-Chain Proof</div>
            <div className="flex flex-wrap gap-2">
              {escrow.lock_tx_hash && (
                <a
                  href={`https://etherscan.io/tx/${escrow.lock_tx_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 px-2 py-1 bg-amber-500/10 border border-amber-500/30 rounded text-[10px] text-amber-400 hover:bg-amber-500/20 transition-colors"
                >
                  <Lock className="w-3 h-3" />
                  Lock TX
                  <ExternalLink className="w-2.5 h-2.5" />
                </a>
              )}
              {escrow.release_tx_hash && (
                <a
                  href={`https://etherscan.io/tx/${escrow.release_tx_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 px-2 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded text-[10px] text-emerald-400 hover:bg-emerald-500/20 transition-colors"
                >
                  <Unlock className="w-3 h-3" />
                  Release TX
                  <ExternalLink className="w-2.5 h-2.5" />
                </a>
              )}
            </div>
          </div>
          
          {/* Dispute Info */}
          {escrow.status === 'disputed' && escrow.dispute_reason && (
            <div className="p-3 bg-red-950/30 border border-red-900/50 rounded">
              <div className="flex items-center gap-2 text-red-400 text-xs font-bold mb-1">
                <AlertTriangle className="w-3 h-3" />
                Dispute Reason
              </div>
              <p className="text-xs text-red-300">{escrow.dispute_reason}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Pipeline visualization
const EscrowPipeline = ({ escrows }: { escrows: EscrowRecord[] }) => {
  const statusCounts = {
    created: escrows.filter(e => e.status === 'created').length,
    submitted: escrows.filter(e => e.status === 'submitted').length,
    verifying: escrows.filter(e => e.status === 'verifying').length,
    released: escrows.filter(e => e.status === 'released').length,
    refunded: escrows.filter(e => e.status === 'refunded').length,
    disputed: escrows.filter(e => e.status === 'disputed').length,
  };
  
  const totalAmount = escrows.reduce((sum, e) => sum + e.amount, 0);
  const releasedAmount = escrows
    .filter(e => e.status === 'released')
    .reduce((sum, e) => sum + e.amount, 0);
  
  return (
    <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-slate-300">Escrow Pipeline</h3>
        <div className="text-xs text-slate-500">
          <span className="text-emerald-400 font-mono">{releasedAmount.toFixed(2)}</span>
          <span> / </span>
          <span className="font-mono">{totalAmount.toFixed(2)}</span>
          <span> MNEE released</span>
        </div>
      </div>
      
      {/* Status flow */}
      <div className="flex items-center justify-between gap-2">
        {(['created', 'submitted', 'verifying', 'released'] as EscrowStatus[]).map((status, i) => (
          <React.Fragment key={status}>
            <div className="flex-1 text-center">
              <div className={clsx(
                'mx-auto w-10 h-10 rounded-full flex items-center justify-center mb-1',
                statusCounts[status] > 0 ? 'bg-slate-700' : 'bg-slate-800'
              )}>
                <StatusIcon status={status} />
              </div>
              <div className="text-[10px] uppercase text-slate-500">{status}</div>
              <div className="text-sm font-bold text-slate-300">{statusCounts[status]}</div>
            </div>
            {i < 3 && <ArrowRight className="w-4 h-4 text-slate-600 flex-shrink-0" />}
          </React.Fragment>
        ))}
      </div>
      
      {/* Refunded/Disputed count */}
      {(statusCounts.refunded > 0 || statusCounts.disputed > 0) && (
        <div className="mt-3 pt-3 border-t border-slate-700 flex gap-4 justify-center text-xs">
          {statusCounts.refunded > 0 && (
            <div className="flex items-center gap-1 text-orange-400">
              <RefreshCw className="w-3 h-3" />
              {statusCounts.refunded} refunded
            </div>
          )}
          {statusCounts.disputed > 0 && (
            <div className="flex items-center gap-1 text-red-400">
              <AlertTriangle className="w-3 h-3" />
              {statusCounts.disputed} disputed
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const EscrowManager = ({ escrows = [], onRefresh }: EscrowManagerProps) => {
  // Demo data if no escrows provided
  const [demoEscrows] = useState<EscrowRecord[]>([
    {
      escrow_id: 'ESC-a1b2c3d4',
      task_id: 'TASK-001',
      customer_agent: 'user-agent',
      merchant_agent: 'startup-designer',
      amount: 1.5,
      fee: 0.015,
      status: 'released',
      created_at: new Date(Date.now() - 300000).toISOString(),
      submitted_at: new Date(Date.now() - 200000).toISOString(),
      verified_at: new Date(Date.now() - 100000).toISOString(),
      released_at: new Date(Date.now() - 50000).toISOString(),
      verification_score: 0.92,
      verification_passed: true,
      lock_tx_hash: '0x1234567890abcdef1234567890abcdef12345678',
      release_tx_hash: '0xabcdef1234567890abcdef1234567890abcdef12',
    },
    {
      escrow_id: 'ESC-e5f6g7h8',
      task_id: 'TASK-002',
      customer_agent: 'user-agent',
      merchant_agent: 'startup-analyst',
      amount: 0.5,
      fee: 0.005,
      status: 'verifying',
      created_at: new Date(Date.now() - 60000).toISOString(),
      submitted_at: new Date(Date.now() - 30000).toISOString(),
      verification_score: 0.75,
      lock_tx_hash: '0x9876543210fedcba9876543210fedcba98765432',
    },
    {
      escrow_id: 'ESC-i9j0k1l2',
      task_id: 'TASK-003',
      customer_agent: 'startup-analyst',
      merchant_agent: 'batch-agent',
      amount: 3.0,
      fee: 0.03,
      status: 'created',
      created_at: new Date().toISOString(),
      lock_tx_hash: '0xfedcba9876543210fedcba9876543210fedcba98',
    },
  ]);
  
  const displayEscrows = escrows.length > 0 ? escrows : demoEscrows;
  
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-200">Escrow Manager</h2>
          <p className="text-xs text-slate-500">Trustless Agent-to-Agent transactions</p>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-2 hover:bg-slate-800 rounded transition-colors"
          >
            <RefreshCw className="w-4 h-4 text-slate-400" />
          </button>
        )}
      </div>
      
      {/* Pipeline Overview */}
      <EscrowPipeline escrows={displayEscrows} />
      
      {/* Escrow List */}
      <div className="space-y-3">
        {displayEscrows.map(escrow => (
          <EscrowCard key={escrow.escrow_id} escrow={escrow} />
        ))}
        
        {displayEscrows.length === 0 && (
          <div className="text-center py-8 text-slate-500">
            <Lock className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No escrow transactions yet</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default EscrowManager;
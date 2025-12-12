import React, { useState, useEffect } from 'react';
import { Network, Zap, ArrowRight, ExternalLink, RefreshCw } from 'lucide-react';
import clsx from 'clsx';

interface A2ATransfer {
  transfer_id: number;
  from_agent: string;
  to_agent: string;
  amount: number;
  task_description: string;
  tx_hash: string;
  timestamp: string;
}

interface AgentBalance {
  [agentId: string]: number;
}

interface A2ANetworkProps {
  className?: string;
}

const AGENT_COLORS: Record<string, string> = {
  'user-agent': 'bg-indigo-500',
  'startup-designer': 'bg-purple-500',
  'startup-analyst': 'bg-emerald-500',
  'startup-archivist': 'bg-amber-500',
};

const AGENT_POSITIONS: Record<string, { x: number; y: number }> = {
  'user-agent': { x: 50, y: 20 },
  'startup-designer': { x: 20, y: 60 },
  'startup-analyst': { x: 50, y: 60 },
  'startup-archivist': { x: 80, y: 60 },
};

export const A2ANetwork = ({ className }: A2ANetworkProps) => {
  const [transfers, setTransfers] = useState<A2ATransfer[]>([]);
  const [balances, setBalances] = useState<AgentBalance>({});
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch transfers
      const transferRes = await fetch('http://localhost:8000/a2a/transfers?count=20');
      if (transferRes.ok) {
        const data = await transferRes.json();
        setTransfers(data.transfers || []);
        setTotalCount(data.total_count || 0);
      }

      // Fetch balances
      const balanceRes = await fetch('http://localhost:8000/a2a/balances');
      if (balanceRes.ok) {
        const data = await balanceRes.json();
        setBalances(data.balances || {});
      }
    } catch (e) {
      console.error('Failed to fetch A2A data:', e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  // Demo A2A payment
  const executeDemo = async () => {
    setLoading(true);
    try {
      const demos = [
        { from: 'user-agent', to: 'startup-analyst', amount: 0.5, task: 'Analyze market data' },
        { from: 'startup-analyst', to: 'startup-designer', amount: 0.3, task: 'Create visualization' },
      ];
      
      for (const demo of demos) {
        await fetch('http://localhost:8000/a2a/pay', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            from_agent: demo.from,
            to_agent: demo.to,
            amount: demo.amount,
            task_description: demo.task
          })
        });
      }
      
      await fetchData();
    } catch (e) {
      console.error('Demo failed:', e);
    }
    setLoading(false);
  };

  const totalVolume = transfers.reduce((sum, t) => sum + t.amount, 0);

  return (
    <div className={clsx("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-600/20 rounded-lg">
            <Network className="w-6 h-6 text-purple-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">A2A Payment Network</h2>
            <p className="text-sm text-slate-500">Real on-chain Agent-to-Agent transfers</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors"
          >
            <RefreshCw className={clsx("w-4 h-4", loading && "animate-spin")} />
            Refresh
          </button>
          <button
            onClick={executeDemo}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Zap className="w-4 h-4" />
            Execute A2A Demo
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">{Object.keys(balances).length}</div>
          <div className="text-xs text-slate-500">Registered Agents</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-400">{totalCount}</div>
          <div className="text-xs text-slate-500">A2A Transfers</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="text-2xl font-bold font-mono text-emerald-400">{totalVolume.toFixed(2)}</div>
          <div className="text-xs text-slate-500">MNEE Volume</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
          <div className="text-2xl font-bold font-mono text-white">
            {Object.values(balances).reduce((a, b) => a + b, 0).toFixed(1)}
          </div>
          <div className="text-xs text-slate-500">Total Wallet Balance</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Network Graph */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-lg p-6 min-h-[350px] relative">
          <div className="absolute top-4 left-4 text-xs text-slate-500 uppercase font-bold">
            Agent Network Topology
          </div>

          {/* SVG for edges */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            <defs>
              <marker
                id="arrowhead-a2a"
                markerWidth="10"
                markerHeight="7"
                refX="9"
                refY="3.5"
                orient="auto"
              >
                <polygon points="0 0, 10 3.5, 0 7" fill="#8b5cf6" />
              </marker>
            </defs>

            {transfers.slice(0, 5).map((transfer, i) => {
              const fromPos = AGENT_POSITIONS[transfer.from_agent];
              const toPos = AGENT_POSITIONS[transfer.to_agent];
              if (!fromPos || !toPos) return null;

              return (
                <line
                  key={i}
                  x1={`${fromPos.x}%`}
                  y1={`${fromPos.y}%`}
                  x2={`${toPos.x}%`}
                  y2={`${toPos.y}%`}
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  strokeOpacity={0.6}
                  markerEnd="url(#arrowhead-a2a)"
                />
              );
            })}
          </svg>

          {/* Agent nodes */}
          {Object.entries(AGENT_POSITIONS).map(([agentId, pos]) => {
            const balance = balances[agentId] || 0;
            return (
              <div
                key={agentId}
                className="absolute transform -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
              >
                <div className={clsx(
                  "w-16 h-16 rounded-full border-2 border-slate-600 flex items-center justify-center",
                  AGENT_COLORS[agentId]
                )}>
                  <div className="text-white text-[10px] font-bold text-center leading-tight">
                    {agentId.split('-')[0]}
                  </div>
                </div>
                <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap">
                  <div className="text-[10px] font-mono text-emerald-400">
                    {balance.toFixed(1)} MNEE
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Transfer List */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-slate-800">
            <h3 className="text-sm font-bold text-slate-300">Recent A2A Transfers</h3>
            <p className="text-xs text-slate-500">Real on-chain MNEE transfers</p>
          </div>
          <div className="divide-y divide-slate-800 max-h-[280px] overflow-y-auto">
            {transfers.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">
                No A2A transfers yet. Click "Execute A2A Demo" to create some.
              </div>
            ) : (
              transfers.map((transfer) => (
                <div
                  key={transfer.transfer_id}
                  className="p-3 hover:bg-slate-800/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-1 text-xs">
                      <span className="text-slate-400">{transfer.from_agent.split('-')[0]}</span>
                      <ArrowRight className="w-3 h-3 text-purple-400" />
                      <span className="text-slate-400">{transfer.to_agent.split('-')[0]}</span>
                    </div>
                    <span className="font-mono text-xs font-bold text-emerald-400">
                      {transfer.amount.toFixed(2)} MNEE
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500 mb-1 truncate">
                    {transfer.task_description}
                  </div>
                  <div className="flex items-center justify-between">
                    <a
                      href={`https://etherscan.io/tx/${transfer.tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-[10px] font-mono text-indigo-400 hover:underline"
                    >
                      {transfer.tx_hash.slice(0, 10)}...
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                    <span className="text-[10px] text-slate-600">
                      {new Date(transfer.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

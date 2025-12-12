import React from 'react';
import { ExternalLink } from 'lucide-react';
import { Transaction } from '../lib/types';
import clsx from 'clsx';

export const Ledger = ({ transactions }: { transactions: Transaction[] }) => {
  const getExplorerUrl = (txHash: string) => {
    // For local hardhat fork, still show etherscan link for demo
    return `https://etherscan.io/tx/${txHash}`;
  };

  return (
    <div className="border border-slate-800 rounded overflow-hidden bg-slate-900/50">
      <table className="w-full text-sm text-left data-table">
        <thead className="bg-slate-900 text-slate-500 font-medium border-b border-slate-800">
          <tr>
            <th className="px-4 py-3">Timestamp</th>
            <th className="px-4 py-3">Agent</th>
            <th className="px-4 py-3">Service</th>
            <th className="px-4 py-3 text-right">Amount</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3 font-mono">TX Hash</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800 text-slate-300">
          {transactions.map((tx, i) => (
            <tr key={i} className="hover:bg-slate-800/50 transition-colors">
              <td className="px-4 py-3 font-mono text-xs text-slate-500">
                {new Date(tx.timestamp).toLocaleTimeString()}
              </td>
              <td className="px-4 py-3">
                <span className="px-2 py-0.5 bg-slate-800 rounded text-xs text-slate-300 border border-slate-700">
                  {tx.agent_id}
                </span>
              </td>
              <td className="px-4 py-3">{tx.service_id}</td>
              <td className="px-4 py-3 text-right font-mono text-emerald-400">
                {tx.amount.toFixed(2)} <span className="text-slate-500 text-[10px]">MNEE</span>
              </td>
              <td className="px-4 py-3">
                <span className={clsx(
                  "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                  tx.status === 'SUCCESS' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'
                )}>
                  {tx.status}
                </span>
              </td>
              <td className="px-4 py-3">
                {tx.tx_hash ? (
                  <a
                    href={getExplorerUrl(tx.tx_hash)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 font-mono text-xs text-indigo-400 hover:text-indigo-300 transition-colors group"
                  >
                    <span className="truncate max-w-[80px]">{tx.tx_hash}</span>
                    <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </a>
                ) : (
                  <span className="font-mono text-xs text-slate-600">-</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {transactions.length === 0 && (
        <div className="py-12 text-center text-slate-500">
          No transactions yet
        </div>
      )}
    </div>
  );
};

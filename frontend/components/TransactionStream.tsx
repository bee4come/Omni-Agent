import React from 'react';
import { Activity, Hash } from 'lucide-react';
import { Card, cn } from './ui/Card';

interface TransactionStreamProps {
    transactions: any[];
}

export const TransactionStream = ({ transactions }: TransactionStreamProps) => {
    return (
        <Card>
            <h2 className="font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4" />
                Transaction Stream
            </h2>
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {transactions.map((tx: any, i: number) => (
                    <div key={i} className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                                <div className={cn("w-2 h-2 rounded-full", tx.status === 'SUCCESS' ? 'bg-emerald-500' : 'bg-red-500')} />
                                <div>
                                    <div className="text-sm font-medium text-slate-300">{tx.service_id}</div>
                                    <div className="text-xs text-slate-500">Agent: {tx.agent_id}</div>
                                </div>
                            </div>
                            <div className="text-right">
                                <div className="text-sm font-bold text-indigo-400">{tx.amount} MNEE</div>
                                <div className="text-xs text-slate-500">{new Date(tx.timestamp).toLocaleTimeString()}</div>
                            </div>
                        </div>
                        {tx.service_call_hash && (
                            <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-900/50 rounded px-2 py-1">
                                <Hash className="w-3 h-3" />
                                <span className="font-mono" title={tx.service_call_hash}>
                                    {tx.service_call_hash.substring(0, 16)}...
                                </span>
                            </div>
                        )}
                    </div>
                ))}
                {transactions.length === 0 && (
                    <div className="text-center text-slate-600 py-12">
                        No transactions yet
                    </div>
                )}
            </div>
        </Card>
    );
};

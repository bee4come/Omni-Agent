import React from 'react';
import { Card } from './ui/Card';
import { TransactionStream } from './TransactionStream';

interface DashboardProps {
    stats: any;
    transactions: any[];
}

export const Dashboard = ({ stats, transactions }: DashboardProps) => {
    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                    <div className="text-sm text-slate-500 mb-2">Total Allocated Budget</div>
                    <div className="text-3xl font-bold text-emerald-400">
                        {stats?.totalAllocatedBudget?.toFixed(2) || '0.00'} <span className="text-lg text-slate-500">MNEE</span>
                    </div>
                </Card>
                <Card>
                    <div className="text-sm text-slate-500 mb-2">Total Spent Today</div>
                    <div className="text-3xl font-bold text-indigo-400">
                        {stats?.totalSpent?.toFixed(2) || '0.00'} <span className="text-lg text-slate-500">MNEE</span>
                    </div>
                </Card>
                <Card>
                    <div className="text-sm text-slate-500 mb-2">Transactions</div>
                    <div className="text-3xl font-bold text-slate-300">
                        {stats?.transactions?.total || 0}
                    </div>
                </Card>
            </div>
            
            <TransactionStream transactions={transactions} />
        </div>
    );
};

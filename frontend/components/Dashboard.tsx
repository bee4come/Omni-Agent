import React from 'react';
import { Card } from './ui/Card';
import { TransactionStream } from './TransactionStream';
import { BarChart, PieChart, Activity } from 'lucide-react';

interface DashboardProps {
    stats: any;
    transactions: any[];
}

export const Dashboard = ({ stats, transactions }: DashboardProps) => {
    if (!stats) return <div>Loading stats...</div>;

    return (
        <div className="space-y-8 animate-fade-in">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <Activity className="text-indigo-500" />
                Financial Analytics
            </h2>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
                    <div className="text-sm text-slate-400 mb-1">Total Budget</div>
                    <div className="text-3xl font-bold text-white">
                        {stats.totalAllocatedBudget?.toFixed(0)} <span className="text-sm text-slate-500">MNEE</span>
                    </div>
                </Card>
                <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
                    <div className="text-sm text-slate-400 mb-1">Total Spent</div>
                    <div className="text-3xl font-bold text-indigo-400">
                        {stats.totalSpent?.toFixed(2)} <span className="text-sm text-slate-500">MNEE</span>
                    </div>
                </Card>
                <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
                    <div className="text-sm text-slate-400 mb-1">Transactions</div>
                    <div className="text-3xl font-bold text-emerald-400">
                        {stats.transactions?.successful} <span className="text-sm text-slate-500">/ {stats.transactions?.total}</span>
                    </div>
                </Card>
                <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700">
                    <div className="text-sm text-slate-400 mb-1">Active Agents</div>
                    <div className="text-3xl font-bold text-amber-400">
                        {stats.agentCount}
                    </div>
                </Card>
            </div>

            {/* Charts Placeholder (For Hackathon visual impact) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className="h-64 flex items-center justify-center border-dashed border-2 border-slate-800 bg-slate-900/30">
                    <div className="text-center text-slate-500">
                        <BarChart className="w-12 h-12 mx-auto mb-2 opacity-20" />
                        <p>Spending by Agent (Coming Soon)</p>
                    </div>
                </Card>
                <Card className="h-64 flex items-center justify-center border-dashed border-2 border-slate-800 bg-slate-900/30">
                    <div className="text-center text-slate-500">
                        <PieChart className="w-12 h-12 mx-auto mb-2 opacity-20" />
                        <p>Service Usage Distribution (Coming Soon)</p>
                    </div>
                </Card>
            </div>
            
            <div className="pt-4">
                <h3 className="text-lg font-semibold text-slate-300 mb-4">Recent Transactions</h3>
                <TransactionStream transactions={transactions} />
            </div>
        </div>
    );
};
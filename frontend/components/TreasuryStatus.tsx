import React from 'react';
import { DollarSign } from 'lucide-react';
import { Card, cn } from './ui/Card';
import { Badge } from './ui/Badge';

interface TreasuryStatusProps {
    treasury: any;
}

export const TreasuryStatus = ({ treasury }: TreasuryStatusProps) => {
    return (
        <Card>
            <div className="flex items-center justify-between mb-6">
                <h2 className="font-semibold flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-emerald-400" />
                    Treasury Status
                </h2>
                <Badge variant="success">Active</Badge>
            </div>

            <div className="space-y-4">
                {treasury?.agents && Object.entries(treasury.agents).map(([id, data]: [string, any]) => (
                    <div key={id} className="p-3 bg-slate-950 rounded-lg border border-slate-800">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-sm font-medium text-slate-300">{id}</span>
                            <span className={cn("text-xs font-bold", data.priority === 'HIGH' ? "text-emerald-400" : "text-slate-500")}>
                                {data.priority}
                            </span>
                        </div>
                        <div className="space-y-1">
                            <div className="flex justify-between text-xs text-slate-500">
                                <span>Daily Spend</span>
                                <span>{data.currentDailySpend.toFixed(2)} / {data.dailyBudget} MNEE</span>
                            </div>
                            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                <div
                                    className={cn("h-full rounded-full transition-all duration-500",
                                        (data.currentDailySpend / data.dailyBudget) > 0.9 ? "bg-red-500" : "bg-indigo-500"
                                    )}
                                    style={{ width: `${Math.min((data.currentDailySpend / data.dailyBudget) * 100, 100)}%` }}
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </Card>
    );
};

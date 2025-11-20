import React from 'react';
import { Settings, Server, CheckCircle, AlertTriangle } from 'lucide-react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';

interface ConfigPanelProps {
    treasury: any;
    services: any[];
}

export const ConfigPanel = ({ treasury, services }: ConfigPanelProps) => {
    return (
        <div className="space-y-6">
            <Card>
                <h2 className="font-semibold mb-4 flex items-center gap-2">
                    <Settings className="w-4 h-4" />
                    Agent Budget Configuration
                </h2>
                <div className="space-y-4">
                    {treasury?.agents && Object.entries(treasury.agents).map(([id, data]: [string, any]) => (
                        <div key={id} className="p-4 bg-slate-950 rounded-lg border border-slate-800">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-semibold text-lg text-slate-200">{id}</h3>
                                <Badge variant={data.priority === 'HIGH' ? 'success' : data.priority === 'MEDIUM' ? 'warning' : 'default'}>
                                    {data.priority} PRIORITY
                                </Badge>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-xs text-slate-500 block mb-1">Daily Budget (MNEE)</label>
                                    <div className="text-xl font-bold text-emerald-400">{data.dailyBudget}</div>
                                </div>
                                <div>
                                    <label className="text-xs text-slate-500 block mb-1">Max Per Call (MNEE)</label>
                                    <div className="text-xl font-bold text-indigo-400">{data.maxPerCall}</div>
                                </div>
                                <div>
                                    <label className="text-xs text-slate-500 block mb-1">Today's Spend</label>
                                    <div className="text-xl font-bold text-slate-300">{data.currentDailySpend.toFixed(2)}</div>
                                </div>
                                <div>
                                    <label className="text-xs text-slate-500 block mb-1">Remaining</label>
                                    <div className="text-xl font-bold text-slate-300">{data.remainingBudget.toFixed(2)}</div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </Card>
            
            <Card>
                <h2 className="font-semibold mb-4 flex items-center gap-2">
                    <Server className="w-4 h-4" />
                    Service Provider Configuration
                </h2>
                <div className="space-y-3">
                    {services.map((service: any, i: number) => (
                        <div key={i} className="p-4 bg-slate-950 rounded-lg border border-slate-800 flex items-center justify-between">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <div className="font-semibold text-slate-200">{service.id}</div>
                                    {service.isVerified ? (
                                        <div className="flex items-center gap-1 text-emerald-400" title="Verified Service Provider">
                                            <CheckCircle className="w-4 h-4" />
                                            <span className="text-xs">Verified</span>
                                        </div>
                                    ) : (
                                        <div className="flex items-center gap-1 text-amber-400" title="Unverified Service Provider">
                                            <AlertTriangle className="w-4 h-4" />
                                            <span className="text-xs">Unverified</span>
                                        </div>
                                    )}
                                </div>
                                <div className="text-xs text-slate-500 mt-1">Provider: {service.providerAddress}</div>
                                {service.metadataURI && (
                                    <a href={service.metadataURI} target="_blank" rel="noopener noreferrer" className="text-xs text-indigo-400 hover:text-indigo-300 mt-1 inline-block">
                                        View Details →
                                    </a>
                                )}
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="text-right">
                                    <div className="text-sm text-slate-500">Unit Price</div>
                                    <div className="text-lg font-bold text-indigo-400">{service.unitPrice} MNEE</div>
                                </div>
                                <Badge variant={service.active ? 'success' : 'danger'}>
                                    {service.active ? 'Active' : 'Inactive'}
                                </Badge>
                            </div>
                        </div>
                    ))}
                </div>
            </Card>
        </div>
    );
};

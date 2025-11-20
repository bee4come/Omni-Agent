import React from 'react';
import { ShieldAlert, XCircle, CheckCircle, AlertTriangle, Shield, AlertCircle } from 'lucide-react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';

interface PolicyConsoleProps {
    logs: any[];
}

export const PolicyConsole = ({ logs }: PolicyConsoleProps) => {
    return (
        <div className="space-y-6">
            <Card>
                <h2 className="font-semibold mb-4 flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    Policy Decision Log
                </h2>
                <div className="space-y-3 max-h-[700px] overflow-y-auto">
                    {logs.map((log: any, i: number) => (
                        <div key={i} className="p-4 rounded-lg bg-slate-950 border border-slate-800">
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center gap-2">
                                    {log.action === 'REJECTED' && <XCircle className="w-5 h-5 text-red-400" />}
                                    {log.action === 'ALLOWED' && <CheckCircle className="w-5 h-5 text-emerald-400" />}
                                    {log.action === 'DOWNGRADED' && <AlertTriangle className="w-5 h-5 text-amber-400" />}
                                    <Badge variant={log.action === 'REJECTED' ? 'danger' : log.action === 'ALLOWED' ? 'success' : 'warning'}>
                                        {log.action}
                                    </Badge>
                                </div>
                                <span className="text-xs text-slate-500">{new Date(log.timestamp).toLocaleString()}</span>
                            </div>
                            <div className="grid grid-cols-2 gap-3 text-sm mb-3">
                                <div>
                                    <span className="text-slate-500">Agent:</span>
                                    <span className="text-slate-300 ml-2 font-medium">{log.agent_id}</span>
                                </div>
                                <div>
                                    <span className="text-slate-500">Service:</span>
                                    <span className="text-slate-300 ml-2 font-medium">{log.service_id}</span>
                                </div>
                                {log.cost && (
                                    <div>
                                        <span className="text-slate-500">Cost:</span>
                                        <span className="text-indigo-400 ml-2 font-medium">{log.cost} MNEE</span>
                                    </div>
                                )}
                                {log.risk_level && (
                                    <div className="flex items-center gap-2">
                                        <span className="text-slate-500">Risk:</span>
                                        {log.risk_level === 'RISK_OK' && (
                                            <div className="flex items-center gap-1 text-emerald-400">
                                                <Shield className="w-4 h-4" />
                                                <span className="font-medium">OK</span>
                                            </div>
                                        )}
                                        {log.risk_level === 'RISK_REVIEW' && (
                                            <div className="flex items-center gap-1 text-amber-400">
                                                <AlertCircle className="w-4 h-4" />
                                                <span className="font-medium">REVIEW</span>
                                            </div>
                                        )}
                                        {log.risk_level === 'RISK_BLOCK' && (
                                            <div className="flex items-center gap-1 text-red-400">
                                                <AlertTriangle className="w-4 h-4" />
                                                <span className="font-medium">BLOCK</span>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                            <div className="text-sm text-slate-400 bg-slate-900/50 rounded p-3">
                                <span className="text-slate-500 font-medium">Reason:</span> {log.reason}
                            </div>
                        </div>
                    ))}
                    {logs.length === 0 && (
                        <div className="text-center text-slate-600 py-12">
                            No policy decisions recorded yet
                        </div>
                    )}
                </div>
            </Card>
        </div>
    );
};

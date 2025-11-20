import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';

interface PolicyLogsPreviewProps {
    logs: any[];
}

export const PolicyLogsPreview = ({ logs }: PolicyLogsPreviewProps) => {
    return (
        <Card className="flex-1 min-h-[300px]">
            <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                    System Policy Log
                </h2>
            </div>
            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                {logs.map((log: any, i: number) => (
                    <div key={i} className="text-xs p-3 rounded-lg bg-slate-950 border border-slate-800">
                        <div className="flex justify-between text-slate-500 mb-1">
                            <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                            <Badge variant={log.action === 'REJECTED' ? 'danger' : log.action === 'ALLOWED' ? 'success' : 'warning'}>
                                {log.action}
                            </Badge>
                        </div>
                        <div className="text-slate-400 text-[11px] mb-1">
                            Agent: <span className="text-slate-300">{log.agent_id}</span> | Service: <span className="text-slate-300">{log.service_id}</span>
                        </div>
                        <p className="text-slate-300 leading-relaxed">{log.reason}</p>
                    </div>
                ))}
                {logs.length === 0 && (
                    <div className="text-center text-slate-600 py-8 text-xs">
                        No policy events recorded yet.
                    </div>
                )}
            </div>
        </Card>
    );
};

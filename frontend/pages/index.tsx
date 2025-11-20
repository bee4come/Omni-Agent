import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Send, ShieldAlert, Activity, DollarSign, Server, Database, Image as ImageIcon, FileText } from 'lucide-react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// --- Utility ---
function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// --- Components ---

const Card = ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div className={cn("bg-slate-900 border border-slate-800 rounded-xl p-6", className)}>
        {children}
    </div>
);

const Badge = ({ children, variant = 'default' }: { children: React.ReactNode; variant?: 'default' | 'danger' | 'warning' | 'success' }) => {
    const variants = {
        default: "bg-slate-800 text-slate-300",
        danger: "bg-red-900/30 text-red-400 border border-red-900/50",
        warning: "bg-amber-900/30 text-amber-400 border border-amber-900/50",
        success: "bg-emerald-900/30 text-emerald-400 border border-emerald-900/50",
    };
    return (
        <span className={cn("px-2 py-1 rounded-md text-xs font-medium", variants[variant])}>
            {children}
        </span>
    );
};

export default function Dashboard() {
    const [input, setInput] = useState('');
    const [agentId, setAgentId] = useState('user-agent');
    const [messages, setMessages] = useState<{ role: string, content: string }[]>([]);
    const [loading, setLoading] = useState(false);
    const [treasury, setTreasury] = useState<any>(null);
    const [logs, setLogs] = useState<any[]>([]);

    const fetchTreasury = async () => {
        try {
            const res = await axios.get('/api/treasury');
            setTreasury(res.data);
        } catch (e) {
            console.error(e);
        }
    };

    useEffect(() => {
        fetchTreasury();
        const interval = setInterval(fetchTreasury, 5000);
        return () => clearInterval(interval);
    }, []);

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await axios.post('/api/chat', {
                agent_id: agentId,
                message: userMsg.content
            });

            setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);

            // Simulate adding a log for demo purposes if we detect keywords
            if (res.data.response.includes("Policy Rejected")) {
                setLogs(prev => [{
                    timestamp: new Date().toISOString(),
                    type: 'REJECTED',
                    message: `Agent ${agentId} request blocked by policy.`
                }, ...prev]);
            } else {
                setLogs(prev => [{
                    timestamp: new Date().toISOString(),
                    type: 'PAYMENT',
                    message: `Payment executed for ${agentId}.`
                }, ...prev]);
            }

            fetchTreasury();
        } catch (e) {
            setMessages(prev => [...prev, { role: 'assistant', content: "Error: Failed to connect to agent." }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-indigo-500/30">
            {/* Header */}
            <header className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-xl sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                            <Activity className="w-5 h-5 text-white" />
                        </div>
                        <h1 className="font-bold text-lg tracking-tight">MNEE Nexus <span className="text-slate-500 font-normal">/ Omni-Agent</span></h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 rounded-full border border-slate-800">
                            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                            <span className="text-xs font-medium text-slate-400">Mainnet Connected</span>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-8 grid grid-cols-12 gap-8">

                {/* Left Column: Chat & Controls (8 cols) */}
                <div className="col-span-12 lg:col-span-8 space-y-6">

                    {/* Agent Selector */}
                    <div className="flex gap-4">
                        {['user-agent', 'batch-agent', 'ops-agent'].map(id => (
                            <button
                                key={id}
                                onClick={() => setAgentId(id)}
                                className={cn(
                                    "px-4 py-3 rounded-xl border text-sm font-medium transition-all flex-1 text-left",
                                    agentId === id
                                        ? "bg-indigo-600/10 border-indigo-500/50 text-indigo-400"
                                        : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                                )}
                            >
                                <div className="text-xs opacity-70 uppercase tracking-wider mb-1">Active Agent</div>
                                <div className="font-semibold">{id}</div>
                            </button>
                        ))}
                    </div>

                    {/* Chat Window */}
                    <Card className="h-[600px] flex flex-col p-0 overflow-hidden relative">
                        <div className="flex-1 overflow-y-auto p-6 space-y-6">
                            {messages.length === 0 && (
                                <div className="h-full flex flex-col items-center justify-center text-slate-600 space-y-4">
                                    <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center">
                                        <Server className="w-8 h-8 opacity-50" />
                                    </div>
                                    <p>Select an agent and start a task to see MNEE payments in action.</p>
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        <button onClick={() => setInput("Generate a cyberpunk avatar")} className="px-3 py-2 bg-slate-900 rounded-lg hover:bg-slate-800 border border-slate-800">Generate Avatar (1.0 MNEE)</button>
                                        <button onClick={() => setInput("Submit a heavy batch job")} className="px-3 py-2 bg-slate-900 rounded-lg hover:bg-slate-800 border border-slate-800">Batch Job (3.0 MNEE)</button>
                                    </div>
                                </div>
                            )}

                            {messages.map((msg, i) => (
                                <div key={i} className={cn("flex gap-4 max-w-3xl", msg.role === 'user' ? "ml-auto flex-row-reverse" : "")}>
                                    <div className={cn(
                                        "w-8 h-8 rounded-lg flex items-center justify-center shrink-0",
                                        msg.role === 'user' ? "bg-slate-800" : "bg-indigo-600"
                                    )}>
                                        {msg.role === 'user' ? <div className="w-4 h-4 bg-slate-400 rounded-full" /> : <Activity className="w-4 h-4 text-white" />}
                                    </div>
                                    <div className={cn(
                                        "px-5 py-3.5 rounded-2xl text-sm leading-relaxed",
                                        msg.role === 'user' ? "bg-slate-800 text-slate-200" : "bg-indigo-900/20 text-indigo-100 border border-indigo-500/20"
                                    )}>
                                        {msg.content}
                                    </div>
                                </div>
                            ))}
                            {loading && (
                                <div className="flex gap-4">
                                    <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shrink-0 animate-pulse">
                                        <Activity className="w-4 h-4 text-white" />
                                    </div>
                                    <div className="px-5 py-3.5 rounded-2xl bg-indigo-900/20 border border-indigo-500/20 text-sm text-indigo-300">
                                        Thinking & Paying Service Providers...
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Input Area */}
                        <div className="p-4 bg-slate-900 border-t border-slate-800">
                            <div className="flex gap-2">
                                <input
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                                    placeholder={`Command ${agentId}...`}
                                    className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                                />
                                <button
                                    onClick={sendMessage}
                                    disabled={loading || !input.trim()}
                                    className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                    <Send className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    </Card>
                </div>

                {/* Right Column: Treasury & Logs (4 cols) */}
                <div className="col-span-12 lg:col-span-4 space-y-6">

                    {/* Treasury Status */}
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

                    {/* System Logs */}
                    <Card className="flex-1 min-h-[300px]">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="font-semibold flex items-center gap-2">
                                <ShieldAlert className="w-4 h-4 text-amber-400" />
                                System Policy Log
                            </h2>
                        </div>
                        <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                            {logs.map((log, i) => (
                                <div key={i} className="text-xs p-3 rounded-lg bg-slate-950 border border-slate-800">
                                    <div className="flex justify-between text-slate-500 mb-1">
                                        <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
                                        <span className={cn("font-bold", log.type === 'REJECTED' ? "text-red-400" : "text-emerald-400")}>
                                            {log.type}
                                        </span>
                                    </div>
                                    <p className="text-slate-300 leading-relaxed">{log.message}</p>
                                </div>
                            ))}
                            {logs.length === 0 && (
                                <div className="text-center text-slate-600 py-8 text-xs">
                                    No policy events recorded yet.
                                </div>
                            )}
                        </div>
                    </Card>

                </div>
            </main>
        </div>
    );
}

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Server, Activity, Shield, AlertTriangle, CheckCircle } from 'lucide-react';
import { Card, cn } from './ui/Card';
import { LiveGraph } from './LiveGraph';
import { ChatResponse, StepRecord, GuardianAudit } from '../lib/types';

interface ChatInterfaceProps {
    onMessageSent: () => void;
}

export const ChatInterface = ({ onMessageSent }: ChatInterfaceProps) => {
    const [agentId, setAgentId] = useState('user-agent');
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<{ 
        role: string, 
        content: string, 
        timestamp?: string,
        guardian?: GuardianAudit,
        steps?: StepRecord[]
    }[]>([]);
    
    // Live Graph State
    const [graphStatus, setGraphStatus] = useState<'idle' | 'planning' | 'auditing' | 'executing' | 'finished'>('idle');
    const [activeGuardian, setActiveGuardian] = useState<GuardianAudit | undefined>(undefined);
    const [activeStep, setActiveStep] = useState<StepRecord | undefined>(undefined);
    const [loading, setLoading] = useState(false);

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMsg = { role: 'user', content: input, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);
        setGraphStatus('planning'); // Start animation
        setActiveGuardian(undefined);
        setActiveStep(undefined);

        try {
            // Call API
            const res = await axios.post<ChatResponse>('/api/chat', {
                agent_id: agentId,
                message: userMsg.content
            });

            // Simulate "Live" processing sequence for the demo effect
            
            // 1. Planning Done -> Auditing
            setTimeout(() => {
                setGraphStatus('auditing');
                setActiveGuardian(res.data.guardian);
            }, 800);

            // 2. Auditing Done -> Executing (if not blocked)
            setTimeout(() => {
                if (res.data.guardian.blocked) {
                    setGraphStatus('finished');
                } else {
                    setGraphStatus('executing');
                    if (res.data.steps.length > 0) {
                        setActiveStep(res.data.steps[0]); // Show first step
                    }
                }
            }, 2500); // Give time to read audit

            // 3. Executing Done -> Finished & Show Result
            setTimeout(() => {
                setGraphStatus('finished');
                
                setMessages(prev => [...prev, { 
                    role: 'assistant', 
                    content: res.data.response,
                    timestamp: new Date().toISOString(),
                    guardian: res.data.guardian,
                    steps: res.data.steps
                }]);

                setLoading(false);
                onMessageSent(); // Refresh dashboard stats
            }, 4000);

        } catch (e) {
            setGraphStatus('finished');
            setLoading(false);
            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: "Error: Failed to connect to agent. Please ensure backend is running.",
                timestamp: new Date().toISOString()
            }]);
        }
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[700px]">
            
            {/* Left: Chat Area (2/3) */}
            <div className="lg:col-span-2 flex flex-col space-y-4 h-full">
                
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
                <Card className="flex-1 flex flex-col p-0 overflow-hidden relative bg-slate-950/50">
                    <div className="flex-1 overflow-y-auto p-6 space-y-6">
                        {messages.length === 0 && (
                            <div className="h-full flex flex-col items-center justify-center text-slate-600 space-y-4">
                                <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center">
                                    <Server className="w-8 h-8 opacity-50" />
                                </div>
                                <p>Select an agent and start a task to see MNEE payments in action.</p>
                                <div className="grid grid-cols-2 gap-2 text-xs">
                                    <button onClick={() => setInput("Buy me a cyberpunk avatar")} className="px-3 py-2 bg-slate-900 rounded-lg hover:bg-slate-800 border border-slate-800">Buy Avatar (A2A)</button>
                                    <button onClick={() => setInput("Generate a cyberpunk avatar")} className="px-3 py-2 bg-slate-900 rounded-lg hover:bg-slate-800 border border-slate-800">Generate (Direct)</button>
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
                                
                                <div className="flex flex-col gap-2 max-w-full overflow-hidden">
                                    <div className={cn(
                                        "px-5 py-3.5 rounded-2xl text-sm leading-relaxed",
                                        msg.role === 'user' ? "bg-slate-800 text-slate-200" : "bg-indigo-900/20 text-indigo-100 border border-indigo-500/20"
                                    )}>
                                        <div className="whitespace-pre-wrap font-mono text-xs">{msg.content}</div>
                                    </div>

                                    {/* Audit Badge in Chat */}
                                    {msg.guardian && (
                                        <div className={`text-xs flex items-center gap-2 px-3 py-2 rounded-lg border ${msg.guardian.blocked ? 'bg-red-900/20 border-red-500/30 text-red-400' : 'bg-emerald-900/20 border-emerald-500/30 text-emerald-400'}`}>
                                            {msg.guardian.blocked ? <AlertTriangle className="w-3 h-3" /> : <Shield className="w-3 h-3" />}
                                            <span>Guardian Risk Score: {msg.guardian.risk_score}/10</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                        
                        {loading && (
                            <div className="flex gap-4 animate-pulse">
                                <div className="w-8 h-8 bg-slate-800 rounded-lg" />
                                <div className="h-8 bg-slate-800 rounded-lg w-32" />
                            </div>
                        )}
                    </div>

                    {/* Input Area */}
                    <div className="p-4 bg-slate-900 border-t border-slate-800">
                        <div className="flex gap-2">
                            <input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && !loading && sendMessage()}
                                placeholder={`Command ${agentId}...`}
                                disabled={loading}
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

            {/* Right: Live Graph / Command Center (1/3) */}
            <div className="lg:col-span-1 h-full">
                <Card className="h-full p-6 bg-white/5 overflow-y-auto">
                    <LiveGraph 
                        status={graphStatus}
                        guardianAudit={activeGuardian}
                        currentStep={activeStep}
                    />
                    
                    {/* Historical Audit Log (Mini) */}
                    {activeGuardian && (
                        <div className="mt-8 p-4 bg-slate-900 rounded-xl border border-slate-800 text-xs space-y-2 animate-fade-in">
                            <div className="uppercase tracking-wider text-slate-500 font-bold mb-2">Guardian Reasoning</div>
                            <p className="text-slate-300 italic leading-relaxed">"{activeGuardian.reasoning}"</p>
                        </div>
                    )}
                </Card>
            </div>

        </div>
    );
};

import React, { useState } from 'react';
import axios from 'axios';
import { Send, Server, Activity } from 'lucide-react';
import { Card, cn } from './ui/Card';
import { A2AViewer } from './A2AViewer';

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
        payment_results?: any[]
    }[]>([]);
    const [loading, setLoading] = useState(false);

    const sendMessage = async () => {
        if (!input.trim()) return;

        const userMsg = { role: 'user', content: input, timestamp: new Date().toISOString() };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await axios.post('/api/chat', {
                agent_id: agentId,
                message: userMsg.content
            });

            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: res.data.response,
                timestamp: new Date().toISOString(),
                payment_results: res.data.payment_results
            }]);

            // Refresh all data after action
            setTimeout(() => {
                onMessageSent();
            }, 500);
        } catch (e) {
            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: "Error: Failed to connect to agent. Please ensure backend is running.",
                timestamp: new Date().toISOString()
            }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">

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
                                <button onClick={() => setInput("Buy me a cyberpunk avatar")} className="px-3 py-2 bg-slate-900 rounded-lg hover:bg-slate-800 border border-slate-800">Buy Avatar (A2A)</button>
                                <button onClick={() => setInput("Generate a cyberpunk avatar")} className="px-3 py-2 bg-slate-900 rounded-lg hover:bg-slate-800 border border-slate-800">Generate (Direct)</button>
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
                            
                            <div className="flex flex-col gap-2 max-w-full overflow-hidden">
                                <div className={cn(
                                    "px-5 py-3.5 rounded-2xl text-sm leading-relaxed",
                                    msg.role === 'user' ? "bg-slate-800 text-slate-200" : "bg-indigo-900/20 text-indigo-100 border border-indigo-500/20"
                                )}>
                                    <div className="whitespace-pre-wrap font-mono text-xs">{msg.content}</div>
                                </div>

                                {/* A2A Visualization Module */}
                                {msg.payment_results && msg.payment_results.length > 0 && (
                                    <div className="w-[600px] max-w-full">
                                        <A2AViewer latestResults={msg.payment_results} />
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    
                    {loading && (
                        <div className="flex gap-4">
                            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shrink-0 animate-pulse">
                                <Activity className="w-4 h-4 text-white" />
                            </div>
                            <div className="px-5 py-3.5 rounded-2xl bg-indigo-900/20 border border-indigo-500/20 text-sm text-indigo-300">
                                Thinking & Negotiating with Agents...
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
    );
};
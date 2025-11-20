import React from 'react';
import { Activity, Send, TrendingUp, ShieldAlert, Settings } from 'lucide-react';
import { cn } from './ui/Card';

interface LayoutProps {
    children: React.ReactNode;
    activeTab: 'chat' | 'dashboard' | 'policy' | 'config';
    setActiveTab: (tab: 'chat' | 'dashboard' | 'policy' | 'config') => void;
}

export const Layout = ({ children, activeTab, setActiveTab }: LayoutProps) => {
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
                            <span className="text-xs font-medium text-slate-400">System Online</span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Tab Navigation */}
            <div className="border-b border-slate-800 bg-slate-900/30">
                <div className="max-w-7xl mx-auto px-6">
                    <div className="flex gap-1">
                        {[
                            { id: 'chat', label: 'Chat Interface', icon: Send },
                            { id: 'dashboard', label: 'Dashboard', icon: TrendingUp },
                            { id: 'policy', label: 'Policy Console', icon: ShieldAlert },
                            { id: 'config', label: 'Configuration', icon: Settings }
                        ].map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={cn(
                                    "px-4 py-3 text-sm font-medium transition-all border-b-2 flex items-center gap-2",
                                    activeTab === tab.id
                                        ? "border-indigo-500 text-indigo-400"
                                        : "border-transparent text-slate-500 hover:text-slate-300"
                                )}
                            >
                                <tab.icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <main className="max-w-7xl mx-auto px-6 py-8">
                {children}
            </main>
        </div>
    );
};

import React from 'react';
import { 
  LayoutDashboard, Users, TerminalSquare, FileJson, Wallet, Activity, 
  Package, Shield, Settings, BarChart3, RefreshCw, Lock 
} from 'lucide-react';
import clsx from 'clsx';

interface AppShellProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  treasuryBalance: number;
  onRefresh?: () => void;
  loading?: boolean;
}

export const AppShell = ({ children, activeTab, setActiveTab, treasuryBalance, onRefresh, loading }: AppShellProps) => {
  const nav = [
    { id: 'overview', icon: LayoutDashboard, label: 'Overview' },
    { id: 'fleet', icon: Users, label: 'Agent Fleet' },
    { id: 'a2a', icon: Activity, label: 'A2A Network' },
    { id: 'escrow', icon: Lock, label: 'Escrow Manager' },
    { id: 'ops', icon: TerminalSquare, label: 'Live Ops' },
    { id: 'ledger', icon: FileJson, label: 'Ledger' },
    { id: 'policy', icon: Shield, label: 'Policy Logs' },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-200">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 flex flex-col bg-slate-950/50">
        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
          <div className="w-8 h-8 bg-indigo-600 flex items-center justify-center rounded">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold tracking-tight text-white">MNEE Nexus</div>
            <div className="text-[10px] text-slate-500 uppercase font-mono">FinOps Console</div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {nav.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={clsx(
                "w-full flex items-center gap-3 px-4 py-3 rounded text-sm font-medium transition-all",
                activeTab === item.id 
                  ? "bg-slate-800 text-white border-l-2 border-indigo-500" 
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              )}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="bg-slate-900 rounded p-4 border border-slate-800">
            <div className="flex items-center gap-2 text-xs text-slate-500 uppercase font-bold mb-1">
              <Wallet className="w-3 h-3" /> Treasury
            </div>
            <div className="text-xl font-mono font-bold text-emerald-400">
              {treasuryBalance.toFixed(2)} MNEE
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-hidden flex flex-col relative bg-[url('/grid.svg')]">
        <div className="absolute inset-0 bg-slate-950 opacity-90 z-[-1]" />
        <header className="h-14 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-950/80 backdrop-blur">
          <div className="text-sm font-mono text-slate-500">SYSTEM_STATUS: <span className="text-emerald-500">ONLINE</span></div>
          <div className="flex items-center gap-4">
            {onRefresh && (
              <button 
                onClick={onRefresh}
                disabled={loading}
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded text-xs transition-colors disabled:opacity-50"
              >
                <RefreshCw className={clsx("w-3 h-3", loading && "animate-spin")} />
                Refresh
              </button>
            )}
            <div className="text-xs text-slate-600 font-mono">v1.0.0-beta</div>
          </div>
        </header>
        <div className="flex-1 overflow-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

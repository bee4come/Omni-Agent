import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  LayoutDashboard, Users, TerminalSquare, FileJson, Wallet, Activity,
  Package, Shield, Settings, BarChart3, RefreshCw, Lock, Menu, X, Wifi, WifiOff
} from 'lucide-react';
import clsx from 'clsx';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface AppShellProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  treasuryBalance: number;
  onRefresh?: () => void;
  loading?: boolean;
  connectionStatus?: ConnectionStatus;
}

export const AppShell = ({ children, activeTab, setActiveTab, treasuryBalance, onRefresh, loading, connectionStatus = 'disconnected' }: AppShellProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navRef = useRef<HTMLElement>(null);

  const nav = [
    { id: 'overview', icon: LayoutDashboard, label: 'Overview' },
    { id: 'fleet', icon: Users, label: 'Agent Fleet' },
    { id: 'a2a', icon: Activity, label: 'A2A Network' },
    { id: 'escrow', icon: Lock, label: 'Escrow Manager' },
    { id: 'ops', icon: TerminalSquare, label: 'Live Ops' },
    { id: 'ledger', icon: FileJson, label: 'Ledger' },
    { id: 'policy', icon: Shield, label: 'Policy Logs' },
  ];

  const handleNavClick = (tabId: string) => {
    setActiveTab(tabId);
    setSidebarOpen(false);
  };

  // Keyboard navigation for nav items
  const handleNavKeyDown = useCallback((e: React.KeyboardEvent, currentIndex: number) => {
    let newIndex = currentIndex;

    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
      e.preventDefault();
      newIndex = (currentIndex + 1) % nav.length;
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
      e.preventDefault();
      newIndex = currentIndex === 0 ? nav.length - 1 : currentIndex - 1;
    } else if (e.key === 'Home') {
      e.preventDefault();
      newIndex = 0;
    } else if (e.key === 'End') {
      e.preventDefault();
      newIndex = nav.length - 1;
    }

    if (newIndex !== currentIndex) {
      const buttons = navRef.current?.querySelectorAll('button[role="tab"]');
      (buttons?.[newIndex] as HTMLButtonElement)?.focus();
    }
  }, [nav.length]);

  // Close sidebar on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && sidebarOpen) {
        setSidebarOpen(false);
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [sidebarOpen]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-200">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        role="complementary"
        aria-label="Sidebar navigation"
        aria-hidden={!sidebarOpen ? 'false' : undefined}
        className={clsx(
          "fixed lg:static inset-y-0 left-0 z-50 w-64 border-r border-slate-800 flex flex-col bg-slate-950 lg:bg-slate-950/50 transform transition-transform duration-300 ease-in-out",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-600 flex items-center justify-center rounded">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="font-bold tracking-tight text-white">MNEE Nexus</div>
              <div className="text-[10px] text-slate-500 uppercase font-mono">FinOps Console</div>
            </div>
          </div>
          {/* Close button for mobile */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 text-slate-400 hover:text-white"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav
          ref={navRef}
          className="flex-1 p-4 space-y-1 overflow-y-auto"
          role="tablist"
          aria-label="Main navigation"
          aria-orientation="vertical"
        >
          {nav.map((item, index) => (
            <button
              key={item.id}
              role="tab"
              aria-selected={activeTab === item.id}
              aria-controls={`tabpanel-${item.id}`}
              tabIndex={activeTab === item.id ? 0 : -1}
              onClick={() => handleNavClick(item.id)}
              onKeyDown={(e) => handleNavKeyDown(e, index)}
              className={clsx(
                "w-full flex items-center gap-3 px-4 py-3 rounded text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-950",
                activeTab === item.id
                  ? "bg-slate-800 text-white border-l-2 border-indigo-500"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-200"
              )}
            >
              <item.icon className="w-4 h-4" aria-hidden="true" />
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
      <main
        role="main"
        id={`tabpanel-${activeTab}`}
        aria-label="Main content"
        className="flex-1 overflow-hidden flex flex-col relative bg-[url('/grid.svg')]"
      >
        <div className="absolute inset-0 bg-slate-950 opacity-90 z-[-1]" />
        <header role="banner" className="h-14 border-b border-slate-800 flex items-center justify-between px-4 lg:px-8 bg-slate-950/80 backdrop-blur">
          <div className="flex items-center gap-4">
            {/* Mobile hamburger menu */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 text-slate-400 hover:text-white"
              aria-label="Open menu"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3">
              <div className="text-sm font-mono text-slate-500">
                <span className="hidden sm:inline">SYSTEM_STATUS: </span>
                <span className="text-emerald-500">ONLINE</span>
              </div>
              {/* WebSocket Connection Status */}
              <div
                className={clsx(
                  "flex items-center gap-1.5 px-2 py-1 rounded text-xs font-mono",
                  connectionStatus === 'connected' && "bg-emerald-500/10 text-emerald-400",
                  connectionStatus === 'connecting' && "bg-amber-500/10 text-amber-400",
                  connectionStatus === 'disconnected' && "bg-slate-500/10 text-slate-400",
                  connectionStatus === 'error' && "bg-red-500/10 text-red-400"
                )}
                title={`WebSocket: ${connectionStatus}`}
              >
                {connectionStatus === 'connected' ? (
                  <Wifi className="w-3 h-3" />
                ) : (
                  <WifiOff className="w-3 h-3" />
                )}
                <span className="hidden sm:inline">
                  {connectionStatus === 'connected' ? 'LIVE' : connectionStatus === 'connecting' ? 'SYNC' : 'POLL'}
                </span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-4">
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={loading}
                className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded text-xs transition-colors disabled:opacity-50"
              >
                <RefreshCw className={clsx("w-3 h-3", loading && "animate-spin")} />
                <span className="hidden sm:inline">Refresh</span>
              </button>
            )}
            <div className="text-xs text-slate-600 font-mono hidden sm:block">v1.0.0-beta</div>
          </div>
        </header>
        <div className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

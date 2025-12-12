import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Play, Shield, CheckCircle, XCircle, Loader2, ChevronDown, Zap, Wallet, Sparkles, ArrowRight, ExternalLink } from 'lucide-react';
import { sendCommand, fetchAgents } from '../lib/api';
import { ChatResponse, StepRecord, GuardianAudit, AgentStatus, A2ATransfer, EscrowRecord } from '../lib/types';
import clsx from 'clsx';

// Demo scenarios that trigger A2A payments
const DEMO_SCENARIOS = [
  { label: 'Market Analysis', cmd: 'Analyze competitor pricing and generate report' },
  { label: 'Image Generation', cmd: 'Generate 3 marketing images for product launch' },
  { label: 'Batch Compute', cmd: 'Process ML inference on dataset batch-001' },
  { label: 'Multi-Agent Task', cmd: 'Collect market data, analyze trends, and create visual report' },
];

interface LiveOpsProps {
  onAction: () => void;
}

export const LiveOps = ({ onAction }: LiveOpsProps) => {
  const [input, setInput] = useState('');
  const [agentId, setAgentId] = useState('user-agent');
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [showAgentDropdown, setShowAgentDropdown] = useState(false);
  const [logs, setLogs] = useState<{type: 'user'|'system'|'error', content: string}[]>([]);
  const [activeTask, setActiveTask] = useState<{
    status: 'idle'|'planning'|'auditing'|'executing'|'finished';
    steps: StepRecord[];
    a2a_transfers?: A2ATransfer[];
    escrow_records?: EscrowRecord[];
    guardian?: GuardianAudit;
  }>({ status: 'idle', steps: [] });
  
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Load agents for selector
  useEffect(() => {
    const loadAgents = async () => {
      try {
        const data = await fetchAgents();
        setAgents(data.agents || []);
        if (data.agents?.length > 0 && !agentId) {
          setAgentId(data.agents[0].id);
        }
      } catch (e) {
        console.error('Failed to load agents:', e);
      }
    };
    loadAgents();
  }, []);

  const selectedAgent = agents.find(a => a.id === agentId);

  const handleSend = async () => {
    if (!input.trim()) return;
    const cmd = input;
    setInput('');
    setLogs(prev => [...prev, { type: 'user', content: `> ${cmd}` }]);
    
    setActiveTask({ status: 'planning', steps: [] });

    try {
      // Planning
      setLogs(prev => [...prev, { type: 'system', content: 'Planner: Analyzing request...' }]);
      
      // Simulate delays for UX since API is sync
      setTimeout(() => setActiveTask(p => ({...p, status: 'auditing'})), 800);
      setTimeout(() => setLogs(p => [...p, { type: 'system', content: 'Guardian: Auditing plan against Policy...' }]), 1000);

      const res: ChatResponse = await sendCommand(agentId, cmd);
      
      setTimeout(() => {
        setActiveTask(p => ({
          ...p,
          status: 'executing',
          guardian: res.guardian
        }));
        
        if (res.guardian.blocked) {
           setLogs(p => [...p, { type: 'error', content: `Guardian Blocked: ${res.guardian.reasoning}` }]);
           setActiveTask(p => ({...p, status: 'finished'}));
        } else {
           setLogs(p => [...p, { type: 'system', content: `Guardian Approved (Risk: ${res.guardian.risk_score}/10)` }]);
           
           // Show escrow locks first
           if (res.escrow_records && res.escrow_records.length > 0) {
             res.escrow_records.forEach((e, i) => {
               setTimeout(() => {
                 setLogs(p => [...p, { 
                   type: 'system', 
                   content: `[ESCROW] ${e.escrow_id}: ${e.amount.toFixed(2)} MNEE locked (${e.customer_agent} -> ${e.merchant_agent})` 
                 }]);
               }, i * 200);
             });
             setActiveTask(p => ({...p, escrow_records: res.escrow_records}));
           }
           
           // Show A2A transfers
           if (res.a2a_transfers && res.a2a_transfers.length > 0) {
             const escrowDelay = (res.escrow_records?.length || 0) * 200;
             res.a2a_transfers.forEach((t, i) => {
               setTimeout(() => {
                 const txLink = t.tx_hash ? ` [TX: ${t.tx_hash.slice(0, 10)}...]` : '';
                 setLogs(p => [...p, { 
                   type: 'system', 
                   content: `[A2A] ${t.from_agent} -> ${t.to_agent}: ${t.amount.toFixed(3)} MNEE${txLink}` 
                 }]);
               }, escrowDelay + i * 300);
             });
             setActiveTask(p => ({...p, a2a_transfers: res.a2a_transfers}));
           }
           
           // Show steps
           const totalDelay = ((res.escrow_records?.length || 0) * 200) + ((res.a2a_transfers?.length || 0) * 300);
           if (res.steps) {
             setActiveTask(p => ({...p, steps: res.steps, status: 'executing'}));
             res.steps.forEach((s, i) => {
                setTimeout(() => {
                   setLogs(p => [...p, { type: 'system', content: `Executor: Running ${s.tool_name}...` }]);
                }, 500 + totalDelay);
             });
           }
           setTimeout(() => {
             setLogs(p => [...p, { type: 'system', content: `Result: ${res.response}` }]);
             setActiveTask(p => ({...p, status: 'finished'}));
             onAction();
           }, 2000 + totalDelay);
        }
      }, 2000);

    } catch (e) {
      setLogs(prev => [...prev, { type: 'error', content: 'Connection Error' }]);
      setActiveTask({ status: 'idle', steps: [] });
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[600px]">
      {/* Left: Terminal */}
      <div className="lg:col-span-2 flex flex-col bg-slate-950 border border-slate-800 rounded overflow-hidden font-mono text-sm">
        <div className="bg-slate-900 p-2 px-4 border-b border-slate-800 flex justify-between items-center">
          <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500" />
            <div className="w-3 h-3 rounded-full bg-amber-500/20 border border-amber-500" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/20 border border-emerald-500" />
          </div>
          
          {/* Agent Selector */}
          <div className="relative">
            <button
              onClick={() => setShowAgentDropdown(!showAgentDropdown)}
              className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded text-xs transition-colors"
            >
              <Zap className="w-3 h-3 text-indigo-400" />
              <span className="text-slate-300">{agentId}</span>
              {selectedAgent && (
                <span className="text-emerald-400 font-mono">
                  {selectedAgent.remainingBudget?.toFixed(1) || (selectedAgent.dailyBudget - selectedAgent.currentDailySpend).toFixed(1)} MNEE
                </span>
              )}
              <ChevronDown className="w-3 h-3 text-slate-500" />
            </button>
            
            {showAgentDropdown && (
              <div className="absolute right-0 top-full mt-1 w-64 bg-slate-900 border border-slate-700 rounded-lg shadow-xl z-50 overflow-hidden">
                <div className="p-2 border-b border-slate-800 text-[10px] text-slate-500 uppercase font-bold">
                  Select Agent
                </div>
                <div className="max-h-48 overflow-y-auto">
                  {agents.map(agent => {
                    const remaining = agent.dailyBudget - agent.currentDailySpend;
                    const percentage = (agent.currentDailySpend / agent.dailyBudget) * 100;
                    return (
                      <button
                        key={agent.id}
                        onClick={() => {
                          setAgentId(agent.id);
                          setShowAgentDropdown(false);
                        }}
                        className={clsx(
                          "w-full px-3 py-2 flex items-center justify-between hover:bg-slate-800 transition-colors",
                          agent.id === agentId && "bg-slate-800"
                        )}
                      >
                        <div className="flex items-center gap-2">
                          <div className={clsx(
                            "w-2 h-2 rounded-full",
                            percentage > 90 ? "bg-red-500" : percentage > 50 ? "bg-amber-500" : "bg-emerald-500"
                          )} />
                          <span className="text-sm text-slate-300">{agent.id}</span>
                          <span className={clsx(
                            "text-[10px] px-1.5 py-0.5 rounded uppercase font-bold",
                            agent.priority === 'HIGH' ? "bg-red-500/20 text-red-400" :
                            agent.priority === 'MEDIUM' ? "bg-amber-500/20 text-amber-400" :
                            "bg-slate-700 text-slate-400"
                          )}>
                            {agent.priority}
                          </span>
                        </div>
                        <span className="text-xs font-mono text-emerald-400">
                          {remaining.toFixed(1)}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex-1 p-4 overflow-y-auto space-y-2 text-slate-300 scanline">
          <div className="text-slate-500 mb-4">MNEE Nexus Protocol v1.0.0 initialized...</div>
          {logs.map((l, i) => (
            <div key={i} className={clsx(
              l.type === 'user' ? 'text-emerald-400' : l.type === 'error' ? 'text-red-400' : 'text-slate-300'
            )}>
              {l.content}
            </div>
          ))}
          <div ref={logEndRef} />
        </div>

        {/* Demo Scenarios */}
        <div className="px-4 py-2 bg-slate-900/50 border-t border-slate-800 flex gap-2 overflow-x-auto">
          <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1 mr-2">
            <Sparkles className="w-3 h-3" /> Demo:
          </span>
          {DEMO_SCENARIOS.map((scenario, i) => (
            <button
              key={i}
              onClick={() => {
                setInput(scenario.cmd);
              }}
              className="px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded text-[10px] text-slate-400 hover:text-slate-200 transition-colors whitespace-nowrap"
            >
              {scenario.label}
            </button>
          ))}
        </div>

        <div className="p-4 bg-slate-900 border-t border-slate-800 flex gap-2">
          <span className="text-emerald-500 font-bold">{'>'}</span>
          <input 
            className="flex-1 bg-transparent focus:outline-none text-slate-200"
            autoFocus
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Enter command..."
          />
        </div>
      </div>

      {/* Right: Process Monitor */}
      <div className="bg-slate-900 border border-slate-800 rounded p-6 space-y-6">
        <div className="uppercase tracking-wider text-xs font-bold text-slate-500 mb-4">System Monitor</div>
        
        {/* Status Steps */}
        <div className="space-y-4 relative">
          <div className="absolute left-3 top-2 bottom-2 w-0.5 bg-slate-800 -z-10" />
          
          <StepItem status={activeTask.status === 'idle' ? 'waiting' : 'done'} label="Planner" desc="Decompose goal" />
          <StepItem status={activeTask.status === 'auditing' ? 'active' : activeTask.status === 'idle' || activeTask.status === 'planning' ? 'waiting' : 'done'} label="Guardian" desc="Risk Audit" />
          <StepItem status={activeTask.status === 'executing' ? 'active' : activeTask.status === 'finished' ? 'done' : 'waiting'} label="Executor" desc="Run Tools" />
        </div>

        {/* Guardian Detail */}
        {activeTask.guardian && (
          <div className={clsx("mt-6 p-4 rounded border text-xs", activeTask.guardian.blocked ? "bg-red-950/30 border-red-900 text-red-400" : "bg-emerald-950/30 border-emerald-900 text-emerald-400")}>
            <div className="flex items-center gap-2 font-bold mb-1">
              <Shield className="w-4 h-4" /> Risk Score: {activeTask.guardian.risk_score}/10
            </div>
            <p className="opacity-80">{activeTask.guardian.reasoning}</p>
          </div>
        )}

        {/* A2A Transfers */}
        {activeTask.a2a_transfers && activeTask.a2a_transfers.length > 0 && (
          <div className="mt-6">
            <div className="text-[10px] uppercase font-bold text-slate-500 mb-3 flex items-center gap-2">
              <ArrowRight className="w-3 h-3" /> A2A Payments
            </div>
            <div className="space-y-2">
              {activeTask.a2a_transfers.map((t, i) => (
                <div key={i} className="bg-purple-950/30 border border-purple-900/50 rounded p-3 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-1 text-purple-300">
                      <span className="font-mono">{t.from_agent.split('-')[0]}</span>
                      <ArrowRight className="w-3 h-3 text-purple-500" />
                      <span className="font-mono">{t.to_agent.split('-')[0]}</span>
                    </div>
                    <span className="font-mono font-bold text-emerald-400">
                      {t.amount.toFixed(3)} MNEE
                    </span>
                  </div>
                  <div className="text-slate-500 text-[10px] truncate">{t.task_description}</div>
                  {t.tx_hash && (
                    <a 
                      href={`https://etherscan.io/tx/${t.tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-[10px] text-indigo-400 hover:underline mt-1"
                    >
                      <ExternalLink className="w-2.5 h-2.5" />
                      {t.tx_hash.slice(0, 16)}...
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const StepItem = ({ status, label, desc }: { status: 'waiting'|'active'|'done', label: string, desc: string }) => (
  <div className="flex gap-4 items-center">
    <div className={clsx(
      "w-6 h-6 rounded-full flex items-center justify-center border-2 bg-slate-900 z-10 transition-all",
      status === 'active' ? "border-indigo-500 text-indigo-500 animate-pulse" : 
      status === 'done' ? "border-emerald-500 bg-emerald-500 text-slate-950" : "border-slate-700 text-slate-700"
    )}>
      {status === 'active' ? <Loader2 className="w-3 h-3 animate-spin" /> : status === 'done' ? <CheckCircle className="w-3 h-3" /> : <div className="w-2 h-2 rounded-full bg-slate-700" />}
    </div>
    <div>
      <div className={clsx("text-sm font-bold", status === 'active' ? "text-indigo-400" : status === 'done' ? "text-slate-200" : "text-slate-600")}>{label}</div>
      <div className="text-xs text-slate-500">{desc}</div>
    </div>
  </div>
);

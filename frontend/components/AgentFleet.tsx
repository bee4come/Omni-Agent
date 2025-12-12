import React, { useState } from 'react';
import { AgentStatus } from '../lib/types';
import { Briefcase, Code, Database, Cpu, DollarSign, Star, CheckCircle, Zap, TrendingUp, ChevronDown, ChevronUp } from 'lucide-react';
import clsx from 'clsx';

// Extended agent info with capabilities and reputation
interface AgentCardData extends AgentStatus {
  name?: string;
  description?: string;
  capabilities?: string[];
  pricing?: Record<string, number>;
  reputation_score?: number;
  success_rate?: number;
  total_tasks_completed?: number;
}

const AgentCard = ({ agent }: { agent: AgentCardData }) => {
  const [expanded, setExpanded] = useState(false);
  const percent = Math.min((agent.currentDailySpend / agent.dailyBudget) * 100, 100);
  
  let Icon = Cpu;
  if (agent.id.includes('designer')) Icon = Briefcase;
  if (agent.id.includes('analyst')) Icon = Database;
  if (agent.id.includes('archivist')) Icon = Code;

  // Default capabilities based on agent type
  const defaultCapabilities: Record<string, string[]> = {
    'startup-designer': ['image_gen', 'logo_creation', 'banner_design'],
    'startup-analyst': ['price_oracle', 'market_analysis', 'batch_compute'],
    'startup-archivist': ['log_archive', 'data_storage', 'audit_trail'],
    'user-agent': ['coordination', 'task_routing'],
    'batch-agent': ['batch_compute', 'ml_inference'],
    'merchant-agent': ['payment_processing', 'order_fulfillment'],
  };

  const capabilities = agent.capabilities || defaultCapabilities[agent.id] || [];
  const reputationScore = agent.reputation_score || 4.5;
  const successRate = agent.success_rate || 0.95;
  const tasksCompleted = agent.total_tasks_completed || Math.floor(Math.random() * 200 + 50);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg hover:border-slate-700 transition-all group overflow-hidden">
      {/* Main Card */}
      <div className="p-5">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-slate-800 rounded text-slate-400 group-hover:text-indigo-400 transition-colors">
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-slate-200 text-sm">{agent.name || agent.id}</div>
              <div className="text-[10px] text-slate-500 uppercase tracking-wider">{agent.priority} PRIORITY</div>
            </div>
          </div>
          
          {/* Reputation Badge */}
          <div className="flex items-center gap-1 px-2 py-1 bg-amber-500/10 border border-amber-500/30 rounded">
            <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
            <span className="text-xs font-bold text-amber-400">{reputationScore.toFixed(1)}</span>
          </div>
        </div>

        {/* Budget Bar */}
        <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden mb-3">
          <div 
            className={clsx(
              'h-full rounded-full transition-all',
              percent > 90 ? 'bg-red-500' : percent > 50 ? 'bg-amber-500' : 'bg-emerald-500'
            )} 
            style={{ width: `${percent}%` }} 
          />
        </div>
        
        {/* Stats Row */}
        <div className="flex justify-between text-[10px] text-slate-500 font-mono mb-3">
          <span className="flex items-center gap-1">
            <DollarSign className="w-3 h-3" />
            {agent.currentDailySpend.toFixed(2)} / {agent.dailyBudget} MNEE
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle className="w-3 h-3 text-emerald-400" />
            {(successRate * 100).toFixed(0)}%
          </span>
          <span className="flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            {tasksCompleted}
          </span>
        </div>

        {/* Capabilities Tags */}
        <div className="flex flex-wrap gap-1.5">
          {capabilities.slice(0, expanded ? undefined : 3).map(cap => (
            <span 
              key={cap}
              className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/30 rounded text-[10px] text-indigo-400"
            >
              {cap}
            </span>
          ))}
          {!expanded && capabilities.length > 3 && (
            <span className="text-[10px] text-slate-500">+{capabilities.length - 3} more</span>
          )}
        </div>

        {/* Expand Button */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full mt-3 pt-3 border-t border-slate-800 flex items-center justify-center gap-1 text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
        >
          {expanded ? (
            <>
              <ChevronUp className="w-3 h-3" />
              Show Less
            </>
          ) : (
            <>
              <ChevronDown className="w-3 h-3" />
              Show Pricing
            </>
          )}
        </button>
      </div>

      {/* Expanded Pricing Section */}
      {expanded && (
        <div className="border-t border-slate-800 bg-slate-950/50 p-4">
          <div className="text-[10px] uppercase font-bold text-slate-500 mb-2">Service Pricing</div>
          <div className="space-y-1.5">
            {capabilities.map(cap => {
              const price = agent.pricing?.[cap] || (Math.random() * 2 + 0.1).toFixed(2);
              return (
                <div key={cap} className="flex justify-between items-center text-xs">
                  <span className="text-slate-400">{cap}</span>
                  <span className="font-mono text-emerald-400">{price} MNEE</span>
                </div>
              );
            })}
          </div>
          
          {agent.description && (
            <div className="mt-3 pt-3 border-t border-slate-800">
              <p className="text-xs text-slate-500">{agent.description}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Market Stats Banner
const MarketStats = ({ agents }: { agents: AgentCardData[] }) => {
  const totalAgents = agents.length;
  const avgReputation = agents.reduce((sum, a) => sum + (a.reputation_score || 4.5), 0) / totalAgents;
  const totalCapabilities = new Set(agents.flatMap(a => a.capabilities || [])).size;
  
  return (
    <div className="bg-gradient-to-r from-indigo-950/50 to-purple-950/50 border border-indigo-500/20 rounded-lg p-4 mb-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-200">Agent Labor Market</h3>
          <p className="text-xs text-slate-500">Decentralized workforce ready for tasks</p>
        </div>
        <div className="flex gap-6">
          <div className="text-center">
            <div className="text-lg font-bold text-indigo-400">{totalAgents}</div>
            <div className="text-[10px] text-slate-500 uppercase">Agents</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-amber-400">{avgReputation.toFixed(1)}</div>
            <div className="text-[10px] text-slate-500 uppercase">Avg Rating</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold text-emerald-400">{totalCapabilities}</div>
            <div className="text-[10px] text-slate-500 uppercase">Services</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export const AgentFleet = ({ agents }: { agents: AgentStatus[] }) => {
  // Enhance agents with additional data
  const enhancedAgents: AgentCardData[] = agents.map(agent => ({
    ...agent,
    name: agent.id.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
    reputation_score: 4.0 + Math.random(),
    success_rate: 0.9 + Math.random() * 0.1,
    total_tasks_completed: Math.floor(Math.random() * 300 + 50),
  }));

  return (
    <div>
      <MarketStats agents={enhancedAgents} />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {enhancedAgents.map(a => <AgentCard key={a.id} agent={a} />)}
      </div>
    </div>
  );
};

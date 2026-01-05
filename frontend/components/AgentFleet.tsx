import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { AgentStatus } from '../lib/types';
import { Briefcase, Code, Database, Cpu, DollarSign, Star, CheckCircle, Zap, TrendingUp, ChevronDown, ChevronUp, Settings, Pause, Play, X } from 'lucide-react';
import clsx from 'clsx';
import { updateAgentBudget, pauseAgent, resumeAgent } from '../lib/api';

// Simple hash function to generate deterministic values from agent ID
function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}

// Get deterministic pseudo-random value between 0 and 1 based on agent ID and seed
function seededRandom(agentId: string, seed: string): number {
  const hash = hashCode(agentId + seed);
  return (hash % 1000) / 1000;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
} as const;

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: 'spring' as const,
      stiffness: 100,
      damping: 12,
    },
  },
};

// Extended agent info with capabilities and reputation
interface AgentCardData extends AgentStatus {
  name?: string;
  description?: string;
  capabilities?: string[];
  pricing?: Record<string, number>;
  reputation_score?: number;
  success_rate?: number;
  total_tasks_completed?: number;
  paused?: boolean;
}

interface AgentCardProps {
  agent: AgentCardData;
  onBudgetUpdate?: (agentId: string, newBudget: number) => void;
  onPauseToggle?: (agentId: string, paused: boolean) => void;
}

const AgentCard = ({ agent, onBudgetUpdate, onPauseToggle }: AgentCardProps) => {
  const [expanded, setExpanded] = useState(false);
  const [showBudgetModal, setShowBudgetModal] = useState(false);
  const [newBudget, setNewBudget] = useState(agent.dailyBudget.toString());
  const [isPaused, setIsPaused] = useState(agent.paused ?? false);
  const [updating, setUpdating] = useState(false);
  const [pauseUpdating, setPauseUpdating] = useState(false);
  const percent = Math.min((agent.currentDailySpend / agent.dailyBudget) * 100, 100);

  let Icon = Cpu;
  if (agent.id.includes('designer')) Icon = Briefcase;
  if (agent.id.includes('analyst')) Icon = Database;
  if (agent.id.includes('archivist')) Icon = Code;

  const handleBudgetUpdate = async () => {
    const budget = parseFloat(newBudget);
    if (isNaN(budget) || budget <= 0) {
      toast.error('Please enter a valid budget amount');
      return;
    }
    setUpdating(true);
    try {
      await updateAgentBudget(agent.id, budget);
      toast.success(`Budget updated to ${budget} MNEE`);
      onBudgetUpdate?.(agent.id, budget);
      setShowBudgetModal(false);
    } catch (e) {
      toast.error('Failed to update budget');
    } finally {
      setUpdating(false);
    }
  };

  const handlePauseToggle = async () => {
    setPauseUpdating(true);
    try {
      if (isPaused) {
        await resumeAgent(agent.id);
        toast.success(`${agent.id} resumed`);
      } else {
        await pauseAgent(agent.id);
        toast.success(`${agent.id} paused`);
      }
      setIsPaused(!isPaused);
      onPauseToggle?.(agent.id, !isPaused);
    } catch (e) {
      toast.error('Failed to update agent status');
    } finally {
      setPauseUpdating(false);
    }
  };

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
  const reputationScore = agent.reputation_score ?? 4.5;
  const successRate = agent.success_rate ?? 0.95;
  const tasksCompleted = agent.total_tasks_completed ?? Math.floor(seededRandom(agent.id, 'tasks') * 200 + 50);

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

        {/* Action Buttons */}
        <div className="flex gap-2 mt-3 pt-3 border-t border-slate-800">
          <button
            onClick={() => setShowBudgetModal(true)}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded text-xs text-slate-300 transition-colors"
            aria-label={`Edit budget for ${agent.id}`}
          >
            <Settings className="w-3 h-3" />
            Edit Budget
          </button>
          <button
            onClick={handlePauseToggle}
            disabled={pauseUpdating}
            className={clsx(
              "flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded text-xs transition-colors disabled:opacity-50",
              isPaused
                ? "bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-600/30"
                : "bg-amber-600/20 hover:bg-amber-600/30 text-amber-400 border border-amber-600/30"
            )}
            aria-label={isPaused ? `Resume ${agent.id}` : `Pause ${agent.id}`}
          >
            {isPaused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
            {pauseUpdating ? 'Updating...' : isPaused ? 'Resume' : 'Pause'}
          </button>
        </div>

        {/* Expand Button */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full mt-2 flex items-center justify-center gap-1 text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
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

      {/* Budget Edit Modal */}
      <AnimatePresence>
        {showBudgetModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
            onClick={() => setShowBudgetModal(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-slate-900 border border-slate-700 rounded-lg p-6 w-full max-w-sm mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-slate-200">Edit Budget</h3>
                <button
                  onClick={() => setShowBudgetModal(false)}
                  className="p-1 text-slate-400 hover:text-white"
                  aria-label="Close modal"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-sm text-slate-400 mb-4">
                Set daily budget for <span className="text-indigo-400 font-mono">{agent.id}</span>
              </p>
              <div className="mb-4">
                <label htmlFor="budget-input" className="block text-xs text-slate-500 uppercase font-bold mb-2">
                  Daily Budget (MNEE)
                </label>
                <input
                  id="budget-input"
                  type="number"
                  step="0.1"
                  min="0"
                  value={newBudget}
                  onChange={(e) => setNewBudget(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                  placeholder="Enter budget amount"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowBudgetModal(false)}
                  className="flex-1 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm text-slate-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleBudgetUpdate}
                  disabled={updating}
                  className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded text-sm text-white transition-colors disabled:opacity-50"
                >
                  {updating ? 'Updating...' : 'Save'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Expanded Pricing Section */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="border-t border-slate-800 bg-slate-950/50 p-4">
              <div className="text-[10px] uppercase font-bold text-slate-500 mb-2">Service Pricing</div>
              <div className="space-y-1.5">
                {capabilities.map(cap => {
                  const price = agent.pricing?.[cap] ?? (seededRandom(agent.id, cap) * 2 + 0.1).toFixed(2);
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
          </motion.div>
        )}
      </AnimatePresence>
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
  // Enhance agents with additional data (memoized to prevent recalculation)
  const enhancedAgents: AgentCardData[] = useMemo(() => agents.map(agent => ({
    ...agent,
    name: agent.id.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
    reputation_score: 4.0 + seededRandom(agent.id, 'reputation'),
    success_rate: 0.9 + seededRandom(agent.id, 'success') * 0.1,
    total_tasks_completed: Math.floor(seededRandom(agent.id, 'tasks') * 300 + 50),
  })), [agents]);

  // Empty state
  if (agents.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-12 text-center">
        <Cpu className="w-12 h-12 text-slate-600 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-slate-400 mb-2">No Agents Configured</h3>
        <p className="text-sm text-slate-500 max-w-md mx-auto">
          Configure agents in config/agents.yaml to see them here.
          Each agent can have its own budget, priority, and capabilities.
        </p>
      </div>
    );
  }

  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <MarketStats agents={enhancedAgents} />
      </motion.div>
      <motion.div
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {enhancedAgents.map(a => (
          <motion.div key={a.id} variants={itemVariants}>
            <AgentCard agent={a} />
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
};

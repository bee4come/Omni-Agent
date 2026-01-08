import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import {
  Play,
  RefreshCw,
  ChevronDown,
  GitBranch,
  Clock,
  CheckCircle,
  Loader2,
  Zap,
  FileText,
  BarChart3,
  Coins,
  User,
  Users,
} from 'lucide-react';
import clsx from 'clsx';
import {
  fetchWorkflowTemplates,
  startWorkflow,
  fetchWorkflowInstances,
  fetchWorkflowInstance,
  fetchAgents,
  fetchAgentBids,
} from '../lib/api';
import { WorkflowTemplate, WorkflowInstance, AgentStatus, BidInfo } from '../lib/types';
import { WorkflowView } from './WorkflowView';
import { AgentBidding } from './AgentBidding';

interface WorkflowDemoProps {
  onWorkflowComplete?: () => void;
}

// Template icons
const getTemplateIcon = (workflowId: string) => {
  if (workflowId.includes('content')) return FileText;
  if (workflowId.includes('data') || workflowId.includes('analysis')) return BarChart3;
  return GitBranch;
};

export const WorkflowDemo = ({ onWorkflowComplete }: WorkflowDemoProps) => {
  // State
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);
  const [showTemplateDropdown, setShowTemplateDropdown] = useState(false);

  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('user-agent');
  const [showAgentDropdown, setShowAgentDropdown] = useState(false);

  const [instances, setInstances] = useState<WorkflowInstance[]>([]);
  const [activeInstance, setActiveInstance] = useState<WorkflowInstance | null>(null);

  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [pollingId, setPollingId] = useState<NodeJS.Timeout | null>(null);

  // Coordination phase state
  const [showCoordination, setShowCoordination] = useState(false);
  const [coordinationBids, setCoordinationBids] = useState<BidInfo[]>([]);
  const [coordinationStep, setCoordinationStep] = useState(0);

  // Load templates and agents on mount
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const [templatesRes, agentsRes, instancesRes] = await Promise.all([
          fetchWorkflowTemplates(),
          fetchAgents(),
          fetchWorkflowInstances(),
        ]);

        setTemplates(templatesRes.templates || []);
        setAgents(agentsRes.agents || []);
        setInstances(instancesRes.instances || []);

        // Auto-select first template
        if (templatesRes.templates?.length > 0 && !selectedTemplate) {
          setSelectedTemplate(templatesRes.templates[0]);
        }
      } catch (e) {
        console.error('Failed to load workflow data:', e);
        toast.error('Failed to load workflow data');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingId) clearInterval(pollingId);
    };
  }, [pollingId]);

  // Poll active instance for updates
  const pollInstance = useCallback(async (instanceId: string) => {
    try {
      const data = await fetchWorkflowInstance(instanceId);
      if (data) {
        setActiveInstance(data);

        // Stop polling if completed or failed
        if (data.status === 'completed' || data.status === 'failed') {
          if (pollingId) {
            clearInterval(pollingId);
            setPollingId(null);
          }

          if (data.status === 'completed') {
            toast.success('Workflow completed successfully!');
            onWorkflowComplete?.();
          } else {
            toast.error('Workflow failed');
          }
        }
      }
    } catch (e) {
      console.error('Failed to poll instance:', e);
    }
  }, [pollingId, onWorkflowComplete]);

  // Fetch bids for all capabilities in template
  const fetchAllBids = async () => {
    if (!selectedTemplate) return [];

    const capabilities = selectedTemplate.steps.map(s => s.capability);
    const uniqueCapabilities = Array.from(new Set(capabilities));

    const bids: BidInfo[] = [];
    for (const capability of uniqueCapabilities) {
      try {
        const bidInfo = await fetchAgentBids(capability);
        bids.push(bidInfo);
      } catch (e) {
        console.error(`Failed to fetch bids for ${capability}:`, e);
      }
    }
    return bids;
  };

  // Start workflow with coordination phase
  const handleStartWorkflow = async () => {
    if (!selectedTemplate) {
      toast.error('Please select a workflow template');
      return;
    }

    setStarting(true);

    // Phase 1: Show coordination (agent bidding)
    try {
      const bids = await fetchAllBids();
      setCoordinationBids(bids);
      setShowCoordination(true);
      setCoordinationStep(0);

      // Animate through each capability's bidding
      for (let i = 0; i < bids.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        setCoordinationStep(i + 1);
      }

      // Wait for final animation
      await new Promise(resolve => setTimeout(resolve, 1500));
    } catch (e) {
      console.error('Coordination phase failed:', e);
    }

    // Phase 2: Actually start the workflow
    try {
      const result = await startWorkflow(
        selectedTemplate.workflow_id,
        selectedAgent,
        { topic: 'AI Agent Payment Demo' }
      );

      if (result.instance) {
        setActiveInstance(result.instance);
        setInstances(prev => [result.instance, ...prev]);
        setShowCoordination(false);
        toast.success('Workflow started!');

        // Start polling for updates
        const id = setInterval(() => pollInstance(result.instance.instance_id), 1000);
        setPollingId(id);
      }
    } catch (e) {
      console.error('Failed to start workflow:', e);
      toast.error('Failed to start workflow');
      setShowCoordination(false);
    } finally {
      setStarting(false);
    }
  };

  // Refresh instances
  const handleRefresh = async () => {
    setLoading(true);
    try {
      const data = await fetchWorkflowInstances();
      setInstances(data.instances || []);
    } catch (e) {
      console.error('Failed to refresh instances:', e);
    } finally {
      setLoading(false);
    }
  };

  const selectedAgentData = agents.find(a => a.id === selectedAgent);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-200">Workflow Orchestration</h2>
          <p className="text-xs text-slate-500">Multi-agent collaboration with escrow handoffs</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="p-2 hover:bg-slate-800 rounded transition-colors"
        >
          <RefreshCw className={clsx('w-4 h-4 text-slate-400', loading && 'animate-spin')} />
        </button>
      </div>

      {/* Control Panel */}
      <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
        <div className="flex flex-col lg:flex-row gap-4">
          {/* Template Selector */}
          <div className="flex-1">
            <label className="block text-[10px] uppercase font-bold text-slate-500 mb-2">
              Workflow Template
            </label>
            <div className="relative">
              <button
                onClick={() => setShowTemplateDropdown(!showTemplateDropdown)}
                className="w-full flex items-center justify-between px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg hover:border-slate-600 transition-colors"
              >
                {selectedTemplate ? (
                  <div className="flex items-center gap-3">
                    {React.createElement(getTemplateIcon(selectedTemplate.workflow_id), {
                      className: 'w-4 h-4 text-indigo-400',
                    })}
                    <div className="text-left">
                      <div className="text-sm text-slate-200">{selectedTemplate.name}</div>
                      <div className="text-[10px] text-slate-500">
                        {selectedTemplate.step_count} steps | {selectedTemplate.total_cost.toFixed(2)} MNEE
                      </div>
                    </div>
                  </div>
                ) : (
                  <span className="text-slate-400">Select template...</span>
                )}
                <ChevronDown className="w-4 h-4 text-slate-500" />
              </button>

              <AnimatePresence>
                {showTemplateDropdown && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute z-50 w-full mt-2 bg-slate-900 border border-slate-700 rounded-lg shadow-xl overflow-hidden"
                  >
                    {templates.map(template => {
                      const Icon = getTemplateIcon(template.workflow_id);
                      return (
                        <button
                          key={template.workflow_id}
                          onClick={() => {
                            setSelectedTemplate(template);
                            setShowTemplateDropdown(false);
                          }}
                          className={clsx(
                            'w-full px-4 py-3 flex items-center gap-3 hover:bg-slate-800 transition-colors text-left',
                            selectedTemplate?.workflow_id === template.workflow_id && 'bg-slate-800'
                          )}
                        >
                          <Icon className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="text-sm text-slate-200">{template.name}</div>
                            <div className="text-[10px] text-slate-500 truncate">
                              {template.description}
                            </div>
                          </div>
                          <div className="flex items-center gap-1 text-[10px] text-emerald-400">
                            <Coins className="w-3 h-3" />
                            {template.total_cost.toFixed(2)}
                          </div>
                        </button>
                      );
                    })}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Agent Selector */}
          <div className="lg:w-48">
            <label className="block text-[10px] uppercase font-bold text-slate-500 mb-2">
              Customer Agent
            </label>
            <div className="relative">
              <button
                onClick={() => setShowAgentDropdown(!showAgentDropdown)}
                className="w-full flex items-center justify-between px-4 py-3 bg-slate-900 border border-slate-700 rounded-lg hover:border-slate-600 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4 text-indigo-400" />
                  <span className="text-sm text-slate-200">{selectedAgent}</span>
                </div>
                <ChevronDown className="w-4 h-4 text-slate-500" />
              </button>

              <AnimatePresence>
                {showAgentDropdown && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="absolute z-50 w-full mt-2 bg-slate-900 border border-slate-700 rounded-lg shadow-xl overflow-hidden max-h-48 overflow-y-auto"
                  >
                    {agents.map(agent => (
                      <button
                        key={agent.id}
                        onClick={() => {
                          setSelectedAgent(agent.id);
                          setShowAgentDropdown(false);
                        }}
                        className={clsx(
                          'w-full px-4 py-2 flex items-center justify-between hover:bg-slate-800 transition-colors',
                          selectedAgent === agent.id && 'bg-slate-800'
                        )}
                      >
                        <span className="text-sm text-slate-300">{agent.id}</span>
                        <span className="text-[10px] font-mono text-emerald-400">
                          {(agent.dailyBudget - agent.currentDailySpend).toFixed(1)}
                        </span>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Start Button */}
          <div className="lg:w-40">
            <label className="block text-[10px] uppercase font-bold text-slate-500 mb-2">
              &nbsp;
            </label>
            <button
              onClick={handleStartWorkflow}
              disabled={!selectedTemplate || starting || (activeInstance?.status === 'running')}
              className={clsx(
                'w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-bold text-sm transition-all',
                !selectedTemplate || starting || (activeInstance?.status === 'running')
                  ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                  : 'bg-indigo-600 hover:bg-indigo-500 text-white'
              )}
            >
              {starting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Starting...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  Start Workflow
                </>
              )}
            </button>
          </div>
        </div>

        {/* Selected Agent Budget Info */}
        {selectedAgentData && (
          <div className="mt-4 pt-4 border-t border-slate-700 flex items-center gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-1">
              <Zap className="w-3 h-3" />
              <span>Budget: </span>
              <span className="font-mono text-emerald-400">
                {(selectedAgentData.dailyBudget - selectedAgentData.currentDailySpend).toFixed(2)} MNEE
              </span>
              <span className="text-slate-600">/ {selectedAgentData.dailyBudget.toFixed(2)}</span>
            </div>
            {selectedTemplate && selectedAgentData.dailyBudget - selectedAgentData.currentDailySpend < selectedTemplate.total_cost && (
              <span className="text-amber-400">
                Insufficient budget for this workflow
              </span>
            )}
          </div>
        )}
      </div>

      {/* Coordination Phase - Agent Bidding */}
      <AnimatePresence>
        {showCoordination && coordinationBids.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="bg-slate-800/30 border border-indigo-500/30 rounded-lg p-4"
          >
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center animate-pulse">
                <Users className="w-4 h-4 text-indigo-400" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-indigo-400">Agent Coordination Phase</h3>
                <p className="text-[10px] text-slate-500">
                  Step {Math.min(coordinationStep + 1, coordinationBids.length)} of {coordinationBids.length} capabilities
                </p>
              </div>
            </div>

            {coordinationBids.map((bidInfo, index) => (
              <motion.div
                key={bidInfo.capability}
                initial={{ opacity: 0, height: 0 }}
                animate={{
                  opacity: index <= coordinationStep ? 1 : 0.3,
                  height: 'auto',
                }}
                className="mb-4 last:mb-0"
              >
                <AgentBidding
                  bidInfo={bidInfo}
                  showAnimation={index === coordinationStep}
                />
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Active Workflow Visualization */}
      {!showCoordination && (activeInstance || selectedTemplate) && (
        <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4">
          <WorkflowView
            template={!activeInstance ? selectedTemplate || undefined : undefined}
            instance={activeInstance || undefined}
          />
        </div>
      )}

      {/* Recent Instances */}
      {instances.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-slate-400">Recent Workflows</h3>
          <div className="grid gap-2">
            {instances.slice(0, 5).map(instance => (
              <motion.button
                key={instance.instance_id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                onClick={() => setActiveInstance(instance)}
                className={clsx(
                  'w-full flex items-center justify-between p-3 bg-slate-900/50 border rounded-lg text-left transition-colors',
                  activeInstance?.instance_id === instance.instance_id
                    ? 'border-indigo-500 bg-indigo-500/10'
                    : 'border-slate-700 hover:border-slate-600'
                )}
              >
                <div className="flex items-center gap-3">
                  <div className={clsx(
                    'w-2 h-2 rounded-full',
                    instance.status === 'completed' && 'bg-emerald-500',
                    instance.status === 'running' && 'bg-indigo-500 animate-pulse',
                    instance.status === 'failed' && 'bg-red-500',
                    instance.status === 'pending' && 'bg-slate-500'
                  )} />
                  <div>
                    <div className="text-sm text-slate-300">{instance.name}</div>
                    <div className="text-[10px] text-slate-500 font-mono">
                      {instance.instance_id}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-mono text-emerald-400">
                    {instance.spent_so_far.toFixed(2)} MNEE
                  </span>
                  {instance.status === 'completed' && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                  {instance.status === 'running' && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />}
                  {instance.status === 'pending' && <Clock className="w-4 h-4 text-slate-400" />}
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowDemo;

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GitBranch,
  CheckCircle,
  XCircle,
  Loader2,
  Clock,
  ArrowRight,
  Lock,
  Unlock,
  User,
  Coins,
  FileText,
  BarChart3,
  Palette,
  Archive,
  Eye,
  ExternalLink,
  Users,
  Zap,
} from 'lucide-react';
import clsx from 'clsx';
import {
  WorkflowTemplate,
  WorkflowInstance,
  WorkflowStepStatus,
  WorkflowStepStatusType,
} from '../lib/types';
import { WorkflowOutputCard } from './WorkflowOutputCard';

interface WorkflowViewProps {
  template?: WorkflowTemplate;
  instance?: WorkflowInstance;
  onStepClick?: (stepId: string) => void;
}

// Role-based icons
const getRoleIcon = (role: string) => {
  const r = role.toLowerCase();
  if (r.includes('writer') || r.includes('write')) return FileText;
  if (r.includes('designer') || r.includes('design')) return Palette;
  if (r.includes('reviewer') || r.includes('review')) return Eye;
  if (r.includes('collector') || r.includes('collect')) return Archive;
  if (r.includes('analyzer') || r.includes('analy')) return BarChart3;
  if (r.includes('reporter') || r.includes('report')) return FileText;
  return User;
};

// Status colors and icons
const getStatusColor = (status: WorkflowStepStatusType) => {
  switch (status) {
    case 'pending':
      return 'border-slate-600 bg-slate-800 text-slate-400';
    case 'running':
      return 'border-indigo-500 bg-indigo-500/20 text-indigo-400 ring-2 ring-indigo-500/30';
    case 'completed':
      return 'border-emerald-500 bg-emerald-500/20 text-emerald-400';
    case 'failed':
      return 'border-red-500 bg-red-500/20 text-red-400';
    default:
      return 'border-slate-600 bg-slate-800 text-slate-400';
  }
};

const getStatusIcon = (status: WorkflowStepStatusType) => {
  switch (status) {
    case 'pending':
      return Clock;
    case 'running':
      return Loader2;
    case 'completed':
      return CheckCircle;
    case 'failed':
      return XCircle;
    default:
      return Clock;
  }
};

// Escrow status badge
const EscrowBadge = ({ status }: { status?: string }) => {
  if (!status) return null;

  const colors: Record<string, string> = {
    locked: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    released: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    refunded: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  };

  return (
    <span className={clsx(
      'flex items-center gap-1 px-1.5 py-0.5 text-[9px] font-bold uppercase rounded border',
      colors[status] || 'bg-slate-700 text-slate-400 border-slate-600'
    )}>
      {status === 'locked' ? <Lock className="w-2.5 h-2.5" /> : <Unlock className="w-2.5 h-2.5" />}
      {status}
    </span>
  );
};

// Individual step card
interface StepCardProps {
  step: WorkflowStepStatus;
  index: number;
  isLast: boolean;
  onClick?: () => void;
}

const StepCard = ({ step, index, isLast, onClick }: StepCardProps) => {
  const [expanded, setExpanded] = useState(false);
  const StatusIconComponent = getStatusIcon(step.status);
  const RoleIconComponent = getRoleIcon(step.role);

  return (
    <div className="flex items-center">
      {/* Step Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 }}
        className={clsx(
          'relative flex-shrink-0 w-40 border rounded-lg overflow-hidden cursor-pointer transition-all',
          getStatusColor(step.status),
          step.status === 'running' && 'animate-pulse'
        )}
        onClick={() => {
          setExpanded(!expanded);
          onClick?.();
        }}
      >
        {/* Header */}
        <div className="p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <RoleIconComponent className="w-4 h-4" />
              <span className="text-xs font-bold">{step.role}</span>
            </div>
            <StatusIconComponent
              className={clsx('w-4 h-4', step.status === 'running' && 'animate-spin')}
            />
          </div>

          {/* Agent ID */}
          <div className="text-[10px] text-slate-500 font-mono truncate mb-2">
            {step.agent_id}
          </div>

          {/* Cost */}
          <div className="flex items-center justify-between text-[10px]">
            <div className="flex items-center gap-1">
              <Coins className="w-3 h-3 text-emerald-400" />
              <span className="font-mono font-bold text-emerald-400">
                {step.cost.toFixed(2)} MNEE
              </span>
            </div>
            {step.escrow_status && <EscrowBadge status={step.escrow_status} />}
          </div>
        </div>

        {/* Expanded Details */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-t border-slate-700 bg-slate-900/50 overflow-hidden"
            >
              <div className="p-3 space-y-2 text-[10px]">
                {/* Selection Reason */}
                {step.selection_reason && (
                  <div className="flex items-start gap-1.5 p-2 bg-indigo-500/10 border border-indigo-500/20 rounded">
                    <Zap className="w-3 h-3 text-indigo-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="text-indigo-400 font-bold mb-0.5">Agent Selection</div>
                      <div className="text-slate-400">{step.selection_reason}</div>
                    </div>
                  </div>
                )}

                {/* Competing Bids Info */}
                {step.bid_info && step.bid_info.bids && step.bid_info.bids.length > 1 && (
                  <div className="flex items-center gap-1 text-slate-500">
                    <Users className="w-3 h-3" />
                    <span>{step.bid_info.bids.length} agents competed for this task</span>
                  </div>
                )}

                {step.escrow_id && (
                  <div className="flex items-center gap-1 text-slate-400">
                    <Lock className="w-3 h-3" />
                    <span className="font-mono">{step.escrow_id}</span>
                  </div>
                )}
                {step.tx_hash && (
                  <a
                    href={`https://etherscan.io/tx/${step.tx_hash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-indigo-400 hover:text-indigo-300 transition-colors"
                  >
                    <ExternalLink className="w-3 h-3" />
                    <span className="font-mono">{step.tx_hash.slice(0, 12)}...</span>
                  </a>
                )}
                {step.started_at && (
                  <div className="text-slate-500">
                    Started: {new Date(step.started_at).toLocaleTimeString()}
                  </div>
                )}
                {step.completed_at && (
                  <div className="text-slate-500">
                    Completed: {new Date(step.completed_at).toLocaleTimeString()}
                  </div>
                )}

                {/* Output Data */}
                {step.output_data && step.status === 'completed' && (
                  <div className="mt-2 pt-2 border-t border-slate-700">
                    <WorkflowOutputCard
                      role={step.role}
                      output={step.output_data as Record<string, unknown>}
                    />
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Arrow connector */}
      {!isLast && (
        <motion.div
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: index * 0.1 + 0.05 }}
          className="flex-shrink-0 mx-2"
        >
          <ArrowRight
            className={clsx(
              'w-5 h-5',
              step.status === 'completed' ? 'text-emerald-500' : 'text-slate-600'
            )}
          />
        </motion.div>
      )}
    </div>
  );
};

// Progress bar
const ProgressBar = ({ instance }: { instance: WorkflowInstance }) => {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-slate-400">
          Step {instance.current_step_index + 1} of {instance.total_steps}
        </span>
        <span className="font-mono text-emerald-400">
          {instance.spent_so_far.toFixed(2)} / {instance.total_cost.toFixed(2)} MNEE
        </span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${instance.progress_percent}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
    </div>
  );
};

// Main WorkflowView component
export const WorkflowView = ({ template, instance, onStepClick }: WorkflowViewProps) => {
  // Use instance steps if available, otherwise template steps
  const steps: WorkflowStepStatus[] = instance?.steps || (template?.steps.map(s => ({
    step_id: s.step_id,
    role: s.role,
    agent_id: s.agent_id,
    status: 'pending' as WorkflowStepStatusType,
    cost: s.estimated_cost,
  })) || []);

  const workflowName = instance?.name || template?.name || 'Workflow';
  const workflowStatus = instance?.status || 'pending';

  if (steps.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-500">
        <GitBranch className="w-5 h-5 mr-2" />
        No workflow selected
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <GitBranch className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="text-sm font-bold text-slate-200">{workflowName}</h3>
            <p className="text-[10px] text-slate-500">
              {steps.length} steps | Total: {instance?.total_cost.toFixed(2) || template?.total_cost.toFixed(2)} MNEE
            </p>
          </div>
        </div>

        {/* Status badge */}
        <span className={clsx(
          'px-2 py-1 text-[10px] font-bold uppercase rounded',
          workflowStatus === 'completed' && 'bg-emerald-500/20 text-emerald-400',
          workflowStatus === 'running' && 'bg-indigo-500/20 text-indigo-400 animate-pulse',
          workflowStatus === 'failed' && 'bg-red-500/20 text-red-400',
          workflowStatus === 'pending' && 'bg-slate-700 text-slate-400'
        )}>
          {workflowStatus}
        </span>
      </div>

      {/* Progress bar (only for instances) */}
      {instance && <ProgressBar instance={instance} />}

      {/* Pipeline visualization */}
      <div className="bg-slate-800/30 border border-slate-700 rounded-lg p-4 overflow-x-auto">
        <div className="flex items-start min-w-max">
          {steps.map((step, index) => (
            <StepCard
              key={step.step_id}
              step={step}
              index={index}
              isLast={index === steps.length - 1}
              onClick={() => onStepClick?.(step.step_id)}
            />
          ))}

          {/* Completion indicator */}
          {workflowStatus === 'completed' && (
            <motion.div
              initial={{ opacity: 0, scale: 0 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: steps.length * 0.1 }}
              className="flex-shrink-0 ml-2 w-12 h-12 rounded-full bg-emerald-500/20 border-2 border-emerald-500 flex items-center justify-center"
            >
              <CheckCircle className="w-6 h-6 text-emerald-400" />
            </motion.div>
          )}
        </div>
      </div>

      {/* Escrow summary */}
      {instance && instance.escrow_ids.length > 0 && (
        <div className="flex items-center gap-2 text-[10px] text-slate-500">
          <Lock className="w-3 h-3" />
          <span>Escrows: </span>
          <div className="flex gap-1">
            {instance.escrow_ids.map((id, i) => (
              <span key={i} className="font-mono px-1.5 py-0.5 bg-slate-800 rounded">
                {id}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowView;

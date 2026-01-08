import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  Trophy,
  Star,
  Clock,
  Coins,
  CheckCircle,
  TrendingUp,
  Zap,
  BarChart3,
  Shield,
} from 'lucide-react';
import clsx from 'clsx';
import { BidInfo, AgentBid } from '../lib/types';

interface AgentBiddingProps {
  bidInfo: BidInfo;
  showAnimation?: boolean;
  onComplete?: () => void;
  className?: string;
}

// Individual bid card
const BidCard = ({
  bid,
  isWinner,
  rank,
  animationDelay,
}: {
  bid: AgentBid;
  isWinner: boolean;
  rank: number;
  animationDelay: number;
}) => {
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setRevealed(true), animationDelay);
    return () => clearTimeout(timer);
  }, [animationDelay]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={revealed ? { opacity: 1, y: 0, scale: 1 } : {}}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={clsx(
        'relative p-4 rounded-lg border transition-all',
        isWinner
          ? 'bg-emerald-500/10 border-emerald-500/50 ring-2 ring-emerald-500/30'
          : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
      )}
    >
      {/* Winner badge */}
      {isWinner && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.3, type: 'spring', stiffness: 500 }}
          className="absolute -top-2 -right-2 w-8 h-8 bg-emerald-500 rounded-full flex items-center justify-center"
        >
          <Trophy className="w-4 h-4 text-white" />
        </motion.div>
      )}

      {/* Rank badge */}
      <div
        className={clsx(
          'absolute -top-2 -left-2 w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold',
          rank === 1
            ? 'bg-amber-500 text-amber-950'
            : rank === 2
            ? 'bg-slate-400 text-slate-900'
            : 'bg-orange-700 text-orange-100'
        )}
      >
        #{rank}
      </div>

      {/* Agent info */}
      <div className="mb-3">
        <h4 className="text-sm font-bold text-slate-200">{bid.agent_name}</h4>
        <p className="text-[10px] text-slate-500 font-mono">{bid.agent_id}</p>
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="flex items-center gap-1.5">
          <Coins className="w-3.5 h-3.5 text-emerald-400" />
          <div>
            <div className="text-xs font-bold text-emerald-400">{bid.price} MNEE</div>
            <div className="text-[9px] text-slate-500">Price</div>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-blue-400" />
          <div>
            <div className="text-xs font-bold text-blue-400">{bid.estimated_time}s</div>
            <div className="text-[9px] text-slate-500">Est. Time</div>
          </div>
        </div>
      </div>

      {/* Reputation & Success Rate */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1">
          {[1, 2, 3, 4, 5].map((s) => (
            <Star
              key={s}
              className={clsx(
                'w-3 h-3',
                s <= Math.round(bid.reputation_score)
                  ? 'text-amber-400 fill-amber-400'
                  : 'text-slate-600'
              )}
            />
          ))}
          <span className="text-[10px] text-slate-400 ml-1">
            {bid.reputation_score.toFixed(1)}
          </span>
        </div>
        <div className="flex items-center gap-1 text-[10px]">
          <Shield className="w-3 h-3 text-indigo-400" />
          <span className="text-slate-400">{(bid.success_rate * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Score breakdown */}
      <div className="space-y-1.5">
        <div className="text-[9px] text-slate-500 uppercase font-bold">Score Breakdown</div>
        <div className="space-y-1">
          <ScoreBar
            label="Price"
            value={bid.score_breakdown.price_score}
            color="emerald"
          />
          <ScoreBar
            label="Reputation"
            value={bid.score_breakdown.reputation_score}
            color="amber"
          />
          <ScoreBar
            label="Reliability"
            value={bid.score_breakdown.success_score}
            color="indigo"
          />
        </div>
      </div>

      {/* Total score */}
      <div className="mt-3 pt-3 border-t border-slate-700 flex items-center justify-between">
        <span className="text-[10px] text-slate-400">Total Score</span>
        <span
          className={clsx(
            'text-sm font-bold',
            isWinner ? 'text-emerald-400' : 'text-slate-300'
          )}
        >
          {(bid.score * 100).toFixed(1)}
        </span>
      </div>

      {/* Task history */}
      <div className="mt-2 flex items-center justify-between text-[9px] text-slate-500">
        <span>{bid.total_tasks} tasks completed</span>
        <span>Load: {bid.current_load}/{5}</span>
      </div>
    </motion.div>
  );
};

// Score bar component
const ScoreBar = ({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: 'emerald' | 'amber' | 'indigo';
}) => {
  const colorClasses = {
    emerald: 'bg-emerald-500',
    amber: 'bg-amber-500',
    indigo: 'bg-indigo-500',
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-[9px] text-slate-500 w-16">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${value * 100}%` }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className={clsx('h-full rounded-full', colorClasses[color])}
        />
      </div>
      <span className="text-[9px] text-slate-400 w-8 text-right">
        {(value * 100).toFixed(0)}
      </span>
    </div>
  );
};

// Main AgentBidding component
export const AgentBidding = ({
  bidInfo,
  showAnimation = true,
  onComplete,
  className,
}: AgentBiddingProps) => {
  const [phase, setPhase] = useState<'collecting' | 'evaluating' | 'selected'>('collecting');
  const [showWinner, setShowWinner] = useState(false);

  // Sort bids by score descending
  const sortedBids = [...bidInfo.bids].sort((a, b) => b.score - a.score);
  const winnerBid = sortedBids[0];

  useEffect(() => {
    if (!showAnimation) {
      setPhase('selected');
      setShowWinner(true);
      return;
    }

    // Animation sequence
    const timers: NodeJS.Timeout[] = [];

    timers.push(setTimeout(() => setPhase('evaluating'), 1000));
    timers.push(setTimeout(() => setPhase('selected'), 2500));
    timers.push(
      setTimeout(() => {
        setShowWinner(true);
        onComplete?.();
      }, 3000)
    );

    return () => timers.forEach(clearTimeout);
  }, [showAnimation, onComplete]);

  if (bidInfo.bids.length === 0) {
    return (
      <div className={clsx('p-4 bg-slate-800/50 rounded-lg border border-slate-700', className)}>
        <div className="flex items-center justify-center gap-2 text-slate-500">
          <Users className="w-4 h-4" />
          <span className="text-sm">No agents available for {bidInfo.capability}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center">
            <Users className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-200">Agent Coordination</h3>
            <p className="text-[10px] text-slate-500">
              Capability: <span className="text-indigo-400">{bidInfo.capability}</span>
            </p>
          </div>
        </div>

        {/* Phase indicator */}
        <div className="flex items-center gap-2">
          <div
            className={clsx(
              'px-2 py-1 text-[10px] font-bold uppercase rounded transition-colors',
              phase === 'collecting' && 'bg-blue-500/20 text-blue-400 animate-pulse',
              phase === 'evaluating' && 'bg-amber-500/20 text-amber-400 animate-pulse',
              phase === 'selected' && 'bg-emerald-500/20 text-emerald-400'
            )}
          >
            {phase === 'collecting' && 'Collecting Bids'}
            {phase === 'evaluating' && 'Evaluating...'}
            {phase === 'selected' && 'Agent Selected'}
          </div>
        </div>
      </div>

      {/* Bid cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sortedBids.map((bid, index) => (
          <BidCard
            key={bid.agent_id}
            bid={bid}
            isWinner={showWinner && bid.agent_id === bidInfo.selected_agent}
            rank={index + 1}
            animationDelay={showAnimation ? index * 300 : 0}
          />
        ))}
      </div>

      {/* Selection reason */}
      <AnimatePresence>
        {showWinner && bidInfo.selection_reason && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-start gap-3 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg"
          >
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
              <Zap className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="text-sm font-bold text-emerald-400 mb-1">
                Winner: {winnerBid?.agent_name}
              </div>
              <div className="text-xs text-slate-400">{bidInfo.selection_reason}</div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Weights info */}
      {bidInfo.weights && (
        <div className="flex items-center justify-center gap-4 text-[10px] text-slate-500">
          <span className="flex items-center gap-1">
            <BarChart3 className="w-3 h-3" />
            Weights:
          </span>
          <span>Price: {(bidInfo.weights.price * 100).toFixed(0)}%</span>
          <span>Reputation: {(bidInfo.weights.reputation * 100).toFixed(0)}%</span>
          <span>Success: {(bidInfo.weights.success * 100).toFixed(0)}%</span>
        </div>
      )}
    </div>
  );
};

export default AgentBidding;

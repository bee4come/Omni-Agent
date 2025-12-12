import React from 'react';
import { AlertTriangle, XCircle, AlertCircle } from 'lucide-react';
import clsx from 'clsx';

interface BudgetAlertProps {
  agentId: string;
  currentSpend: number;
  dailyBudget: number;
  onDismiss?: () => void;
}

export const BudgetAlert = ({ agentId, currentSpend, dailyBudget, onDismiss }: BudgetAlertProps) => {
  const percentage = (currentSpend / dailyBudget) * 100;
  
  if (percentage < 75) return null;

  const isWarning = percentage >= 75 && percentage < 90;
  const isCritical = percentage >= 90 && percentage < 100;
  const isExhausted = percentage >= 100;

  const getAlertConfig = () => {
    if (isExhausted) {
      return {
        icon: XCircle,
        bgColor: 'bg-red-500/10 border-red-500/30',
        textColor: 'text-red-400',
        title: 'Budget Exhausted',
        message: `${agentId} has exceeded its daily budget. All requests will be denied.`
      };
    }
    if (isCritical) {
      return {
        icon: AlertTriangle,
        bgColor: 'bg-orange-500/10 border-orange-500/30',
        textColor: 'text-orange-400',
        title: 'Critical Budget Warning',
        message: `${agentId} has used ${percentage.toFixed(0)}% of its daily budget.`
      };
    }
    return {
      icon: AlertCircle,
      bgColor: 'bg-amber-500/10 border-amber-500/30',
      textColor: 'text-amber-400',
      title: 'Budget Warning',
      message: `${agentId} has used ${percentage.toFixed(0)}% of its daily budget.`
    };
  };

  const config = getAlertConfig();
  const Icon = config.icon;

  return (
    <div className={clsx("flex items-start gap-3 p-4 rounded-lg border", config.bgColor)}>
      <Icon className={clsx("w-5 h-5 flex-shrink-0 mt-0.5", config.textColor)} />
      <div className="flex-1">
        <div className={clsx("font-bold text-sm mb-1", config.textColor)}>{config.title}</div>
        <p className="text-sm text-slate-400">{config.message}</p>
        <div className="mt-2 flex items-center gap-2 text-xs">
          <span className="font-mono text-slate-500">
            {currentSpend.toFixed(2)} / {dailyBudget.toFixed(2)} MNEE
          </span>
        </div>
      </div>
      {onDismiss && (
        <button 
          onClick={onDismiss}
          className="text-slate-500 hover:text-slate-300 transition-colors"
        >
          <XCircle className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

interface BudgetAlertsContainerProps {
  agents: Array<{
    id: string;
    currentDailySpend: number;
    dailyBudget: number;
  }>;
}

export const BudgetAlertsContainer = ({ agents }: BudgetAlertsContainerProps) => {
  const alertAgents = agents.filter(agent => 
    (agent.currentDailySpend / agent.dailyBudget) >= 0.75
  );

  if (alertAgents.length === 0) return null;

  return (
    <div className="space-y-3">
      {alertAgents.map(agent => (
        <BudgetAlert
          key={agent.id}
          agentId={agent.id}
          currentSpend={agent.currentDailySpend}
          dailyBudget={agent.dailyBudget}
        />
      ))}
    </div>
  );
};

import React from 'react';
import { StepRecord, GuardianAudit } from '../lib/types';

interface LiveGraphProps {
  status: 'idle' | 'planning' | 'auditing' | 'executing' | 'finished';
  guardianAudit?: GuardianAudit;
  currentStep?: StepRecord;
}

const Node = ({ title, isActive, icon, detail }: { title: string; isActive: boolean; icon: string; detail?: React.ReactNode }) => (
  <div className={`flex flex-col items-center p-4 rounded-lg border-2 transition-all duration-300 w-full ${
    isActive ? 'border-blue-500 bg-blue-50 shadow-lg scale-105' : 'border-gray-200 bg-gray-50 opacity-70'
  }`}>
    <div className="text-2xl mb-2">{icon}</div>
    <div className="font-bold text-gray-700">{title}</div>
    {isActive && detail && (
      <div className="mt-2 text-xs text-gray-600 w-full bg-white p-2 rounded border border-gray-100 animate-fade-in">
        {detail}
      </div>
    )}
  </div>
);

const Arrow = ({ isActive }: { isActive: boolean }) => (
  <div className={`text-2xl font-bold my-2 ${isActive ? 'text-blue-500' : 'text-gray-300'}`}>
    ↓
  </div>
);

export const LiveGraph: React.FC<LiveGraphProps> = ({ status, guardianAudit, currentStep }) => {
  return (
    <div className="flex flex-col items-center w-full max-w-md mx-auto py-6">
      <h3 className="text-lg font-bold mb-4 text-gray-500 uppercase tracking-wider">Live Operation Room</h3>
      
      {/* Planner Node */}
      <Node 
        title="CEO Planner" 
        isActive={status === 'planning'} 
        icon="🧠"
        detail="Delegating tasks to specialized agents..."
      />
      
      <Arrow isActive={status === 'auditing' || status === 'executing'} />
      
      {/* Guardian Node */}
      <Node 
        title="AI Guardian" 
        isActive={status === 'auditing'} 
        icon="🛡️"
        detail={guardianAudit ? (
          <div>
            <div className="font-semibold">Risk Score: {guardianAudit.risk_score}/10</div>
            <div className="mt-1 italic">{guardianAudit.reasoning}</div>
          </div>
        ) : "Auditing Plan & Budget..."}
      />
      
      <Arrow isActive={status === 'executing'} />
      
      {/* Executor Node */}
      <Node 
        title="Executor" 
        isActive={status === 'executing'} 
        icon="⚡"
        detail={currentStep ? (
          <div>
            <div><strong>Agent:</strong> {currentStep.agent_id}</div>
            <div><strong>Tool:</strong> {currentStep.tool_name}</div>
            <div className="text-green-600">Paying {currentStep.amount_mnee || '...'} MNEE</div>
          </div>
        ) : "Waiting for tasks..."}
      />
      
      <Arrow isActive={status === 'finished'} />
      
      {/* Result Node */}
      <Node 
        title="Result" 
        isActive={status === 'finished'} 
        icon="🏁"
      />
    </div>
  );
};

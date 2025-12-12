'use client';

import React, { useMemo } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, Legend, PieChart, Pie, Cell
} from 'recharts';
import { Transaction } from '../lib/types';

interface SpendingChartProps {
  transactions: Transaction[];
  agents: { id: string; currentDailySpend: number; dailyBudget: number }[];
}

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export const SpendingChart = ({ transactions, agents }: SpendingChartProps) => {
  // Process transactions for hourly spending
  const hourlyData = useMemo(() => {
    const now = new Date();
    const hours: { hour: string; amount: number }[] = [];
    
    for (let i = 23; i >= 0; i--) {
      const hourDate = new Date(now.getTime() - i * 60 * 60 * 1000);
      const hourLabel = hourDate.getHours().toString().padStart(2, '0') + ':00';
      hours.push({ hour: hourLabel, amount: 0 });
    }
    
    transactions.forEach(tx => {
      const txDate = new Date(tx.timestamp);
      const txHour = txDate.getHours().toString().padStart(2, '0') + ':00';
      const hourEntry = hours.find(h => h.hour === txHour);
      if (hourEntry && tx.status === 'SUCCESS') {
        hourEntry.amount += tx.amount;
      }
    });
    
    return hours;
  }, [transactions]);

  // Process agent spending for pie chart
  const agentSpendingData = useMemo(() => {
    return agents.map((agent, index) => ({
      name: agent.id,
      value: agent.currentDailySpend,
      color: COLORS[index % COLORS.length]
    })).filter(a => a.value > 0);
  }, [agents]);

  // Service breakdown
  const serviceData = useMemo(() => {
    const services: Record<string, number> = {};
    transactions.forEach(tx => {
      if (tx.status === 'SUCCESS') {
        services[tx.service_id] = (services[tx.service_id] || 0) + tx.amount;
      }
    });
    return Object.entries(services)
      .map(([name, amount]) => ({ name, amount }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 5);
  }, [transactions]);

  return (
    <div className="space-y-6">
      {/* Hourly Spending Trend */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
          24h Spending Trend
        </h4>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={hourlyData}>
              <defs>
                <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis 
                dataKey="hour" 
                stroke="#64748b" 
                fontSize={10}
                tickLine={false}
                interval={3}
              />
              <YAxis 
                stroke="#64748b" 
                fontSize={10}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  fontSize: '12px'
                }}
                labelStyle={{ color: '#94a3b8' }}
                formatter={(value: number) => [`${value.toFixed(2)} MNEE`, 'Spent']}
              />
              <Area 
                type="monotone" 
                dataKey="amount" 
                stroke="#6366f1" 
                strokeWidth={2}
                fillOpacity={1} 
                fill="url(#colorSpend)" 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Spending Distribution */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
            Spending by Agent
          </h4>
          <div className="h-48">
            {agentSpendingData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={agentSpendingData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={70}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {agentSpendingData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                    formatter={(value: number) => [`${value.toFixed(2)} MNEE`, '']}
                  />
                  <Legend 
                    wrapperStyle={{ fontSize: '10px' }}
                    formatter={(value) => <span className="text-slate-400">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                No spending data yet
              </div>
            )}
          </div>
        </div>

        {/* Top Services */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h4 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">
            Top Services
          </h4>
          <div className="h-48">
            {serviceData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={serviceData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis type="number" stroke="#64748b" fontSize={10} />
                  <YAxis 
                    type="category" 
                    dataKey="name" 
                    stroke="#64748b" 
                    fontSize={10}
                    width={80}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      fontSize: '12px'
                    }}
                    formatter={(value: number) => [`${value.toFixed(2)} MNEE`, 'Revenue']}
                  />
                  <Bar dataKey="amount" fill="#10b981" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                No service data yet
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

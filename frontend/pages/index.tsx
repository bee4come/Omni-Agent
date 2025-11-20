import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Layout } from '../components/Layout';
import { ChatInterface } from '../components/ChatInterface';
import { Dashboard } from '../components/Dashboard';
import { PolicyConsole } from '../components/PolicyConsole';
import { ConfigPanel } from '../components/ConfigPanel';
import { TreasuryStatus } from '../components/TreasuryStatus';
import { PolicyLogsPreview } from '../components/PolicyLogsPreview';

export default function App() {
    const [activeTab, setActiveTab] = useState<'chat' | 'dashboard' | 'policy' | 'config'>('chat');
    const [treasury, setTreasury] = useState<any>(null);
    const [policyLogs, setPolicyLogs] = useState<any[]>([]);
    const [transactions, setTransactions] = useState<any[]>([]);
    const [services, setServices] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);

    const fetchTreasury = async () => {
        try {
            const res = await axios.get('/api/treasury');
            setTreasury(res.data);
        } catch (e) {
            console.error('Error fetching treasury:', e);
        }
    };

    const fetchPolicyLogs = async () => {
        try {
            const res = await axios.get('/api/policy/logs');
            setPolicyLogs(res.data.logs || []);
        } catch (e) {
            console.error('Error fetching policy logs:', e);
        }
    };

    const fetchTransactions = async () => {
        try {
            const res = await axios.get('/api/transactions?limit=50');
            setTransactions(res.data.transactions || []);
        } catch (e) {
            console.error('Error fetching transactions:', e);
        }
    };

    const fetchServices = async () => {
        try {
            const res = await axios.get('/api/services');
            setServices(res.data.services || []);
        } catch (e) {
            console.error('Error fetching services:', e);
        }
    };

    const fetchStats = async () => {
        try {
            const res = await axios.get('/api/stats');
            setStats(res.data);
        } catch (e) {
            console.error('Error fetching stats:', e);
        }
    };

    const refreshAll = () => {
        fetchTreasury();
        fetchPolicyLogs();
        fetchTransactions();
        fetchStats();
    };

    useEffect(() => {
        // Initial fetch
        refreshAll();
        fetchServices(); // Services change less often
        
        // Poll every 3 seconds
        const interval = setInterval(() => {
            refreshAll();
        }, 3000);
        
        return () => clearInterval(interval);
    }, []);

    return (
        <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
            {activeTab === 'chat' && (
                <div className="grid grid-cols-12 gap-8">
                    <div className="col-span-12 lg:col-span-8">
                        <ChatInterface onMessageSent={refreshAll} />
                    </div>
                    <div className="col-span-12 lg:col-span-4 space-y-6">
                        <TreasuryStatus treasury={treasury} />
                        <PolicyLogsPreview logs={policyLogs} />
                    </div>
                </div>
            )}

            {activeTab === 'dashboard' && (
                <Dashboard stats={stats} transactions={transactions} />
            )}

            {activeTab === 'policy' && (
                <PolicyConsole logs={policyLogs} />
            )}

            {activeTab === 'config' && (
                <ConfigPanel treasury={treasury} services={services} />
            )}
        </Layout>
    );
}

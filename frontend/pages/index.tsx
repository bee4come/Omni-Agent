import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Layout } from '../components/Layout';
import { ChatInterface } from '../components/ChatInterface';
import { Dashboard } from '../components/Dashboard';
import { ConfigPanel } from '../components/ConfigPanel';
import { AuditLog } from '../components/AuditLog';
import { TransactionStream } from '../components/TransactionStream';
import { TreasuryStatus } from '../components/TreasuryStatus';

export default function App() {
    const [activeTab, setActiveTab] = useState<'chat' | 'dashboard' | 'config'>('chat');
    const [treasury, setTreasury] = useState<any>(null);
    const [policyLogs, setPolicyLogs] = useState<any[]>([]);
    const [transactions, setTransactions] = useState<any[]>([]);
    const [services, setServices] = useState<any[]>([]);
    const [stats, setStats] = useState<any>(null);

    const fetchAll = async () => {
        try {
            const [tRes, pRes, txRes, sRes, statRes] = await Promise.all([
                axios.get('/api/treasury'),
                axios.get('/api/policy/logs?limit=20'),
                axios.get('/api/transactions?limit=20'),
                axios.get('/api/services'),
                axios.get('/api/stats')
            ]);
            
            setTreasury(tRes.data);
            setPolicyLogs(pRes.data.logs || []);
            setTransactions(txRes.data.transactions || []);
            setServices(sRes.data.services || []);
            setStats(statRes.data);
        } catch (e) {
            console.error("Data fetch error", e);
        }
    };

    useEffect(() => {
        fetchAll();
        const interval = setInterval(fetchAll, 3000);
        return () => clearInterval(interval);
    }, []);

    return (
        <Layout activeTab={activeTab} setActiveTab={setActiveTab}>
            
            {/* MAIN COMMAND CENTER */}
            {activeTab === 'chat' && (
                <div className="space-y-8">
                    {/* Top: Chat & Live Brain */}
                    <ChatInterface onMessageSent={fetchAll} />
                    
                    {/* Bottom: Data Streams */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <div className="lg:col-span-1">
                            <TreasuryStatus treasury={treasury} />
                        </div>
                        <div className="lg:col-span-1">
                            <AuditLog logs={policyLogs} />
                        </div>
                        <div className="lg:col-span-1">
                            <TransactionStream transactions={transactions} />
                        </div>
                    </div>
                </div>
            )}

            {/* ANALYTICS DASHBOARD */}
            {activeTab === 'dashboard' && (
                <Dashboard stats={stats} transactions={transactions} />
            )}

            {/* CONFIGURATION */}
            {activeTab === 'config' && (
                <ConfigPanel treasury={treasury} services={services} />
            )}
        </Layout>
    );
}
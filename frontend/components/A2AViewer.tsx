import React from 'react';
import { Card } from './ui/Card';

interface A2AViewerProps {
    latestResults: any[];
}

export const A2AViewer = ({ latestResults }: A2AViewerProps) => {
    // Filter for relevant actions
    const quoteAction = latestResults.find(r => r.action === 'get_quote');
    const purchaseAction = latestResults.find(r => r.action === 'purchase_service');
    
    if (!quoteAction && !purchaseAction) {
        return null;
    }

    const quoteData = quoteAction?.result || {};
    const purchaseData = purchaseAction?.result || {};
    const deliveryData = purchaseData?.data || {};

    return (
        <div className="mt-6">
            <h3 className="text-lg font-semibold text-slate-200 mb-4">🛒 Agent-to-Agent Commerce Rail</h3>
            
            <div className="relative bg-slate-900/50 p-6 rounded-xl border border-slate-700/50 overflow-hidden">
                {/* Background Connection Line */}
                <div className="absolute top-1/2 left-10 right-10 h-1 bg-slate-700 -z-0 transform -translate-y-1/2" />

                <div className="grid grid-cols-3 gap-4 relative z-10">
                    
                    {/* Step 1: Quote */}
                    <div className={`flex flex-col items-center space-y-3 ${quoteAction ? 'opacity-100' : 'opacity-30'}`}>
                        <div className="w-12 h-12 rounded-full bg-blue-900/80 border-2 border-blue-500 flex items-center justify-center text-xl shadow-lg shadow-blue-500/20">
                            📄
                        </div>
                        <div className="bg-slate-800 p-3 rounded-lg border border-slate-700 w-full text-center">
                            <div className="text-xs text-slate-400 uppercase tracking-wider">Step 1</div>
                            <div className="font-bold text-blue-400">Quote</div>
                            {quoteData.quoteId && (
                                <div className="text-xs text-slate-500 mt-1 font-mono">
                                    ID: {quoteData.quoteId.substring(0, 8)}...
                                </div>
                            )}
                            {quoteData.unitPriceMNEE && (
                                <div className="text-xs text-emerald-400 mt-1">
                                    Price: {quoteData.unitPriceMNEE} MNEE
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Step 2: Payment */}
                    <div className={`flex flex-col items-center space-y-3 ${purchaseAction ? 'opacity-100' : 'opacity-30'}`}>
                        <div className="w-12 h-12 rounded-full bg-purple-900/80 border-2 border-purple-500 flex items-center justify-center text-xl shadow-lg shadow-purple-500/20">
                            💸
                        </div>
                        <div className="bg-slate-800 p-3 rounded-lg border border-slate-700 w-full text-center">
                            <div className="text-xs text-slate-400 uppercase tracking-wider">Step 2</div>
                            <div className="font-bold text-purple-400">Payment</div>
                            {purchaseAction?.tx_hash && (
                                <div className="text-xs text-slate-500 mt-1 font-mono" title={purchaseAction.tx_hash}>
                                    TX: {purchaseAction.tx_hash.substring(0, 8)}...
                                </div>
                            )}
                            <div className="text-xs text-slate-400 mt-1">
                                On-Chain Settlement
                            </div>
                        </div>
                    </div>

                    {/* Step 3: Delivery */}
                    <div className={`flex flex-col items-center space-y-3 ${purchaseAction?.result?.status === 'DELIVERED' ? 'opacity-100' : 'opacity-30'}`}>
                        <div className="w-12 h-12 rounded-full bg-emerald-900/80 border-2 border-emerald-500 flex items-center justify-center text-xl shadow-lg shadow-emerald-500/20">
                            📦
                        </div>
                        <div className="bg-slate-800 p-3 rounded-lg border border-slate-700 w-full text-center">
                            <div className="text-xs text-slate-400 uppercase tracking-wider">Step 3</div>
                            <div className="font-bold text-emerald-400">Delivery</div>
                            {deliveryData.imageUrl ? (
                                <div className="text-xs text-slate-300 mt-1">Image Received</div>
                            ) : (
                                <div className="text-xs text-slate-500 mt-1">Pending...</div>
                            )}
                            {purchaseData.serviceCallHash && (
                                <div className="text-[10px] text-slate-600 mt-1 font-mono truncate px-2" title={purchaseData.serviceCallHash}>
                                    Hash: {purchaseData.serviceCallHash.substring(0, 10)}...
                                </div>
                            )}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};

import React from 'react';
import { cn } from './Card';

export const Badge = ({ children, variant = 'default' }: { children: React.ReactNode; variant?: 'default' | 'danger' | 'warning' | 'success' }) => {
    const variants = {
        default: "bg-slate-800 text-slate-300",
        danger: "bg-red-900/30 text-red-400 border border-red-900/50",
        warning: "bg-amber-900/30 text-amber-400 border border-amber-900/50",
        success: "bg-emerald-900/30 text-emerald-400 border border-emerald-900/50",
    };
    return (
        <span className={cn("px-2 py-1 rounded-md text-xs font-medium", variants[variant])}>
            {children}
        </span>
    );
};

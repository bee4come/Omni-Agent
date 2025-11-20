import React from 'react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export const Card = ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div className={cn("bg-slate-900 border border-slate-800 rounded-xl p-6", className)}>
        {children}
    </div>
);

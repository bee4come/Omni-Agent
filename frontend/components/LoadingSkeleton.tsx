import React from 'react';
import clsx from 'clsx';

interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton = ({ className, style }: SkeletonProps) => (
  <div className={clsx("animate-pulse bg-slate-800 rounded", className)} style={style} />
);

export const CardSkeleton = () => (
  <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
    <Skeleton className="h-4 w-1/3" />
    <Skeleton className="h-8 w-1/2" />
    <Skeleton className="h-2 w-full" />
  </div>
);

export const TableSkeleton = ({ rows = 5 }: { rows?: number }) => (
  <div className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/50">
    <div className="bg-slate-900 p-4 border-b border-slate-800">
      <div className="grid grid-cols-6 gap-4">
        {[1, 2, 3, 4, 5, 6].map(i => (
          <Skeleton key={i} className="h-4" />
        ))}
      </div>
    </div>
    <div className="divide-y divide-slate-800">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="p-4">
          <div className="grid grid-cols-6 gap-4">
            {[1, 2, 3, 4, 5, 6].map(j => (
              <Skeleton key={j} className="h-4" />
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
);

export const ChartSkeleton = () => (
  <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
    <Skeleton className="h-4 w-1/4 mb-4" />
    <div className="h-64 flex items-end gap-2">
      {Array.from({ length: 12 }).map((_, i) => (
        <Skeleton 
          key={i} 
          className="flex-1" 
          style={{ height: `${Math.random() * 60 + 20}%` }}
        />
      ))}
    </div>
  </div>
);

export const AgentCardSkeleton = () => (
  <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
    <div className="flex items-center gap-3 mb-4">
      <Skeleton className="w-10 h-10 rounded" />
      <div className="flex-1">
        <Skeleton className="h-4 w-1/2 mb-2" />
        <Skeleton className="h-3 w-1/4" />
      </div>
    </div>
    <Skeleton className="h-2 w-full mb-3" />
    <div className="flex justify-between">
      <Skeleton className="h-3 w-1/4" />
      <Skeleton className="h-3 w-1/4" />
    </div>
  </div>
);

export const StatsCardsSkeleton = () => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    {[1, 2, 3, 4].map(i => (
      <CardSkeleton key={i} />
    ))}
  </div>
);

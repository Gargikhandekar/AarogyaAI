interface LoadingSkeletonProps {
  variant?: 'page' | 'card' | 'chat' | 'list';
  count?: number;
}

export default function LoadingSkeleton({ variant = 'page', count = 3 }: LoadingSkeletonProps) {
  if (variant === 'page') {
    return (
      <div className="flex flex-col items-center gap-4 animate-pulse">
        <div className="w-16 h-16 rounded-2xl bg-slate-200 dark:bg-slate-700" />
        <div className="w-48 h-4 rounded-lg bg-slate-200 dark:bg-slate-700" />
        <div className="w-32 h-3 rounded-lg bg-slate-200 dark:bg-slate-700" />
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="glass-card p-6 animate-pulse">
            <div className="w-12 h-12 rounded-xl bg-slate-200 dark:bg-slate-700 mb-4" />
            <div className="w-3/4 h-4 rounded-lg bg-slate-200 dark:bg-slate-700 mb-2" />
            <div className="w-full h-3 rounded-lg bg-slate-200 dark:bg-slate-700" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'chat') {
    return (
      <div className="space-y-6 animate-pulse px-4">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`rounded-2xl bg-slate-200 dark:bg-slate-700 ${
                i % 2 === 0 ? 'w-2/3 h-12' : 'w-3/4 h-24'
              }`}
            />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-700" />
          <div className="flex-1 h-4 rounded-lg bg-slate-200 dark:bg-slate-700" />
        </div>
      ))}
    </div>
  );
}

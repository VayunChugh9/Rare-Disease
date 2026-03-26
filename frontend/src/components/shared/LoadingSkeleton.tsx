export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded bg-stone-200 ${className}`}
    />
  );
}

export function QueueSkeleton() {
  return (
    <div className="space-y-3 p-6">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 rounded-lg border border-stone-200 bg-white p-4">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-48 flex-1" />
          <Skeleton className="h-5 w-20 rounded-md" />
          <Skeleton className="h-5 w-16 rounded-md" />
          <Skeleton className="h-4 w-24" />
        </div>
      ))}
    </div>
  );
}

export function ReviewSkeleton() {
  return (
    <div className="flex h-full">
      <div className="flex-1 border-r border-stone-200 p-6 space-y-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-32 w-full mt-6" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
      </div>
      <div className="flex-1 p-6 space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-6 w-32" />
        <div className="grid grid-cols-2 gap-3 mt-4">
          <Skeleton className="h-20 rounded-lg" />
          <Skeleton className="h-20 rounded-lg" />
        </div>
        <Skeleton className="h-32 w-full mt-4" />
        <Skeleton className="h-24 w-full" />
      </div>
    </div>
  );
}

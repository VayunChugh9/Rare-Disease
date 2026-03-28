import { Inbox } from "lucide-react";

export function EmptyState({
  icon: Icon = Inbox,
  title = "No items",
  description = "",
  action,
}: {
  icon?: React.ElementType;
  title?: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <Icon className="h-12 w-12 text-stone-300 mb-4" strokeWidth={1.5} />
      <h3 className="text-sm font-medium text-slate-700">{title}</h3>
      {description && (
        <p className="mt-1 text-sm text-slate-500">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

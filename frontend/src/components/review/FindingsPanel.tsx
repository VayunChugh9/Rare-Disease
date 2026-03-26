import { AlertTriangle, Info, AlertCircle } from "lucide-react";

interface FindingsPanelProps {
  redFlags: string[];
  actionItems: string[];
  missingInfo: string[];
}

export function FindingsPanel({
  redFlags,
  actionItems,
  missingInfo,
}: FindingsPanelProps) {
  const hasContent = redFlags.length > 0 || actionItems.length > 0 || missingInfo.length > 0;
  if (!hasContent) return null;

  return (
    <div className="space-y-2">
      {redFlags.length > 0 && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2.5">
          <div className="flex items-center gap-1.5 mb-1.5">
            <AlertTriangle className="h-3.5 w-3.5 text-red-600" />
            <span className="text-xs font-semibold text-red-700 uppercase tracking-wide">
              Red Flags
            </span>
          </div>
          <ul className="space-y-1">
            {redFlags.map((flag, i) => (
              <li key={i} className="text-xs text-red-800 leading-relaxed">
                {flag}
              </li>
            ))}
          </ul>
        </div>
      )}

      {missingInfo.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5">
          <div className="flex items-center gap-1.5 mb-1.5">
            <AlertCircle className="h-3.5 w-3.5 text-amber-600" />
            <span className="text-xs font-semibold text-amber-700 uppercase tracking-wide">
              Missing Information
            </span>
          </div>
          <ul className="space-y-1">
            {missingInfo.map((item, i) => (
              <li key={i} className="text-xs text-amber-800 leading-relaxed">
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {actionItems.length > 0 && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 px-3 py-2.5">
          <div className="flex items-center gap-1.5 mb-1.5">
            <Info className="h-3.5 w-3.5 text-blue-600" />
            <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">
              Action Items
            </span>
          </div>
          <ul className="space-y-1">
            {actionItems.map((item, i) => (
              <li key={i} className="text-xs text-blue-800 leading-relaxed">
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

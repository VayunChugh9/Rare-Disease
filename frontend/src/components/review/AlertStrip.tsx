import { AlertTriangle, Info } from "lucide-react";

interface AlertStripProps {
  redFlags: string[];
  missingInfo: string[];
}

export function AlertStrip({ redFlags, missingInfo }: AlertStripProps) {
  if (redFlags.length === 0 && missingInfo.length === 0) return null;

  return (
    <div className="grid grid-cols-2 gap-4 mx-6 mb-4">
      {redFlags.length > 0 && (
        <div className="bg-red-50/60 border border-red-200/40 p-3 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-[#DC2626]" />
            <span className="section-label text-[#DC2626]">Red Flags</span>
          </div>
          <ul className="space-y-1">
            {redFlags.map((flag, i) => (
              <li key={i} className="text-sm font-medium text-red-800">{flag}</li>
            ))}
          </ul>
        </div>
      )}
      {missingInfo.length > 0 && (
        <div className="bg-amber-50/60 border border-amber-200/40 p-3 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <Info className="h-4 w-4 text-[#CA8A04]" />
            <span className="section-label text-[#CA8A04]">Missing Information</span>
          </div>
          <ul className="space-y-1">
            {missingInfo.map((item, i) => (
              <li key={i} className="text-sm font-medium text-amber-800">{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

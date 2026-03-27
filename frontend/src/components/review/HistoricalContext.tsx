import { useState } from "react";
import { ChevronDown, ChevronUp, History } from "lucide-react";
import type { SignificantHistory, Procedure } from "../../types/referral";

export function HistoricalContext({ significantHistory, procedures }: { significantHistory?: SignificantHistory[]; procedures?: Procedure[] }) {
  const [isOpen, setIsOpen] = useState(false);
  const historyCount = significantHistory?.length ?? 0;
  const procedureCount = procedures?.length ?? 0;

  if (historyCount === 0 && procedureCount === 0) return null;

  return (
    <div className="glass rounded-xl overflow-hidden">
      <button onClick={() => setIsOpen((prev) => !prev)}
        className="w-full flex justify-between items-center py-3 px-6 opacity-70 hover:opacity-100 transition-opacity cursor-pointer">
        <div className="flex items-center gap-3">
          <History className="h-4 w-4 text-[#64748B]" />
          <span className="section-label">Historical Context — {historyCount} resolved conditions, {procedureCount} procedures</span>
        </div>
        {isOpen ? <ChevronUp className="h-4 w-4 text-[#64748B]" /> : <ChevronDown className="h-4 w-4 text-[#64748B]" />}
      </button>
      {isOpen && (
        <div className="px-6 pb-4 space-y-4 text-sm text-[#64748B]">
          {historyCount > 0 && (
            <div>
              <h4 className="section-label mb-2">Resolved Conditions</h4>
              <div className="space-y-1">
                {significantHistory!.map((item, i) => (
                  <div key={i} className="flex justify-between">
                    <span>{item.diagnosis}</span>
                    <span className="text-xs">{item.onset_date}{item.resolution_date && ` — ${item.resolution_date}`}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {procedureCount > 0 && (
            <div>
              <h4 className="section-label mb-2">Procedures & Surgeries</h4>
              <div className="space-y-1">
                {procedures!.map((proc, i) => (
                  <div key={i} className="flex justify-between">
                    <span>{proc.description}</span>
                    {proc.date && <span className="text-xs">{proc.date}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

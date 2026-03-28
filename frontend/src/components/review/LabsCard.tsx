import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { LabPanel } from "../../types/referral";

interface LabsCardProps {
  labs?: LabPanel[];
}

export function LabsCard({ labs }: LabsCardProps) {
  if (!labs || labs.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Recent Labs</CardTitle></CardHeader>
        <CardContent><p className="text-sm italic text-[#64748B]">No recent labs available</p></CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader><CardTitle>Recent Labs</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-6">
          {labs.map((panel, pi) => (
            <div key={pi}>
              <div className="flex justify-between items-center mb-3">
                {panel.panel_name && <span className="text-sm font-semibold text-[#0F172A]">{panel.panel_name}</span>}
                {panel.date && <span className="text-[10px] uppercase font-bold text-[#64748B]">{panel.date}</span>}
              </div>
              <div className="space-y-2">
                {panel.results.map((result, ri) => {
                  const isAbnormal = result.flag && result.flag.toLowerCase() !== "normal";
                  return (
                    <div key={ri} className={`flex justify-between items-center text-sm py-1.5 border-b border-slate-100 last:border-0 ${isAbnormal ? "border-l-4 border-l-[#DC2626] pl-3" : ""}`}>
                      <span className="text-[#0F172A]">{result.test_name}</span>
                      <div className="flex items-center gap-2">
                        <span className={`font-medium ${isAbnormal ? "text-[#DC2626]" : "text-[#0F172A]"}`}>{result.value}</span>
                        {result.unit && <span className="text-xs text-[#64748B]">{result.unit}</span>}
                        {isAbnormal && <span className="text-[10px] font-bold text-[#DC2626] uppercase">{result.flag}</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

import { Pill } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { Medications } from "../../types/referral";

interface MedicationsCardProps {
  medications?: Medications;
}

export function MedicationsCard({ medications }: MedicationsCardProps) {
  const active = medications?.active ?? [];

  return (
    <Card>
      <CardHeader><CardTitle>Active Medications</CardTitle></CardHeader>
      <CardContent>
        {active.length > 0 ? (
          <div className="space-y-4">
            {active.map((med, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#0D9488]/10 flex items-center justify-center text-[#0D9488] shrink-0">
                  <Pill className="h-4 w-4" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-[#0F172A]">{med.name}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {med.dose && <span className="text-xs bg-slate-100 rounded px-1.5 py-0.5 text-[#64748B]">{med.dose}</span>}
                    {med.frequency && <span className="text-xs text-[#64748B]">{med.frequency}</span>}
                    {med.first_prescribed && <span className="text-xs text-[#64748B]">since {med.first_prescribed}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm italic text-[#64748B]">No active medications documented</p>
        )}
      </CardContent>
    </Card>
  );
}

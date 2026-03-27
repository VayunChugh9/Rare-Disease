import { FlaskConical, ExternalLink } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";

export function ClinicalTrialsCard({ flagged, signals }: { flagged: boolean; signals: unknown }) {
  if (!flagged) return null;

  const signalData = signals as Record<string, unknown> | null;
  const signalList = signalData ? Object.entries(signalData).filter(([, v]) => v != null) : [];

  return (
    <Card>
      <CardHeader><CardTitle>Clinical Trial Signals</CardTitle></CardHeader>
      <CardContent>
        <div className="p-4 bg-[#0D9488]/5 border border-[#0D9488]/20 rounded-xl mb-4">
          <div className="flex items-center gap-2 text-[#0D9488] mb-1">
            <FlaskConical className="h-4 w-4" />
            <span className="text-[10px] font-bold uppercase">Potential Eligibility</span>
          </div>
          {signalList.length > 0 ? (
            <div className="space-y-1 mt-2">
              {signalList.map(([key, value], i) => (
                <p key={i} className="text-xs text-[#0F172A]"><span className="font-semibold">{key}:</span> {String(value)}</p>
              ))}
            </div>
          ) : (
            <p className="text-xs font-semibold text-[#0F172A]">Patient may qualify for clinical trials</p>
          )}
        </div>
        <a href="https://clinicaltrials.gov" target="_blank" rel="noopener noreferrer"
          className="text-[11px] text-[#0D9488] hover:underline font-bold uppercase tracking-wider flex items-center gap-1">
          Search ClinicalTrials.gov <ExternalLink className="h-3 w-3" />
        </a>
      </CardContent>
    </Card>
  );
}

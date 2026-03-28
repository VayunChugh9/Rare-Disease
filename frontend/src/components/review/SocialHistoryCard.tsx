import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { SocialHistory } from "../../types/referral";

export function SocialHistoryCard({ socialHistory }: { socialHistory?: SocialHistory }) {
  if (!socialHistory) return null;

  const entries: { label: string; value: string; isSafety?: boolean }[] = [];
  if (socialHistory.smoking_status) entries.push({ label: "Smoking", value: socialHistory.smoking_status });
  if (socialHistory.alcohol_use) entries.push({ label: "Alcohol", value: socialHistory.alcohol_use });
  if (socialHistory.substance_use) entries.push({ label: "Substance Use", value: socialHistory.substance_use });
  if (socialHistory.employment) entries.push({ label: "Employment", value: socialHistory.employment });
  if (socialHistory.education) entries.push({ label: "Education", value: socialHistory.education });
  if (socialHistory.housing) entries.push({ label: "Housing", value: socialHistory.housing });
  if (socialHistory.other) entries.push({ label: "Other", value: socialHistory.other });
  if (socialHistory.safety_concerns) entries.push({ label: "Safety", value: socialHistory.safety_concerns, isSafety: true });

  if (entries.length === 0) return null;

  return (
    <Card>
      <CardHeader><CardTitle>Social History</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-3">
          {entries.map((entry, i) =>
            entry.isSafety ? (
              <div key={i} className="pt-3 border-t border-red-200/50">
                <span className="section-label text-[#DC2626] block mb-1">Safety Alert</span>
                <p className="text-sm font-bold text-[#DC2626] uppercase tracking-tight">{entry.value}</p>
              </div>
            ) : (
              <div key={i} className="flex justify-between text-sm">
                <span className="text-[#64748B]">{entry.label}</span>
                <span className="font-semibold text-[#0F172A]">{entry.value}</span>
              </div>
            )
          )}
        </div>
      </CardContent>
    </Card>
  );
}

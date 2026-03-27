import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { Condition } from "../../types/referral";

interface ConditionsCardProps {
  conditions: Condition[];
  receivingSpecialty?: string;
}

export function ConditionsCard({ conditions, receivingSpecialty }: ConditionsCardProps) {
  if (conditions.length === 0) return null;

  const specialtyLower = (receivingSpecialty ?? "").toLowerCase();

  function isSpecialtyRelevant(diagnosis: string): boolean {
    const diagLower = diagnosis.toLowerCase();
    const keywords: Record<string, string[]> = {
      endocrinology: ["diabetes", "prediabetes", "thyroid", "a1c", "insulin", "obesity", "metabolic"],
      cardiology: ["heart", "cardiac", "hypertension", "afib", "coronary", "cholesterol"],
      neurology: ["seizure", "migraine", "neuropathy", "stroke", "epilepsy"],
      psychiatry: ["depression", "anxiety", "bipolar", "schizophrenia", "ptsd"],
      rheumatology: ["arthritis", "lupus", "fibromyalgia", "autoimmune"],
    };
    const matchKeywords = keywords[specialtyLower] ?? [];
    return matchKeywords.some((kw) => diagLower.includes(kw));
  }

  return (
    <Card>
      <CardHeader><CardTitle>Active Conditions</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-1">
          {conditions.map((cond, i) => {
            const relevant = isSpecialtyRelevant(cond.diagnosis);
            return (
              <div key={i} className={`flex justify-between items-center text-sm p-2 rounded-lg hover:bg-slate-50 transition-colors ${relevant ? "border-l-4 border-[#0D9488] pl-3" : ""}`}>
                <span className="font-medium text-[#0F172A]">{cond.diagnosis}</span>
                {cond.onset_date && <span className="section-label text-[#64748B]">Since {cond.onset_date}</span>}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

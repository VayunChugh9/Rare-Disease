import { motion } from "framer-motion";
import { Card, CardHeader, CardTitle, CardContent } from "../ui/card";
import type { Screening } from "../../types/referral";

const THRESHOLDS: Record<string, number> = {
  "PHQ-9": 10, "GAD-7": 10, "PHQ-2": 3, "AUDIT-C": 4, "DAST-10": 3, "HARK": 1,
};

function isConcerning(instrument: string, score: number): boolean {
  const threshold = THRESHOLDS[instrument.toUpperCase()] ?? THRESHOLDS[instrument];
  if (threshold === undefined) return false;
  return score >= threshold;
}

function getMaxScore(instrument: string): number {
  const maxScores: Record<string, number> = {
    "PHQ-9": 27, "GAD-7": 21, "PHQ-2": 6, "AUDIT-C": 12, "DAST-10": 10, "HARK": 4, "CSSRS": 6,
  };
  return maxScores[instrument.toUpperCase()] ?? maxScores[instrument] ?? 30;
}

export function ScreeningScores({ screenings }: { screenings?: Screening[] }) {
  if (!screenings || screenings.length === 0) return null;

  // Deduplicate: keep only the most recent score per instrument
  const byInstrument = new Map<string, Screening>();
  for (const s of screenings) {
    const key = s.instrument;
    const existing = byInstrument.get(key);
    if (!existing || (s.date && (!existing.date || s.date > existing.date))) {
      byInstrument.set(key, s);
    }
  }

  const deduped = Array.from(byInstrument.values()).sort((a, b) => {
    const aConcerning = isConcerning(a.instrument, parseFloat(a.score) || 0);
    const bConcerning = isConcerning(b.instrument, parseFloat(b.score) || 0);
    if (aConcerning && !bConcerning) return -1;
    if (!aConcerning && bConcerning) return 1;
    return 0;
  });

  return (
    <Card>
      <CardHeader><CardTitle>Screening Scores</CardTitle></CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {deduped.map((screening, i) => {
            const score = parseFloat(screening.score) || 0;
            const max = getMaxScore(screening.instrument);
            const concerning = isConcerning(screening.instrument, score);
            const pct = Math.min((score / max) * 100, 100);

            return (
              <div key={i} className={`p-4 rounded-xl ${concerning ? "bg-red-50/60 border border-red-200/30" : "bg-slate-50/50"}`}>
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-bold text-sm text-[#0F172A]">{screening.instrument}</h4>
                    {screening.date && <p className="text-[10px] text-[#64748B] uppercase">{screening.date}</p>}
                  </div>
                  <span className={`text-2xl font-black ${concerning ? "text-[#DC2626]" : "text-[#0F172A]"}`}>{screening.score}</span>
                </div>
                <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.4, delay: i * 0.1 }}
                    className={`h-full rounded-full ${concerning ? "bg-[#DC2626]" : "bg-[#0D9488]"}`}
                  />
                </div>
                {screening.interpretation && (
                  <p className={`text-[10px] mt-2 font-bold uppercase ${concerning ? "text-[#DC2626]" : "text-[#64748B]"}`}>{screening.interpretation}</p>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

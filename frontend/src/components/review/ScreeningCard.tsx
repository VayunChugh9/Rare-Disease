import type { Screening } from "../../types/referral";

const SEVERITY_STYLES: Record<string, string> = {
  severe: "border-red-200 bg-red-50",
  moderate: "border-amber-200 bg-amber-50",
  mild: "border-blue-100 bg-blue-50",
  positive: "border-amber-200 bg-amber-50",
  negative: "border-stone-200 bg-white",
  default: "border-stone-200 bg-white",
};

const SCORE_STYLES: Record<string, string> = {
  severe: "text-red-700",
  moderate: "text-amber-700",
  mild: "text-blue-700",
  positive: "text-amber-700",
  negative: "text-slate-600",
  default: "text-slate-700",
};

function getSeverity(interpretation: string | undefined): string {
  if (!interpretation) return "default";
  const lower = interpretation.toLowerCase();
  if (lower.includes("severe") || lower.includes("substantial")) return "severe";
  if (lower.includes("moderate") || lower.includes("positive")) return "moderate";
  if (lower.includes("mild") || lower.includes("low")) return "mild";
  if (lower.includes("negative") || lower.includes("minimal")) return "negative";
  return "default";
}

export function ScreeningCard({ screening }: { screening: Screening }) {
  const severity = getSeverity(screening.interpretation);
  const borderStyle = SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.default;
  const scoreStyle = SCORE_STYLES[severity] ?? SCORE_STYLES.default;

  return (
    <div className={`rounded-lg border p-3 ${borderStyle}`}>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
          {screening.instrument}
        </span>
        {screening.date && (
          <span className="text-[10px] text-slate-400">{screening.date}</span>
        )}
      </div>
      <div className={`mt-1 text-2xl font-bold tabular-nums ${scoreStyle}`}>
        {screening.score}
      </div>
      {screening.interpretation && (
        <p className="mt-0.5 text-xs text-slate-600 leading-snug">
          {screening.interpretation}
        </p>
      )}
    </div>
  );
}

export function ScreeningGrid({ screenings }: { screenings: Screening[] }) {
  if (!screenings.length) return null;

  // Show only the most recent of each instrument, prioritize significant ones first
  const latest = new Map<string, Screening>();
  for (const s of screenings) {
    const existing = latest.get(s.instrument);
    if (!existing || (s.date && (!existing.date || s.date > existing.date))) {
      latest.set(s.instrument, s);
    }
  }

  const sorted = Array.from(latest.values()).sort((a, b) => {
    const sevOrder = { severe: 0, moderate: 1, positive: 1, mild: 2, negative: 3, default: 3 };
    const sa = sevOrder[getSeverity(a.interpretation) as keyof typeof sevOrder] ?? 3;
    const sb = sevOrder[getSeverity(b.interpretation) as keyof typeof sevOrder] ?? 3;
    return sa - sb;
  });

  return (
    <div className="grid grid-cols-2 gap-2">
      {sorted.map((s) => (
        <ScreeningCard key={s.instrument + s.date} screening={s} />
      ))}
    </div>
  );
}

import type { ReferralStatus, TriageUrgency } from "../../types/referral";
import { Badge } from "../ui/badge";

const STATUS_STYLES: Record<ReferralStatus, string> = {
  processing: "bg-blue-100 text-blue-700",
  pending_review: "bg-amber-100 text-amber-700",
  reviewed: "bg-green-100 text-green-700",
  finalized: "bg-slate-100 text-slate-700",
  archived: "bg-gray-100 text-gray-500",
};

const STATUS_LABELS: Record<ReferralStatus, string> = {
  processing: "Processing",
  pending_review: "Ready for Review",
  reviewed: "Reviewed",
  finalized: "Finalized",
  archived: "Archived",
};

export function StatusBadge({ status }: { status: ReferralStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ${STATUS_STYLES[status]}`}>
      {STATUS_LABELS[status]}
    </span>
  );
}

const URGENCY_COLORS: Record<TriageUrgency, string> = {
  urgent: "#DC2626",
  semi_urgent: "#EA580C",
  routine: "#0D9488",
  needs_clarification: "#CA8A04",
  inappropriate: "#6B7280",
};

const URGENCY_LABELS: Record<TriageUrgency, string> = {
  urgent: "Urgent",
  semi_urgent: "Semi-Urgent",
  routine: "Routine",
  needs_clarification: "Needs Clarification",
  inappropriate: "Inappropriate",
};

export function TriageBadgeLarge({
  urgency,
  confidence,
}: {
  urgency: TriageUrgency;
  confidence: number;
}) {
  const color = URGENCY_COLORS[urgency];
  const label = URGENCY_LABELS[urgency];
  const pct = Math.round(confidence * 100);

  return (
    <div className="flex flex-col items-end">
      <div
        className="px-5 py-2 rounded-xl shadow-lg flex flex-col items-center"
        style={{ backgroundColor: color, boxShadow: `0 0 20px ${color}40` }}
      >
        <span className="text-white font-black text-sm uppercase tracking-tight">{label}</span>
        <div className="w-full h-1 bg-white/20 rounded-full mt-1.5 overflow-hidden">
          <div className="h-full bg-white rounded-full transition-all duration-1000 ease-out" style={{ width: `${pct}%` }} />
        </div>
      </div>
      <span className="text-[10px] text-[#64748B] mt-1">{pct}% confidence</span>
    </div>
  );
}

export function TriageBadge({ urgency }: { urgency: TriageUrgency }) {
  return <Badge variant={urgency}>{URGENCY_LABELS[urgency]}</Badge>;
}

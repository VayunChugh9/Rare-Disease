import type { ReferralStatus, TriageUrgency } from "../../types/referral";

const STATUS_STYLES: Record<string, string> = {
  processing: "bg-blue-50 text-blue-700 border-blue-200",
  pending_review: "bg-amber-50 text-amber-700 border-amber-200",
  reviewed: "bg-emerald-50 text-emerald-700 border-emerald-200",
  finalized: "bg-slate-100 text-slate-600 border-slate-200",
  archived: "bg-gray-50 text-gray-500 border-gray-200",
};

const STATUS_LABELS: Record<string, string> = {
  processing: "Processing",
  pending_review: "Ready for Review",
  reviewed: "Reviewed",
  finalized: "Finalized",
  archived: "Archived",
};

export function StatusBadge({ status }: { status: ReferralStatus }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.processing;
  const label = STATUS_LABELS[status] ?? status;
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${style}`}
    >
      {label}
    </span>
  );
}

const TRIAGE_STYLES: Record<string, string> = {
  urgent: "bg-red-50 text-red-700 border-red-200",
  semi_urgent: "bg-amber-50 text-amber-700 border-amber-200",
  routine: "bg-emerald-50 text-emerald-700 border-emerald-200",
  needs_clarification: "bg-gray-50 text-gray-600 border-gray-200",
  inappropriate: "bg-gray-50 text-gray-500 border-gray-200",
};

const TRIAGE_LABELS: Record<string, string> = {
  urgent: "Urgent",
  semi_urgent: "High Priority",
  routine: "Routine",
  needs_clarification: "Needs Clarification",
  inappropriate: "Inappropriate",
};

export function TriageBadge({ urgency }: { urgency: TriageUrgency }) {
  const key = urgency?.toLowerCase().replace("-", "_") ?? "needs_clarification";
  const style = TRIAGE_STYLES[key] ?? TRIAGE_STYLES.needs_clarification;
  const label = TRIAGE_LABELS[key] ?? urgency;
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold ${style}`}
    >
      {label}
    </span>
  );
}

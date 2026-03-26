import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Filter, Upload, Clock } from "lucide-react";
import { listReferrals } from "../../api/client";
import type { ReferralListItem, ReferralStatus, TriageUrgency } from "../../types/referral";
import { StatusBadge, TriageBadge } from "../shared/StatusBadge";
import { QueueSkeleton } from "../shared/LoadingSkeleton";
import { EmptyState } from "../shared/EmptyState";

const STATUS_FILTERS: { value: string; label: string }[] = [
  { value: "", label: "All" },
  { value: "pending_review", label: "Ready for Review" },
  { value: "processing", label: "Processing" },
  { value: "reviewed", label: "Reviewed" },
  { value: "finalized", label: "Finalized" },
];

export function ReferralQueue() {
  const navigate = useNavigate();
  const [referrals, setReferrals] = useState<ReferralListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    setLoading(true);
    listReferrals(statusFilter || undefined)
      .then((data) => {
        setReferrals(data.referrals);
        setTotal(data.total);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  const filtered = search
    ? referrals.filter((r) =>
        (r.one_line_summary ?? "").toLowerCase().includes(search.toLowerCase())
      )
    : referrals;

  function formatDate(iso: string | null) {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  }

  function extractPatientName(summary: string | null): string {
    if (!summary) return "Unknown Patient";
    const parts = summary.split(",")[0].trim();
    return parts || "Unknown Patient";
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-lg font-semibold text-slate-800">
            Referral Queue
          </h1>
          <p className="text-sm text-slate-500">
            {total} referral{total !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          onClick={() => navigate("/upload")}
          className="flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-teal-700 transition-colors"
        >
          <Upload className="h-4 w-4" />
          Upload Referral
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search referrals..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-stone-200 bg-white py-2 pl-9 pr-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-teal-300 focus:outline-none focus:ring-1 focus:ring-teal-300"
          />
        </div>

        <div className="flex items-center gap-1.5">
          <Filter className="h-4 w-4 text-slate-400" />
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={`rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors ${
                statusFilter === f.value
                  ? "bg-stone-200 text-slate-800"
                  : "text-slate-500 hover:bg-stone-100"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <QueueSkeleton />
      ) : error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No referrals found"
          description={
            statusFilter
              ? "No referrals match this filter."
              : "Upload a referral document to get started."
          }
          action={
            <button
              onClick={() => navigate("/upload")}
              className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700"
            >
              Upload Referral
            </button>
          }
        />
      ) : (
        <div className="rounded-xl border border-stone-200 bg-white shadow-sm overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-stone-100 bg-stone-50/50">
                <th className="px-4 py-2.5 text-left text-xs font-medium text-slate-500">
                  Patient
                </th>
                <th className="px-4 py-2.5 text-left text-xs font-medium text-slate-500">
                  Summary
                </th>
                <th className="px-4 py-2.5 text-left text-xs font-medium text-slate-500">
                  Status
                </th>
                <th className="px-4 py-2.5 text-left text-xs font-medium text-slate-500">
                  Triage
                </th>
                <th className="px-4 py-2.5 text-left text-xs font-medium text-slate-500">
                  <Clock className="inline h-3.5 w-3.5" /> Date
                </th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr
                  key={r.referral_id}
                  onClick={() => navigate(`/review/${r.referral_id}`)}
                  className="border-b border-stone-50 cursor-pointer hover:bg-stone-50/80 transition-colors"
                >
                  <td className="px-4 py-3">
                    <span className="text-sm font-medium text-slate-800">
                      {extractPatientName(r.one_line_summary)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-slate-600 line-clamp-1">
                      {r.one_line_summary ?? "Processing..."}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={r.status} />
                  </td>
                  <td className="px-4 py-3">
                    <TriageBadge urgency={r.triage_urgency} />
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-slate-500">
                      {formatDate(r.created_at)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

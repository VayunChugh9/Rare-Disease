import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, FileText, CheckCircle, Download, Sparkles } from "lucide-react";
import { getReferral, saveCorrection } from "../../api/client";
import type { ReferralDetail } from "../../types/referral";
import { ReviewSkeleton } from "../shared/LoadingSkeleton";
import { PatientHeader } from "./PatientHeader";
import { FindingsPanel } from "./FindingsPanel";
import { ScreeningGrid } from "./ScreeningCard";
import { ClinicalSections } from "./ClinicalSections";
import { TriageBadge } from "../shared/StatusBadge";

export function ReviewWorkspace() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ReferralDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    getReferral(id)
      .then((d) => {
        setData(d);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handleCorrection = useCallback(
    async (fieldPath: string, oldValue: string, newValue: string) => {
      if (!id) return;
      try {
        await saveCorrection(id, {
          field_path: fieldPath,
          original_value: oldValue,
          corrected_value: newValue,
          correction_type: "value_change",
        });
      } catch (err) {
        console.error("Failed to save correction:", err);
      }
    },
    [id]
  );

  if (loading) {
    return (
      <div className="h-full">
        <ReviewSkeleton />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-sm text-red-600 mb-2">{error ?? "Referral not found"}</p>
          <button
            onClick={() => navigate("/")}
            className="text-sm text-teal-600 hover:underline"
          >
            Back to queue
          </button>
        </div>
      </div>
    );
  }

  const ed = data.extracted_data;
  const cd = ed.clinical_data;
  const triage = data.triage;

  return (
    <div className="flex h-full flex-col">
      {/* Patient Header */}
      <PatientHeader
        patient={ed.patient}
        referral={ed.referral}
        referringProvider={ed.referring_provider}
        status={data.status}
        urgency={triage.urgency}
        createdAt={data.created_at}
      />

      {/* Split panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* LEFT: Source / Summary Narrative */}
        <div className="w-1/2 border-r border-stone-200 overflow-y-auto bg-stone-50/50">
          <div className="p-5">
            {/* Back link */}
            <button
              onClick={() => navigate("/")}
              className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 mb-4"
            >
              <ArrowLeft className="h-3 w-3" /> Back to queue
            </button>

            {/* Summary Narrative */}
            <div className="rounded-xl border border-stone-200 bg-white p-5 mb-4">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="h-4 w-4 text-teal-600" />
                <h2 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                  AI-Generated Summary
                </h2>
                <span className="ml-auto text-[10px] text-slate-400 bg-stone-100 rounded px-1.5 py-0.5">
                  Review before finalizing
                </span>
              </div>
              {data.summary_narrative ? (
                <div className="prose prose-sm prose-slate max-w-none">
                  {data.summary_narrative.split("\n\n").map((para, i) => (
                    <p key={i} className="text-sm text-slate-700 leading-relaxed mb-3 last:mb-0">
                      {para}
                    </p>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400 italic">
                  No summary available
                </p>
              )}
            </div>

            {/* Triage Rationale */}
            <div className="rounded-xl border border-stone-200 bg-white p-5 mb-4">
              <div className="flex items-center gap-2 mb-3">
                <h2 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                  Triage Recommendation
                </h2>
              </div>
              <div className="flex items-start gap-3">
                <TriageBadge urgency={triage.urgency} />
                <div className="flex-1">
                  {triage.confidence && (
                    <div className="flex items-center gap-2 mb-1.5">
                      <div className="h-1.5 flex-1 max-w-[120px] rounded-full bg-stone-200">
                        <div
                          className="h-1.5 rounded-full bg-teal-500"
                          style={{ width: `${triage.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-slate-400">
                        {Math.round(triage.confidence * 100)}% confidence
                      </span>
                    </div>
                  )}
                  {triage.reasoning && (
                    <p className="text-sm text-slate-600 leading-relaxed">
                      {triage.reasoning}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Source Document Info */}
            <div className="rounded-xl border border-stone-200 bg-white p-5">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="h-4 w-4 text-slate-400" />
                <h2 className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                  Source Document
                </h2>
              </div>
              <div className="text-xs text-slate-500 space-y-1">
                {ed.extraction_metadata?.extraction_path && (
                  <p>
                    <span className="text-slate-600 font-medium">Extraction:</span>{" "}
                    {ed.extraction_metadata.extraction_path === "structured_parse"
                      ? "CCD/CCDA structured parse (deterministic)"
                      : "LLM extraction"}
                  </p>
                )}
                {ed.extraction_metadata?.sections_found && (
                  <p>
                    <span className="text-slate-600 font-medium">Sections found:</span>{" "}
                    {ed.extraction_metadata.sections_found.join(", ")}
                  </p>
                )}
                {ed.extraction_metadata?.sections_missing &&
                  ed.extraction_metadata.sections_missing.length > 0 && (
                    <p className="text-amber-600">
                      <span className="font-medium">Missing sections:</span>{" "}
                      {ed.extraction_metadata.sections_missing.join(", ")}
                    </p>
                  )}
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT: Structured Review */}
        <div className="w-1/2 overflow-y-auto">
          <div className="p-5 space-y-4">
            {/* Key Findings */}
            <FindingsPanel
              redFlags={triage.red_flags}
              actionItems={triage.action_items}
              missingInfo={triage.missing_info}
            />

            {/* Screenings */}
            {cd?.screenings && cd.screenings.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wide mb-2">
                  Screening Scores
                </h3>
                <ScreeningGrid screenings={cd.screenings} />
              </div>
            )}

            {/* Clinical Data Sections */}
            {cd && (
              <ClinicalSections data={cd} onCorrection={handleCorrection} />
            )}

            {/* Action Bar */}
            <div className="flex items-center gap-3 pt-2 pb-4">
              <button className="flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-teal-700 transition-colors">
                <CheckCircle className="h-4 w-4" />
                Finalize Review
              </button>
              <button className="flex items-center gap-2 rounded-lg border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-stone-50 transition-colors">
                <Download className="h-4 w-4" />
                Download PDF
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

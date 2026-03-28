import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getReferral, getReferralStatus, saveCorrection, generatePdf, finalizeReferral } from "../../api/client";
import type { ReferralDetail } from "../../types/referral";
import { ReviewSkeleton } from "../shared/LoadingSkeleton";
import { PatientHeader } from "./PatientHeader";
import { AlertStrip } from "./AlertStrip";
import { ActionChips } from "./ActionChips";
import { AISummaryPanel } from "./AISummaryPanel";
import { VitalsCard } from "./VitalsCard";
import { MedicationsCard } from "./MedicationsCard";
import { ConditionsCard } from "./ConditionsCard";
import { LabsCard } from "./LabsCard";
import { ScreeningScores } from "./ScreeningScores";
import { SocialHistoryCard } from "./SocialHistoryCard";
import { AllergiesCard } from "./AllergiesCard";
import { ClinicalTrialsCard } from "./ClinicalTrialsCard";
import { HistoricalContext } from "./HistoricalContext";

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.05, duration: 0.3, ease: [0.4, 0, 0.2, 1] as [number, number, number, number] },
  }),
};

export function ReviewWorkspace() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<ReferralDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [finalizing, setFinalizing] = useState(false);

  const fetchReferral = useCallback(() => {
    if (!id) return;
    getReferral(id)
      .then((d) => { setData(d); setError(null); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    setLoading(true);
    fetchReferral();
  }, [fetchReferral]);

  // Poll for status when referral is still processing
  useEffect(() => {
    if (!id || !data || data.status !== "processing") return;
    const interval = setInterval(async () => {
      try {
        const status = await getReferralStatus(id);
        if (status.status !== "processing") {
          clearInterval(interval);
          fetchReferral();
        }
      } catch {
        // ignore polling errors
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [id, data?.status, fetchReferral]);

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

  const handleGeneratePdf = useCallback(async () => {
    if (!id) return;
    setPdfLoading(true);
    try {
      await generatePdf(id);
    } catch (err) {
      alert(err instanceof Error ? err.message : "PDF generation failed");
    } finally {
      setPdfLoading(false);
    }
  }, [id]);

  const handleFinalize = useCallback(async () => {
    if (!id) return;
    setFinalizing(true);
    try {
      await finalizeReferral(id);
      fetchReferral(); // refresh to show updated status
    } catch (err) {
      alert(err instanceof Error ? err.message : "Finalize failed");
    } finally {
      setFinalizing(false);
    }
  }, [id, fetchReferral]);

  if (loading) {
    return <div className="h-full pt-4"><ReviewSkeleton /></div>;
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-sm text-red-600 mb-2">{error ?? "Referral not found"}</p>
          <button onClick={() => navigate("/queue")} className="text-sm text-[#0D9488] hover:underline">
            Back to queue
          </button>
        </div>
      </div>
    );
  }

  if (data.status === "processing") {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-[#0D9488]" />
          <h2 className="text-sm font-semibold text-slate-800 mb-1">Processing Referral</h2>
          <p className="text-sm text-slate-500">Extracting clinical data and generating AI summary...</p>
          <p className="text-xs text-slate-400 mt-2">This page will update automatically.</p>
        </div>
      </div>
    );
  }

  const ed = data.extracted_data;
  const cd = ed.clinical_data;
  const triage = data.triage;

  let sectionIndex = 0;

  return (
    <div className="flex flex-col">
      <PatientHeader
        patient={ed.patient}
        referral={ed.referral}
        referringProvider={ed.referring_provider}
        status={data.status}
        urgency={triage.urgency}
        confidence={triage.confidence}
        createdAt={data.created_at}
        onGeneratePdf={handleGeneratePdf}
        onFinalize={handleFinalize}
        pdfLoading={pdfLoading}
        finalizing={finalizing}
        clinicalTrialFlagged={data.clinical_trial_flagged}
      />

      {/* Referral Reason - most prominent, above everything */}
      {ed.referral?.reason && (
        <div className="mx-6 mb-4">
          <div className="glass rounded-xl p-5 border-l-4 border-[#0D9488]">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#0D9488] mb-1.5 block">Reason for Referral</span>
            <p className="text-lg font-semibold text-slate-800 leading-snug">{ed.referral.reason}</p>
          </div>
        </div>
      )}

      <AlertStrip redFlags={triage.red_flags} missingInfo={triage.missing_info} />
      <ActionChips items={triage.action_items} />

      <div className="flex mx-6 mb-6 gap-0">
        <AISummaryPanel
          summaryNarrative={data.summary_narrative}
          triageReasoning={triage.reasoning}
          referralReason={ed.referral?.reason ?? null}
          oneLineSummary={data.one_line_summary}
        />

        <div className="flex-1 min-w-0 pl-4 space-y-6 pb-8">
          {/* Section 1: Vitals + Medications */}
          <motion.div className="flex gap-6" custom={sectionIndex++} initial="hidden" animate="visible" variants={cardVariants}>
            <div className="w-[55%]"><VitalsCard vitals={cd?.recent_vitals} /></div>
            <div className="w-[45%]"><MedicationsCard medications={cd?.medications} /></div>
          </motion.div>

          {/* Section 2: Conditions + Labs */}
          <motion.div className="flex gap-6" custom={sectionIndex++} initial="hidden" animate="visible" variants={cardVariants}>
            <div className="w-[50%]">
              <ConditionsCard conditions={cd?.problem_list?.active ?? []} receivingSpecialty={ed.referral?.receiving_specialty} />
            </div>
            <div className="w-[50%]"><LabsCard labs={cd?.recent_labs} /></div>
          </motion.div>

          {/* Section 3: Screening Scores */}
          <motion.div custom={sectionIndex++} initial="hidden" animate="visible" variants={cardVariants}>
            <ScreeningScores screenings={cd?.screenings} />
          </motion.div>

          {/* Section 4: Social + Allergies + Trials */}
          <motion.div className="grid grid-cols-10 gap-6" custom={sectionIndex++} initial="hidden" animate="visible" variants={cardVariants}>
            <div className="col-span-4"><SocialHistoryCard socialHistory={cd?.social_history} /></div>
            <div className="col-span-3"><AllergiesCard allergies={cd?.allergies} /></div>
            <div className="col-span-3">
              <ClinicalTrialsCard flagged={data.clinical_trial_flagged} signals={data.clinical_trial_signals} />
            </div>
          </motion.div>

          {/* Section 5: Historical Context */}
          <motion.div custom={sectionIndex++} initial="hidden" animate="visible" variants={cardVariants}>
            <HistoricalContext significantHistory={cd?.problem_list?.significant_history} procedures={cd?.procedures_and_surgeries} />
          </motion.div>
        </div>
      </div>
    </div>
  );
}

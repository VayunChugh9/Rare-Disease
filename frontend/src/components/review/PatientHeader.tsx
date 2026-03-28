import type { Patient, ReferralInfo, ReferringProvider, ReferralStatus, TriageUrgency } from "../../types/referral";
import { Button } from "../ui/button";
import { StatusBadge, TriageBadgeLarge } from "../shared/StatusBadge";
import { FileText, CheckCircle, Loader2, FlaskConical } from "lucide-react";

interface PatientHeaderProps {
  patient?: Patient;
  referral?: ReferralInfo;
  referringProvider?: ReferringProvider;
  status: ReferralStatus;
  urgency: TriageUrgency;
  confidence: number;
  createdAt: string | null;
  onGeneratePdf: () => void;
  onFinalize: () => void;
  pdfLoading?: boolean;
  finalizing?: boolean;
  clinicalTrialFlagged?: boolean;
}

export function PatientHeader({
  patient, referral, referringProvider, status, urgency, confidence, createdAt, onGeneratePdf, onFinalize,
  pdfLoading, finalizing, clinicalTrialFlagged,
}: PatientHeaderProps) {
  const name = [patient?.first_name, patient?.last_name].filter(Boolean).join(" ") || "Unknown Patient";
  const ageSex = [patient?.age ? `${patient.age}` : null, patient?.sex?.[0]?.toUpperCase()].filter(Boolean).join("");

  return (
    <header className="glass sticky top-[60px] z-40 rounded-2xl p-6 mx-6 mt-4 mb-4 shadow-sm flex justify-between items-start">
      <div className="w-[70%]">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-[24px] font-semibold text-[#0F172A]">{name}</h1>
          {ageSex && <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-[11px] font-bold text-[#64748B]">{ageSex}</span>}
          {patient?.date_of_birth && <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-[11px] font-bold text-[#64748B]">DOB {patient.date_of_birth}</span>}
          {patient?.mrn && <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-[11px] font-bold text-[#64748B] uppercase">MRN {patient.mrn.slice(0, 8)}</span>}
        </div>
        <div className="flex items-center gap-4 text-sm text-[#64748B]">
          {referral?.receiving_specialty && (
            <span className="flex items-center gap-1.5"><span className="section-label">To:</span> {referral.receiving_specialty}</span>
          )}
          {referringProvider?.name && (
            <>
              <span className="text-slate-300">|</span>
              <span className="flex items-center gap-1.5">
                <span className="section-label">From:</span> {referringProvider.name}
                {referringProvider.practice_name && `, ${referringProvider.practice_name}`}
              </span>
            </>
          )}
          {(referral?.date_of_referral || createdAt) && (
            <>
              <span className="text-slate-300">|</span>
              <span className="flex items-center gap-1.5">
                <span className="section-label">Date:</span> {referral?.date_of_referral || createdAt}
              </span>
            </>
          )}
        </div>
      </div>
      <div className="w-[30%] flex flex-col items-end gap-3">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="pulse-dot absolute inline-flex h-full w-full rounded-full bg-[#0D9488] opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#0D9488]" />
            </span>
            <StatusBadge status={status} />
          </div>
          <TriageBadgeLarge urgency={urgency} confidence={confidence} />
        </div>
        {clinicalTrialFlagged && (
          <a href="https://clinicaltrials.gov" target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-purple-50 border border-purple-200 text-purple-700 text-xs font-semibold hover:bg-purple-100 transition-colors">
            <FlaskConical className="h-3.5 w-3.5" />
            Clinical Trial Candidate
          </a>
        )}
        <div className="flex gap-2">
          <Button size="sm" onClick={onGeneratePdf} disabled={pdfLoading}>
            {pdfLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
            {pdfLoading ? "Generating..." : "Generate PDF"}
          </Button>
          {status !== "finalized" ? (
            <Button variant="outline" size="sm" onClick={onFinalize} disabled={finalizing}>
              {finalizing ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
              {finalizing ? "Finalizing..." : "Finalize Review"}
            </Button>
          ) : (
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-50 text-emerald-700 text-xs font-medium">
              <CheckCircle className="h-3.5 w-3.5" /> Finalized
            </span>
          )}
        </div>
      </div>
    </header>
  );
}

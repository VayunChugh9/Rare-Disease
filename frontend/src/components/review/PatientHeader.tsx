import type { Patient, ReferralInfo, ReferringProvider, ReferralStatus, TriageUrgency } from "../../types/referral";
import { Button } from "../ui/button";
import { StatusBadge, TriageBadgeLarge } from "../shared/StatusBadge";
import { FileText, CheckCircle } from "lucide-react";

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
}

export function PatientHeader({
  patient, referral, referringProvider, status, urgency, confidence, createdAt, onGeneratePdf, onFinalize,
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
        <div className="flex gap-2">
          <Button size="sm" onClick={onGeneratePdf}>
            <FileText className="h-4 w-4" />
            Generate PDF
          </Button>
          <Button variant="outline" size="sm" onClick={onFinalize}>
            <CheckCircle className="h-4 w-4" />
            Finalize Review
          </Button>
        </div>
      </div>
    </header>
  );
}

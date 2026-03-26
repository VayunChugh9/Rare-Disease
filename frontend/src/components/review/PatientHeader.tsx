import { User } from "lucide-react";
import type { Patient, ReferralInfo, ReferringProvider } from "../../types/referral";
import { StatusBadge, TriageBadge } from "../shared/StatusBadge";
import type { ReferralStatus, TriageUrgency } from "../../types/referral";

interface PatientHeaderProps {
  patient?: Patient;
  referral?: ReferralInfo;
  referringProvider?: ReferringProvider;
  status: ReferralStatus;
  urgency: TriageUrgency;
  createdAt: string | null;
}

export function PatientHeader({
  patient,
  referral,
  referringProvider,
  status,
  urgency,
  createdAt,
}: PatientHeaderProps) {
  const name = patient
    ? `${patient.first_name ?? ""} ${patient.last_name ?? ""}`.trim()
    : "Unknown Patient";

  const ageStr = patient?.age ? `${patient.age}yo` : "";
  const sexStr = patient?.sex === "M" ? "Male" : patient?.sex === "F" ? "Female" : "";
  const demo = [ageStr, sexStr].filter(Boolean).join(", ");

  return (
    <div className="border-b border-stone-200 bg-white px-6 py-4">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-stone-100">
            <User className="h-5 w-5 text-slate-500" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-slate-800">{name}</h1>
            <div className="flex items-center gap-2 mt-0.5 text-sm text-slate-500">
              {demo && <span>{demo}</span>}
              {patient?.date_of_birth && (
                <>
                  <span className="text-stone-300">|</span>
                  <span>DOB {patient.date_of_birth}</span>
                </>
              )}
              {patient?.mrn && (
                <>
                  <span className="text-stone-300">|</span>
                  <span>MRN {patient.mrn}</span>
                </>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={status} />
          <TriageBadge urgency={urgency} />
        </div>
      </div>

      {/* Referral context bar */}
      {referral && (
        <div className="mt-3 flex items-center gap-4 text-xs text-slate-500">
          {referral.receiving_specialty && (
            <span>
              <span className="font-medium text-slate-600">To:</span>{" "}
              {referral.receiving_specialty}
            </span>
          )}
          {referringProvider?.name && (
            <span>
              <span className="font-medium text-slate-600">From:</span>{" "}
              {referringProvider.name}
              {referringProvider.practice_name &&
                ` at ${referringProvider.practice_name}`}
            </span>
          )}
          {referral.urgency_stated && (
            <span>
              <span className="font-medium text-slate-600">Stated urgency:</span>{" "}
              {referral.urgency_stated}
            </span>
          )}
          {createdAt && (
            <span className="ml-auto text-slate-400">
              {new Date(createdAt).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

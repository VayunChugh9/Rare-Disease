import { ChevronDown, ChevronRight, Pill, HeartPulse, Stethoscope, Shield, Beaker, Users } from "lucide-react";
import { useState } from "react";
import type { ClinicalData } from "../../types/referral";
import { EditableField } from "../shared/EditableField";

interface SectionProps {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
  defaultOpen?: boolean;
  count?: number;
}

function Section({ title, icon: Icon, children, defaultOpen = true, count }: SectionProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-stone-100 last:border-b-0">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-4 py-2.5 text-left hover:bg-stone-50/50 transition-colors"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-slate-400" />
        )}
        <Icon className="h-3.5 w-3.5 text-slate-500" />
        <span className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
          {title}
        </span>
        {count !== undefined && (
          <span className="ml-auto text-[10px] text-slate-400 font-medium">
            {count}
          </span>
        )}
      </button>
      {open && <div className="px-4 pb-3">{children}</div>}
    </div>
  );
}

interface ClinicalSectionsProps {
  data: ClinicalData;
  onCorrection: (fieldPath: string, oldValue: string, newValue: string) => void;
}

export function ClinicalSections({ data, onCorrection }: ClinicalSectionsProps) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white overflow-hidden">
      {/* Conditions */}
      {data.problem_list && (
        <Section
          title="Conditions"
          icon={Stethoscope}
          count={data.problem_list.active.length}
        >
          <div className="space-y-0.5">
            {data.problem_list.active.map((c, i) => (
              <EditableField
                key={i}
                label={c.onset_date ?? "Active"}
                value={c.diagnosis}
                fieldPath={`clinical_data.problem_list.active.${i}.diagnosis`}
                onSave={onCorrection}
              />
            ))}
            {data.problem_list.significant_history.length > 0 && (
              <div className="mt-2 pt-2 border-t border-stone-100">
                <p className="text-[10px] font-medium text-slate-400 uppercase tracking-wider mb-1">
                  Significant History
                </p>
                {data.problem_list.significant_history.map((h, i) => (
                  <div key={i} className="flex items-start gap-2 py-1">
                    <span className="min-w-[120px] shrink-0 text-xs text-slate-400">
                      {h.significance_reason ?? "History"}
                    </span>
                    <span className="text-sm text-slate-600">{h.diagnosis}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Medications */}
      {data.medications && (
        <Section
          title="Medications"
          icon={Pill}
          count={data.medications.active.length}
        >
          {data.medications.active.length === 0 ? (
            <p className="text-xs text-slate-400 italic">No active medications</p>
          ) : (
            <div className="space-y-0.5">
              {data.medications.active.map((m, i) => (
                <EditableField
                  key={i}
                  label={[m.dose, m.frequency].filter(Boolean).join(" ") || "Active"}
                  value={m.name}
                  fieldPath={`clinical_data.medications.active.${i}.name`}
                  onSave={onCorrection}
                />
              ))}
            </div>
          )}
          {data.medications.recently_stopped.length > 0 && (
            <div className="mt-2 pt-2 border-t border-stone-100">
              <p className="text-[10px] font-medium text-slate-400 uppercase tracking-wider mb-1">
                Recently Stopped
              </p>
              {data.medications.recently_stopped.map((m, i) => (
                <div key={i} className="flex items-start gap-2 py-1 text-xs text-slate-500">
                  <span className="min-w-[120px] shrink-0">
                    Stopped {m.stop_date ?? "recently"}
                  </span>
                  <span>{m.name}</span>
                  {m.reason_stopped && (
                    <span className="text-slate-400">({m.reason_stopped})</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </Section>
      )}

      {/* Vitals */}
      {data.recent_vitals && (
        <Section title="Vitals" icon={HeartPulse}>
          <div className="grid grid-cols-3 gap-x-4 gap-y-1">
            {data.recent_vitals.weight && (
              <EditableField
                label="Weight"
                value={data.recent_vitals.weight}
                fieldPath="clinical_data.recent_vitals.weight"
                onSave={onCorrection}
              />
            )}
            {data.recent_vitals.bmi && (
              <EditableField
                label="BMI"
                value={data.recent_vitals.bmi}
                fieldPath="clinical_data.recent_vitals.bmi"
                onSave={onCorrection}
              />
            )}
            {data.recent_vitals.heart_rate && (
              <EditableField
                label="Heart Rate"
                value={data.recent_vitals.heart_rate}
                fieldPath="clinical_data.recent_vitals.heart_rate"
                onSave={onCorrection}
              />
            )}
            {data.recent_vitals.blood_pressure && (
              <EditableField
                label="Blood Pressure"
                value={data.recent_vitals.blood_pressure}
                fieldPath="clinical_data.recent_vitals.blood_pressure"
                onSave={onCorrection}
              />
            )}
            {data.recent_vitals.height && (
              <EditableField
                label="Height"
                value={data.recent_vitals.height}
                fieldPath="clinical_data.recent_vitals.height"
                onSave={onCorrection}
              />
            )}
            {data.recent_vitals.respiratory_rate && (
              <EditableField
                label="Resp. Rate"
                value={data.recent_vitals.respiratory_rate}
                fieldPath="clinical_data.recent_vitals.respiratory_rate"
                onSave={onCorrection}
              />
            )}
          </div>
          {data.recent_vitals.date && (
            <p className="mt-1 text-[10px] text-slate-400">
              As of {data.recent_vitals.date}
            </p>
          )}
        </Section>
      )}

      {/* Allergies */}
      {data.allergies && (
        <Section title="Allergies" icon={Shield}>
          {data.allergies.no_known_allergies ? (
            <p className="text-xs text-emerald-600 font-medium">
              No known allergies (NKDA)
            </p>
          ) : data.allergies.known_allergies.length > 0 ? (
            <div className="space-y-1">
              {data.allergies.known_allergies.map((a, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className="font-medium text-slate-700">{a.substance}</span>
                  {a.reaction && (
                    <span className="text-xs text-slate-500">({a.reaction})</span>
                  )}
                  {a.severity && (
                    <span className="text-xs text-red-600">{a.severity}</span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No allergy information</p>
          )}
        </Section>
      )}

      {/* Labs */}
      {data.recent_labs && data.recent_labs.length > 0 && (
        <Section
          title="Recent Labs"
          icon={Beaker}
          count={data.recent_labs.reduce((n, p) => n + p.results.length, 0)}
          defaultOpen={false}
        >
          {data.recent_labs.map((panel, pi) => (
            <div key={pi} className="mb-2 last:mb-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-medium text-slate-600">
                  {panel.panel_name ?? "Lab Panel"}
                </span>
                {panel.date && (
                  <span className="text-[10px] text-slate-400">{panel.date}</span>
                )}
              </div>
              <table className="w-full text-xs">
                <tbody>
                  {panel.results.map((r, ri) => (
                    <tr key={ri} className="border-b border-stone-50">
                      <td className="py-1 text-slate-600 w-1/3">{r.test_name}</td>
                      <td className={`py-1 font-medium ${
                        r.flag === "abnormal" || r.flag === "high" || r.flag === "low"
                          ? "text-amber-700"
                          : "text-slate-700"
                      }`}>
                        {r.value} {r.unit}
                      </td>
                      <td className="py-1 text-slate-400">{r.flag ?? ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </Section>
      )}

      {/* Social History */}
      {data.social_history && (
        <Section title="Social History" icon={Users}>
          <div className="space-y-0.5">
            <EditableField
              label="Smoking"
              value={data.social_history.smoking_status}
              fieldPath="clinical_data.social_history.smoking_status"
              onSave={onCorrection}
            />
            {data.social_history.alcohol_use && (
              <EditableField
                label="Alcohol"
                value={data.social_history.alcohol_use}
                fieldPath="clinical_data.social_history.alcohol_use"
                onSave={onCorrection}
              />
            )}
            {data.social_history.employment && (
              <EditableField
                label="Employment"
                value={data.social_history.employment}
                fieldPath="clinical_data.social_history.employment"
                onSave={onCorrection}
              />
            )}
            {data.social_history.safety_concerns && (
              <div className="mt-1 rounded border border-red-200 bg-red-50 px-2 py-1.5">
                <span className="text-xs font-semibold text-red-700">Safety: </span>
                <span className="text-xs text-red-800">
                  {data.social_history.safety_concerns}
                </span>
              </div>
            )}
          </div>
        </Section>
      )}
    </div>
  );
}

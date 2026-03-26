/* TypeScript types matching backend API response shapes */

export interface ReferralListItem {
  referral_id: string;
  status: ReferralStatus;
  one_line_summary: string | null;
  triage_urgency: TriageUrgency;
  triage_confidence: number;
  created_at: string | null;
}

export interface ReferralListResponse {
  total: number;
  referrals: ReferralListItem[];
}

export interface ReferralDetail {
  referral_id: string;
  status: ReferralStatus;
  created_at: string | null;
  one_line_summary: string | null;
  summary_narrative: string | null;
  triage: TriageInfo;
  clinical_trial_flagged: boolean;
  clinical_trial_signals: unknown;
  extracted_data: ExtractedData;
}

export interface TriageInfo {
  urgency: TriageUrgency;
  confidence: number;
  reasoning: string | null;
  red_flags: string[];
  action_items: string[];
  missing_info: string[];
}

export interface ExtractedData {
  referral_id?: string;
  patient?: Patient;
  referring_provider?: ReferringProvider;
  referral?: ReferralInfo;
  clinical_data?: ClinicalData;
  triage?: ExtractedTriage;
  extraction_metadata?: ExtractionMetadata;
}

export interface Patient {
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  age?: number;
  sex?: string;
  race?: string;
  ethnicity?: string;
  language?: string;
  mrn?: string;
  insurance?: { plan_name?: string; member_id?: string; group_number?: string };
  contact?: { phone?: string; address?: { street?: string; city?: string; state?: string; zip?: string } };
}

export interface ReferringProvider {
  name?: string;
  npi?: string;
  practice_name?: string;
  phone?: string;
  fax?: string;
  address?: string;
}

export interface ReferralInfo {
  receiving_specialty?: string;
  receiving_provider?: string;
  reason?: string;
  clinical_question?: string;
  urgency_stated?: string;
  date_of_referral?: string;
}

export interface ClinicalData {
  problem_list?: ProblemList;
  medications?: Medications;
  allergies?: Allergies;
  recent_labs?: LabPanel[];
  recent_vitals?: RecentVitals;
  screenings?: Screening[];
  procedures_and_surgeries?: Procedure[];
  social_history?: SocialHistory;
  immunizations_summary?: string;
}

export interface ProblemList {
  active: Condition[];
  significant_history: SignificantHistory[];
}

export interface Condition {
  diagnosis: string;
  code?: string;
  code_system?: string;
  onset_date?: string;
}

export interface SignificantHistory extends Condition {
  resolution_date?: string;
  significance_reason?: string;
}

export interface Medications {
  active: Medication[];
  recently_stopped: StoppedMedication[];
}

export interface Medication {
  name: string;
  dose?: string;
  frequency?: string;
  rxnorm?: string;
  first_prescribed?: string;
  source?: string;
}

export interface StoppedMedication {
  name: string;
  dose?: string;
  rxnorm?: string;
  stop_date?: string;
  duration_on_med?: string;
  reason_stopped?: string;
}

export interface Allergies {
  known_allergies: { substance: string; reaction?: string; severity?: string }[];
  no_known_allergies: boolean;
}

export interface LabPanel {
  panel_name?: string;
  panel_loinc?: string;
  date?: string;
  results: LabResult[];
}

export interface LabResult {
  test_name: string;
  loinc?: string;
  value?: string;
  unit?: string;
  flag?: string;
  prior_value?: string;
  prior_date?: string;
}

export interface RecentVitals {
  date?: string;
  height?: string;
  weight?: string;
  bmi?: string;
  heart_rate?: string;
  respiratory_rate?: string;
  blood_pressure?: string;
  temperature?: string;
  pain_score?: string;
  oxygen_saturation?: string;
  trends?: {
    weight_3_visits?: string[];
    bp_3_visits?: string[];
    a1c_3_visits?: string[];
  };
}

export interface Screening {
  instrument: string;
  score: string;
  interpretation?: string;
  date?: string;
  screening_type?: string;
}

export interface Procedure {
  description: string;
  code?: string;
  code_system?: string;
  date?: string;
  is_surgical?: boolean;
}

export interface SocialHistory {
  smoking_status?: string;
  alcohol_use?: string;
  substance_use?: string;
  employment?: string;
  education?: string;
  housing?: string;
  safety_concerns?: string;
  other?: string;
}

export interface ExtractedTriage {
  urgency?: TriageUrgency;
  confidence?: number;
  reasoning?: string;
  red_flags?: string[];
  missing_critical_info?: string[];
  data_quality_notes?: string[];
}

export interface ExtractionMetadata {
  extraction_path?: string;
  ocr_confidence_mean?: number;
  extraction_model?: string;
  extraction_timestamp?: string;
  sections_found?: string[];
  sections_missing?: string[];
}

export type ReferralStatus =
  | "processing"
  | "pending_review"
  | "reviewed"
  | "finalized"
  | "archived";

export type TriageUrgency =
  | "urgent"
  | "semi_urgent"
  | "routine"
  | "needs_clarification"
  | "inappropriate";

export interface UploadResponse {
  referral_id: string;
  status: string;
}

export interface CorrectionPayload {
  field_path: string;
  original_value: unknown;
  corrected_value: unknown;
  correction_type: "value_change" | "field_added" | "field_removed" | "triage_override";
  reason?: string;
}

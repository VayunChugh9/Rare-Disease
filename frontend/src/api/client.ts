/* API client for RefTriage backend */

import type {
  CorrectionPayload,
  ReferralDetail,
  ReferralListResponse,
  UploadResponse,
} from "../types/referral";

const BASE = "/api/referrals";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

export async function listReferrals(
  status?: string,
  limit = 50,
  offset = 0
): Promise<ReferralListResponse> {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  const res = await fetch(`${BASE}/?${params}`);
  return handleResponse(res);
}

export async function getReferral(id: string): Promise<ReferralDetail> {
  const res = await fetch(`${BASE}/${id}`);
  return handleResponse(res);
}

export async function getReferralStatus(
  id: string
): Promise<{ referral_id: string; status: string; triage_urgency: string }> {
  const res = await fetch(`${BASE}/${id}/status`);
  return handleResponse(res);
}

export async function uploadReferral(
  file: File,
  context?: {
    specialty?: string;
    reason?: string;
    urgency?: string;
    providerName?: string;
    providerPractice?: string;
    providerPhone?: string;
  }
): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  if (context?.specialty) form.append("referral_specialty", context.specialty);
  if (context?.reason) form.append("referral_reason", context.reason);
  if (context?.urgency) form.append("referral_urgency", context.urgency);
  if (context?.providerName)
    form.append("referring_provider_name", context.providerName);
  if (context?.providerPractice)
    form.append("referring_provider_practice", context.providerPractice);
  if (context?.providerPhone)
    form.append("referring_provider_phone", context.providerPhone);

  const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
  return handleResponse(res);
}

export async function saveCorrection(
  referralId: string,
  correction: CorrectionPayload
): Promise<{ correction_id: string; status: string }> {
  const res = await fetch(`${BASE}/${referralId}/corrections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(correction),
  });
  return handleResponse(res);
}

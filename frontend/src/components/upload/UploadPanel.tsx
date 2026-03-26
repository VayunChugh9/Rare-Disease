import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileText, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { uploadReferral } from "../../api/client";

type Phase = "idle" | "uploading" | "processing" | "done" | "error";

export function UploadPanel() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>("idle");
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const [referralId, setReferralId] = useState("");

  // Optional context fields
  const [specialty, setSpecialty] = useState("");
  const [reason, setReason] = useState("");
  const [providerName, setProviderName] = useState("");

  const handleFile = useCallback((f: File) => {
    const validTypes = [".xml", ".txt", ".pdf", ".json"];
    const ext = f.name.toLowerCase().slice(f.name.lastIndexOf("."));
    if (!validTypes.includes(ext)) {
      setError(`Unsupported file type: ${ext}. Accepted: XML, TXT, PDF`);
      return;
    }
    setFile(f);
    setError("");
  }, []);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  }

  async function handleSubmit() {
    if (!file) return;
    setPhase("uploading");
    try {
      setPhase("processing");
      const res = await uploadReferral(file, {
        specialty: specialty || undefined,
        reason: reason || undefined,
        providerName: providerName || undefined,
      });
      setReferralId(res.referral_id);
      setPhase("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setPhase("error");
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="text-lg font-semibold text-slate-800 mb-1">
        Upload Referral Document
      </h1>
      <p className="text-sm text-slate-500 mb-8">
        Upload a CCD/CCDA XML, referral letter (TXT), or PDF for AI-assisted extraction and triage.
      </p>

      {phase === "done" ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-8 text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-500 mb-3" />
          <h2 className="text-sm font-semibold text-slate-800 mb-1">
            Referral Processed
          </h2>
          <p className="text-sm text-slate-600 mb-6">
            Extraction and summarization complete. Ready for review.
          </p>
          <button
            onClick={() => navigate(`/review/${referralId}`)}
            className="rounded-lg bg-teal-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-teal-700 transition-colors"
          >
            Review Referral
          </button>
        </div>
      ) : (
        <>
          {/* Drop zone */}
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`relative rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
              dragOver
                ? "border-teal-400 bg-teal-50/50"
                : file
                ? "border-teal-300 bg-teal-50/30"
                : "border-stone-300 bg-white hover:border-stone-400"
            }`}
          >
            {file ? (
              <div className="flex items-center justify-center gap-3">
                <FileText className="h-8 w-8 text-teal-600" />
                <div className="text-left">
                  <p className="text-sm font-medium text-slate-800">
                    {file.name}
                  </p>
                  <p className="text-xs text-slate-500">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <button
                  onClick={() => { setFile(null); setPhase("idle"); }}
                  className="ml-4 text-xs text-slate-500 hover:text-slate-700 underline"
                >
                  Change
                </button>
              </div>
            ) : (
              <>
                <Upload className="mx-auto h-8 w-8 text-stone-400 mb-3" />
                <p className="text-sm text-slate-600 mb-1">
                  Drag and drop a file, or{" "}
                  <label className="cursor-pointer text-teal-600 hover:text-teal-700 font-medium">
                    browse
                    <input
                      type="file"
                      className="hidden"
                      accept=".xml,.txt,.pdf,.json"
                      onChange={(e) => {
                        if (e.target.files?.[0]) handleFile(e.target.files[0]);
                      }}
                    />
                  </label>
                </p>
                <p className="text-xs text-slate-400">
                  XML, TXT, PDF supported
                </p>
              </>
            )}
          </div>

          {error && (
            <div className="mt-3 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {/* Optional context */}
          {file && (
            <div className="mt-6 space-y-3">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                Optional referral context
              </p>
              <div className="grid grid-cols-2 gap-3">
                <input
                  placeholder="Receiving specialty (e.g., Endocrinology)"
                  value={specialty}
                  onChange={(e) => setSpecialty(e.target.value)}
                  className="rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-teal-300 focus:outline-none focus:ring-1 focus:ring-teal-300"
                />
                <input
                  placeholder="Referring provider name"
                  value={providerName}
                  onChange={(e) => setProviderName(e.target.value)}
                  className="rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-teal-300 focus:outline-none focus:ring-1 focus:ring-teal-300"
                />
              </div>
              <textarea
                placeholder="Referral reason / clinical question"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={2}
                className="w-full rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-teal-300 focus:outline-none focus:ring-1 focus:ring-teal-300 resize-none"
              />
            </div>
          )}

          {/* Submit */}
          {file && (
            <button
              onClick={handleSubmit}
              disabled={phase === "uploading" || phase === "processing"}
              className="mt-6 w-full flex items-center justify-center gap-2 rounded-lg bg-teal-600 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-teal-700 disabled:bg-stone-300 disabled:cursor-not-allowed transition-colors"
            >
              {phase === "uploading" || phase === "processing" ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {phase === "uploading"
                    ? "Uploading..."
                    : "Extracting and summarizing..."}
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  Process Referral
                </>
              )}
            </button>
          )}
        </>
      )}
    </div>
  );
}

import { useState, useCallback, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileText, Loader2, CheckCircle2, AlertCircle, Database, FileUp } from "lucide-react";
import { uploadReferral } from "../../api/client";

type Phase = "idle" | "uploading" | "processing" | "done" | "error";

const PROCESSING_STAGES = [
  { label: "Uploading documents", duration: 2000 },
  { label: "Parsing referral note", duration: 4000 },
  { label: "Extracting clinical data from CCD", duration: 5000 },
  { label: "Running AI extraction & structuring", duration: 8000 },
  { label: "Generating triage recommendation", duration: 6000 },
  { label: "Building clinical summary", duration: 4000 },
];

function FileDropZone({
  label,
  description,
  accept,
  icon: Icon,
  file,
  onFile,
}: {
  label: string;
  description: string;
  accept: string;
  icon: React.ElementType;
  file: File | null;
  onFile: (f: File) => void;
}) {
  const [dragOver, setDragOver] = useState(false);

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        if (e.dataTransfer.files[0]) onFile(e.dataTransfer.files[0]);
      }}
      className={`relative rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
        dragOver
          ? "border-teal-400 bg-teal-50/50"
          : file
          ? "border-teal-300 bg-teal-50/30"
          : "border-white/40 bg-slate-50/50 hover:border-slate-300"
      }`}
    >
      {file ? (
        <div className="flex flex-col items-center justify-center gap-2 py-2">
          <FileText className="h-8 w-8 text-teal-600" />
          <p className="text-sm font-medium text-slate-800 text-center break-all px-2">{file.name}</p>
          <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
          <button
            onClick={(e) => { e.stopPropagation(); onFile(null as unknown as File); }}
            className="text-xs text-slate-500 hover:text-slate-700 underline"
          >
            Remove
          </button>
        </div>
      ) : (
        <>
          <Icon className="mx-auto h-6 w-6 text-stone-400 mb-2" />
          <p className="text-sm font-medium text-slate-700 mb-0.5">{label}</p>
          <p className="text-xs text-slate-400 mb-2">{description}</p>
          <label className="cursor-pointer inline-flex items-center gap-1.5 text-sm text-teal-600 hover:text-teal-700 font-medium">
            <FileUp className="h-3.5 w-3.5" />
            Browse files
            <input
              type="file"
              className="hidden"
              accept={accept}
              onChange={(e) => {
                if (e.target.files?.[0]) onFile(e.target.files[0]);
              }}
            />
          </label>
        </>
      )}
    </div>
  );
}

export function UploadPanel() {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<Phase>("idle");
  const [referralNote, setReferralNote] = useState<File | null>(null);
  const [hieFile, setHieFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [referralId, setReferralId] = useState("");

  // Optional context fields
  const [specialty, setSpecialty] = useState("");
  const [reason, setReason] = useState("");
  const [providerName, setProviderName] = useState("");

  const handleNoteFile = useCallback((f: File) => {
    if (!f) { setReferralNote(null); return; }
    const validTypes = [".txt", ".pdf"];
    const ext = f.name.toLowerCase().slice(f.name.lastIndexOf("."));
    if (!validTypes.includes(ext)) {
      setError(`Referral note must be TXT or PDF. Got: ${ext}`);
      return;
    }
    setReferralNote(f);
    setError("");
  }, []);

  const handleHieFile = useCallback((f: File) => {
    if (!f) { setHieFile(null); return; }
    const ext = f.name.toLowerCase().slice(f.name.lastIndexOf("."));
    if (ext !== ".xml") {
      setError(`Patient HIE must be XML (CCD/CCDA). Got: ${ext}`);
      return;
    }
    setHieFile(f);
    setError("");
  }, []);

  const [stageIndex, setStageIndex] = useState(0);
  const stageTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const hasFiles = referralNote || hieFile;

  // Advance through processing stages for visual feedback
  useEffect(() => {
    if (phase !== "uploading" && phase !== "processing") {
      setStageIndex(0);
      return;
    }
    if (stageIndex < PROCESSING_STAGES.length - 1) {
      stageTimerRef.current = setTimeout(() => {
        setStageIndex((i) => i + 1);
      }, PROCESSING_STAGES[stageIndex].duration);
      return () => { if (stageTimerRef.current) clearTimeout(stageTimerRef.current); };
    }
  }, [phase, stageIndex]);

  async function handleSubmit() {
    if (!hasFiles) return;
    setPhase("uploading");
    setStageIndex(0);
    try {
      setPhase("processing");
      const res = await uploadReferral(
        { referralNote: referralNote ?? undefined, hieFile: hieFile ?? undefined },
        {
          specialty: specialty || undefined,
          reason: reason || undefined,
          providerName: providerName || undefined,
        }
      );
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
        Upload Referral Documents
      </h1>
      <p className="text-sm text-slate-500 mb-8">
        Upload a referral note and/or patient CCD/CCDA XML for AI-assisted extraction and triage.
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
            className="rounded-lg bg-[#0D9488] px-5 py-2.5 text-sm font-medium text-white hover:bg-teal-700 transition-colors"
          >
            Review Referral
          </button>
        </div>
      ) : (
        <>
          {/* Dual file upload zones */}
          <div className="grid grid-cols-2 gap-4 mb-4">
            <FileDropZone
              label="Referral Note"
              description="Fax, letter, or typed note (TXT, PDF)"
              accept=".txt,.pdf"
              icon={Upload}
              file={referralNote}
              onFile={handleNoteFile}
            />
            <FileDropZone
              label="Patient HIE / CCD"
              description="CCD/CCDA XML from health exchange"
              accept=".xml"
              icon={Database}
              file={hieFile}
              onFile={handleHieFile}
            />
          </div>

          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}

          {/* Optional context */}
          {hasFiles && (
            <div className="mb-4 space-y-3">
              <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
                Optional referral context
              </p>
              <div className="grid grid-cols-2 gap-3">
                <input
                  placeholder="Receiving specialty (e.g., Endocrinology)"
                  value={specialty}
                  onChange={(e) => setSpecialty(e.target.value)}
                  className="rounded-lg border border-white/40 bg-slate-50/50 px-3 py-2 text-sm placeholder:text-slate-400 focus:border-teal-300 focus:outline-none focus:ring-1 focus:ring-teal-300"
                />
                <input
                  placeholder="Referring provider name"
                  value={providerName}
                  onChange={(e) => setProviderName(e.target.value)}
                  className="rounded-lg border border-white/40 bg-slate-50/50 px-3 py-2 text-sm placeholder:text-slate-400 focus:border-teal-300 focus:outline-none focus:ring-1 focus:ring-teal-300"
                />
              </div>
              <textarea
                placeholder="Referral reason / clinical question"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={2}
                className="w-full rounded-lg border border-white/40 bg-slate-50/50 px-3 py-2 text-sm placeholder:text-slate-400 focus:border-teal-300 focus:outline-none focus:ring-1 focus:ring-teal-300 resize-none"
              />
            </div>
          )}

          {/* Submit / Progress */}
          {hasFiles && (phase === "uploading" || phase === "processing" ? (
            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <div className="flex items-center gap-3 mb-4">
                <Loader2 className="h-5 w-5 animate-spin text-[#0D9488]" />
                <span className="text-sm font-semibold text-slate-800">Processing referral...</span>
              </div>
              {/* Progress bar */}
              <div className="w-full h-2 bg-slate-100 rounded-full mb-4 overflow-hidden">
                <div
                  className="h-full bg-[#0D9488] rounded-full transition-all duration-1000 ease-out"
                  style={{ width: `${((stageIndex + 1) / PROCESSING_STAGES.length) * 100}%` }}
                />
              </div>
              {/* Stage list */}
              <div className="space-y-2">
                {PROCESSING_STAGES.map((stage, i) => (
                  <div key={i} className="flex items-center gap-2.5">
                    {i < stageIndex ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                    ) : i === stageIndex ? (
                      <Loader2 className="h-4 w-4 animate-spin text-[#0D9488] shrink-0" />
                    ) : (
                      <div className="h-4 w-4 rounded-full border-2 border-slate-200 shrink-0" />
                    )}
                    <span className={`text-sm ${
                      i < stageIndex ? "text-emerald-600" :
                      i === stageIndex ? "text-slate-800 font-medium" :
                      "text-slate-400"
                    }`}>
                      {stage.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <button
              onClick={handleSubmit}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#0D9488] py-2.5 text-sm font-medium text-white shadow-sm hover:bg-teal-700 transition-colors"
            >
              <Upload className="h-4 w-4" />
              Process Referral
            </button>
          ))}
        </>
      )}
    </div>
  );
}

import { useState, useRef, useEffect } from "react";
import { Pencil, Check, X } from "lucide-react";

interface EditableFieldProps {
  label: string;
  value: string | null | undefined;
  fieldPath: string;
  onSave: (fieldPath: string, oldValue: string, newValue: string) => void;
  multiline?: boolean;
}

export function EditableField({
  label,
  value,
  fieldPath,
  onSave,
  multiline = false,
}: EditableFieldProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value ?? "");
  const [saved, setSaved] = useState(false);
  const [wasEdited, setWasEdited] = useState(false);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const displayValue = value || "—";

  function handleSave() {
    if (draft !== (value ?? "")) {
      onSave(fieldPath, value ?? "", draft);
      setSaved(true);
      setWasEdited(true);
      setTimeout(() => setSaved(false), 2000);
    }
    setEditing(false);
  }

  function handleCancel() {
    setDraft(value ?? "");
    setEditing(false);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !multiline) handleSave();
    if (e.key === "Escape") handleCancel();
  }

  return (
    <div className={`group flex items-start gap-2 py-1.5 ${wasEdited ? "border-l-4 border-[#2563EB] pl-2" : ""}`}>
      <span className="min-w-[120px] shrink-0 text-xs font-medium text-slate-500 pt-0.5">
        {label}
      </span>
      {editing ? (
        <div className="flex flex-1 items-start gap-1.5">
          {multiline ? (
            <textarea
              ref={inputRef as React.RefObject<HTMLTextAreaElement>}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={3}
              className="flex-1 rounded border border-teal-300 bg-white px-2 py-1 text-sm text-slate-800 outline-none focus:ring-1 focus:ring-teal-400 resize-none"
            />
          ) : (
            <input
              ref={inputRef as React.RefObject<HTMLInputElement>}
              type="text"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 rounded border border-teal-300 bg-white px-2 py-1 text-sm text-slate-800 outline-none focus:ring-1 focus:ring-teal-400"
            />
          )}
          <button
            onClick={handleSave}
            className="rounded p-1 text-teal-600 hover:bg-teal-50"
          >
            <Check className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={handleCancel}
            className="rounded p-1 text-slate-400 hover:bg-stone-100"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ) : (
        <div className="flex flex-1 items-start gap-1.5">
          <span className={`flex-1 text-sm ${value ? "text-slate-800" : "text-slate-400"}`}>
            {displayValue}
          </span>
          {saved && (
            <span className="text-xs text-teal-600 font-medium">Saved</span>
          )}
          <button
            onClick={() => {
              setDraft(value ?? "");
              setEditing(true);
            }}
            className="invisible group-hover:visible rounded p-0.5 text-slate-400 hover:text-teal-600 hover:bg-teal-50 transition-colors"
            title="Edit"
          >
            <Pencil className="h-3 w-3" />
          </button>
        </div>
      )}
    </div>
  );
}

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Sparkles } from "lucide-react";

interface AISummaryPanelProps {
  summaryNarrative: string | null;
  triageReasoning: string | null;
  referralReason: string | null;
  oneLineSummary: string | null;
}

export function AISummaryPanel({
  summaryNarrative,
  triageReasoning,
  referralReason,
  oneLineSummary,
}: AISummaryPanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (
        e.key === "s" &&
        !e.ctrlKey && !e.metaKey && !e.altKey &&
        !(e.target instanceof HTMLInputElement) &&
        !(e.target instanceof HTMLTextAreaElement)
      ) {
        setIsOpen((prev) => !prev);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex w-[35%] shrink-0 sticky top-[76px] self-start" style={{ maxHeight: "calc(100vh - 92px)" }}>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.aside
            key="panel"
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: "100%", opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            className="overflow-hidden shrink-0"
          >
            <div className="glass rounded-2xl p-6 m-2 mr-0 overflow-y-auto" style={{ maxHeight: "calc(100vh - 108px)" }}>
              <div className="flex items-center gap-2 mb-6">
                <Sparkles className="h-4 w-4 text-[#0D9488]" />
                <h2 className="section-label text-[#0F172A]">AI-Generated Summary</h2>
                <span className="ml-auto text-[10px] text-[#64748B] bg-slate-100 rounded px-1.5 py-0.5">
                  Review before finalizing
                </span>
              </div>

              {summaryNarrative && (
                <div className="space-y-3 text-sm leading-relaxed text-[#64748B] mb-6">
                  {summaryNarrative.split("\n\n").map((para, i) => (
                    <p key={i}>{para}</p>
                  ))}
                </div>
              )}

              {triageReasoning && (
                <div className="border-l-4 border-[#0D9488] pl-4 py-1 mb-6">
                  <span className="section-label text-[#0D9488] block mb-1">Triage Reasoning</span>
                  <p className="text-xs italic text-[#64748B]">{triageReasoning}</p>
                </div>
              )}

              {oneLineSummary && (
                <div className="pt-4 border-t border-[#0D9488]/10">
                  <p className="text-[11px] italic text-slate-400">{oneLineSummary}</p>
                </div>
              )}
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center justify-center w-6 shrink-0 hover:bg-slate-100 transition-colors cursor-pointer group"
        title={isOpen ? "Collapse AI Summary (S)" : "Expand AI Summary (S)"}
      >
        <div className="flex flex-col items-center gap-1">
          {isOpen ? (
            <ChevronLeft className="h-4 w-4 text-[#64748B] group-hover:text-[#0D9488]" />
          ) : (
            <ChevronRight className="h-4 w-4 text-[#64748B] group-hover:text-[#0D9488]" />
          )}
          {!isOpen && (
            <span
              className="text-[10px] font-bold uppercase tracking-widest text-[#64748B] group-hover:text-[#0D9488]"
              style={{ writingMode: "vertical-rl", textOrientation: "mixed" }}
            >
              AI Summary
            </span>
          )}
        </div>
      </button>
    </div>
  );
}

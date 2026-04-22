"use client";

import Window from "@/components/shared/Window";
import { useCommandLog } from "@/contexts/CommandLogContext";
import { GraduationCap, Zap, FileText, Download } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";

export default function LectureNotes() {
  const { addLog } = useCommandLog();
  const [step, setStep] = useState(0); // 0 = idle, 1 = fetching, 2 = AI processing, 3 = ready
  const [url, setUrl] = useState("");
  const [notes, setNotes] = useState("");

  const handleGenerate = async () => {
    if (!url) return alert("Please enter a YouTube URL");
    setStep(1);
    addLog("🎓 Lecture Notes", "Generate Notes", "Process started");
    
    try {
      const res = await fetch("http://localhost:8000/api/lecture-notes/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
      });
      setStep(2);
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Generation failed");

      if (data.status === "skipped") {
        alert(data.message);
        setStep(0);
        return;
      }

      setNotes(data.notes);
      setStep(3);
      addLog("🎓 Lecture Notes", "Generate Notes", "Notes Ready ✅");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Generation failed";
      addLog("🎓 Lecture Notes", "Error", message);
      alert(message);
      setStep(0);
    }
  };

  return (
    <Window id="lectureNotes" title="Lecture Notes" icon={<GraduationCap className="w-4 h-4 text-[var(--neon-pink)]" />} defaultPosition={{ x: 300, y: 60 }}>
      <div className="flex flex-col h-full">
        {/* Top Input Area */}
        <div className="p-4 flex gap-3 border-b border-[rgba(192,132,252,0.2)]">
          <input
            type="text"
            placeholder="Paste YouTube URL..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="flex-1 bg-white/5 border-b border-[rgba(192,132,252,0.3)] focus:border-[var(--neon-purple)] outline-none px-3 py-2 rounded-t-md text-sm transition-all"
          />
          <button
            onClick={handleGenerate}
            disabled={step !== 0 && step !== 3}
            className="bg-[var(--neon-purple)]/20 border border-[var(--neon-purple)] text-[var(--neon-purple)] hover:bg-[var(--neon-purple)]/40 hover:shadow-[0_0_15px_rgba(192,132,252,0.4)] px-4 py-2 rounded-md font-semibold transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {step === 0 ? "Generate Notes" : step < 3 ? "Processing..." : "Regenerate"} <Zap className="w-4 h-4" />
          </button>
        </div>

        {/* Stepper Area */}
        <div className="flex justify-between px-8 py-4 bg-black/10 border-b border-[rgba(192,132,252,0.2)]">
          <Step label="Fetching" active={step >= 1} />
          <Step label="AI Processing" active={step >= 2} />
          <Step label="Ready" active={step >= 3} />
        </div>

        {/* Notes Content */}
        <div className="flex-1 overflow-y-auto p-6 leading-relaxed">
          {step === 3 ? (
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-500 whitespace-pre-wrap text-sm text-[var(--color-text-dim)]">
              {notes}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-white/20 font-orbitron">
              {step > 0 ? (
                <div className="flex flex-col items-center gap-4">
                  <div className="w-12 h-12 border-4 border-[var(--neon-purple)] border-t-transparent rounded-full animate-spin" />
                  <span>{step === 1 ? "FETCHING TRANSCRIPT..." : "AI ANALYZING..."}</span>
                </div>
              ) : "AWAITING INPUT"}
            </div>
          )}
        </div>

        {/* Bottom Actions */}
        <div className="p-4 bg-black/20 flex gap-3">
          <button className="flex-1 flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-[var(--neon-pink)]/50 text-[var(--neon-pink)] py-2 rounded-md hover:shadow-[0_0_15px_rgba(244,114,182,0.3)] transition-all font-semibold">
            <FileText className="w-4 h-4" /> Download MD
          </button>
          <button className="flex-1 flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 border border-[var(--neon-pink)]/50 text-[var(--neon-pink)] py-2 rounded-md hover:shadow-[0_0_15px_rgba(244,114,182,0.3)] transition-all font-semibold">
            <Download className="w-4 h-4" /> Download PDF
          </button>
        </div>
      </div>
    </Window>
  );
}

function Step({ label, active }: { label: string; active: boolean }) {
  return (
    <div className={clsx("flex flex-col items-center gap-2 transition-all duration-300", active ? "opacity-100 text-[var(--neon-pink)] drop-shadow-[0_0_8px_var(--neon-pink)]" : "opacity-40")}>
      <div className="w-3 h-3 rounded-full bg-current" />
      <span className="text-xs uppercase font-semibold tracking-wider">{label}</span>
    </div>
  );
}

"use client";
import { useWindows } from "@/contexts/WindowContext";
import { Monitor } from "lucide-react";

export default function ExamPilot() {
  const { windows, closeWindow, toggleMinimize, focusWindow } = useWindows();
  const win = windows["examPilot"];
  if (!win?.isOpen || win.isMinimized) return null;

  return (
    <div className="fixed top-24 left-60 w-[500px] rounded-2xl border border-[rgba(250,204,21,0.3)] bg-[rgba(15,12,0,0.92)] backdrop-blur-2xl shadow-[0_0_60px_rgba(250,204,21,0.08)] overflow-hidden"
      style={{ zIndex: win.zIndex }} onMouseDown={() => focusWindow("examPilot")}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(250,204,21,0.15)] bg-[rgba(250,204,21,0.04)]">
        <div className="flex items-center gap-2">
          <Monitor className="w-4 h-4 text-[#facc15]" />
          <span className="font-orbitron text-sm text-[#facc15]">EXAM PILOT</span>
        </div>
        <div className="flex gap-2">
          <button onClick={() => toggleMinimize("examPilot")} className="w-3 h-3 rounded-full bg-yellow-400" />
          <button onClick={() => closeWindow("examPilot")} className="w-3 h-3 rounded-full bg-red-500" />
        </div>
      </div>
      <div className="p-6 space-y-5">
        <div className="flex gap-4 items-start">
          <div className="w-12 h-12 rounded-xl bg-[rgba(250,204,21,0.1)] border border-[rgba(250,204,21,0.2)] flex items-center justify-center shrink-0">
            <Monitor className="w-6 h-6 text-[#facc15]" />
          </div>
          <div>
            <h2 className="font-orbitron text-base text-white mb-1">Desktop-Only Feature</h2>
            <p className="text-sm text-white/50 leading-relaxed">
              Exam Pilot uses screen capture and OCR to read quiz questions and auto-solve them in real-time.
              This requires direct desktop access and cannot run in the browser.
            </p>
          </div>
        </div>

        <div className="rounded-xl bg-[rgba(250,204,21,0.06)] border border-[rgba(250,204,21,0.15)] p-4 space-y-2">
          <p className="text-xs text-[#facc15] uppercase tracking-widest font-semibold">How to use</p>
          <ol className="text-sm text-white/60 space-y-1 list-decimal list-inside">
            <li>Open a terminal in your project folder</li>
            <li>Run the command below</li>
            <li>Navigate to your quiz / exam page</li>
            <li>ALOA will auto-detect and solve questions</li>
          </ol>
        </div>

        <div className="rounded-xl bg-black/40 border border-white/10 p-3 font-mono text-sm text-[#facc15]">
          <span className="text-white/30">$ </span>python main.py
          <br />
          <span className="text-white/30"># Select option: </span>5
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs">
          {[
            { label: "Tesseract OCR", desc: "Text extraction from screen" },
            { label: "Gemini Vision", desc: "AI answer generation" },
            { label: "Auto-click", desc: "Selects the correct option" },
            { label: "Key rotation", desc: "3-key fallback for rate limits" },
          ].map(f => (
            <div key={f.label} className="rounded-xl bg-white/5 border border-white/10 p-3">
              <p className="text-[#facc15] font-semibold">{f.label}</p>
              <p className="text-white/40 mt-0.5">{f.desc}</p>
            </div>
          ))}
        </div>

        <p className="text-xs text-white/30 text-center">
          Required: Tesseract OCR installed at C:\Program Files\Tesseract-OCR\
        </p>
      </div>
    </div>
  );
}

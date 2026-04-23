"use client";

import { useState, useRef, useEffect } from "react";
import { useWindows } from "@/contexts/WindowContext";
import { Bug, Send, CheckCircle, Loader2, FileCode } from "lucide-react";
import clsx from "clsx";

const API = "http://localhost:8000";

interface Message {
  role: "user" | "assistant";
  content: string;
  hasFix?: boolean;
  fixFile?: string;
}

export default function CodeHealer() {
  const { windows, closeWindow, toggleMinimize, focusWindow } = useWindows();
  const win = windows["codeHealer"];
  const [folderPath, setFolderPath] = useState("");
  const [sessionActive, setSessionActive] = useState(false);
  const [projectInfo, setProjectInfo] = useState<{ project_type: string; run_command: string; file_count: number } | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  if (!win?.isOpen || win.isMinimized) return null;

  async function handleInit() {
    if (!folderPath.trim()) return;
    setLoading(true);
    setStatus("Scanning project...");
    try {
      const r = await fetch(`${API}/api/code-healer/init`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: folderPath }),
      });
      const d = await r.json();
      if (d.status === "success") {
        setProjectInfo({ project_type: d.project_type, run_command: d.run_command, file_count: d.file_count });
        setSessionActive(true);
        setMessages([{ role: "assistant", content: `✅ Project loaded: **${d.project_type}** — ${d.file_count} source files found.\nRun command: \`${d.run_command}\`\n\nAsk me anything about your code, paste an error, or say "run" to test it.` }]);
        setStatus("");
      } else {
        setStatus(`❌ ${d.detail || "Failed to init"}`);
      }
    } catch {
      setStatus("❌ Cannot connect to backend.");
    }
    setLoading(false);
  }

  async function handleSend() {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages(p => [...p, { role: "user", content: userMsg }]);
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/code-healer/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: folderPath, message: userMsg }),
      });
      const d = await r.json();
      setMessages(p => [...p, {
        role: "assistant",
        content: d.response || d.detail || "No response",
        hasFix: d.has_fix,
        fixFile: d.fix_file,
      }]);
    } catch (e) {
      setMessages(p => [...p, { role: "assistant", content: "❌ Backend error." }]);
      console.error(e);
    }
    setLoading(false);
  }

  async function handleApplyFix() {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/code-healer/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: folderPath }),
      });
      const d = await r.json();
      setMessages(p => [...p, { role: "assistant", content: d.message }]);
    } catch (e) {
      setMessages(p => [...p, { role: "assistant", content: "❌ Failed to apply fix." }]);
      console.error(e);
    }
    setLoading(false);
  }


  return (
    <div
      className="fixed top-16 left-40 w-[700px] h-[520px] rounded-2xl border border-[rgba(132,204,252,0.3)] bg-[rgba(5,10,20,0.92)] backdrop-blur-2xl shadow-[0_0_60px_rgba(56,189,248,0.15)] flex flex-col overflow-hidden"
      style={{ zIndex: win.zIndex }}
      onMouseDown={() => focusWindow("codeHealer")}
    >
      {/* Title bar */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(132,204,252,0.15)] bg-[rgba(56,189,248,0.05)]">
        <div className="flex items-center gap-2">
          <Bug className="w-4 h-4 text-[#38bdf8]" />
          <span className="font-orbitron text-sm text-[#38bdf8]">CODE HEALER</span>
          {projectInfo && <span className="text-xs text-white/40 font-mono">[{projectInfo.project_type}]</span>}
        </div>
        <div className="flex gap-2">
          <button onClick={() => toggleMinimize("codeHealer")} className="w-3 h-3 rounded-full bg-yellow-400 hover:bg-yellow-300" />
          <button onClick={() => closeWindow("codeHealer")} className="w-3 h-3 rounded-full bg-red-500 hover:bg-red-400" />
        </div>
      </div>

      {!sessionActive ? (
        /* Init screen */
        <div className="flex-1 flex flex-col items-center justify-center gap-6 p-8">
          <div className="w-16 h-16 rounded-2xl bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.3)] flex items-center justify-center">
            <FileCode className="w-8 h-8 text-[#38bdf8]" />
          </div>
          <div className="text-center">
            <h2 className="font-orbitron text-lg text-white mb-1">Code Healer</h2>
            <p className="text-sm text-white/40">AI-powered project debugger. Paste a folder path to begin.</p>
          </div>
          <div className="w-full max-w-md flex gap-2">
            <input
              value={folderPath}
              onChange={e => setFolderPath(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleInit()}
              placeholder="C:\path\to\your\project"
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-white/20 focus:outline-none focus:border-[#38bdf8]/50"
            />
            <button
              onClick={handleInit}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-[#38bdf8]/10 border border-[#38bdf8]/30 text-[#38bdf8] text-sm hover:bg-[#38bdf8]/20 transition-all disabled:opacity-40"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Scan"}
            </button>
          </div>
          {status && <p className="text-xs text-red-400">{status}</p>}
        </div>
      ) : (
        /* Chat screen */
        <>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-xs">
            {messages.map((m, i) => (
              <div key={i} className={clsx("rounded-xl px-4 py-3 max-w-[90%] whitespace-pre-wrap", m.role === "user"
                ? "ml-auto bg-[rgba(56,189,248,0.1)] border border-[rgba(56,189,248,0.2)] text-white"
                : "bg-white/5 border border-white/10 text-white/80")}>
                {m.content}
                {m.hasFix && (
                  <button onClick={handleApplyFix}
                    className="mt-2 flex items-center gap-1 text-green-400 hover:text-green-300 text-xs">
                    <CheckCircle className="w-3 h-3" /> Apply fix to {m.fixFile}
                  </button>
                )}
              </div>
            ))}
            {loading && <div className="text-white/30 animate-pulse">ALOA is thinking...</div>}
            <div ref={endRef} />
          </div>
          <div className="flex gap-2 p-3 border-t border-white/10">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSend()}
              placeholder="Paste error or ask about your code..."
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-white placeholder-white/20 focus:outline-none focus:border-[#38bdf8]/40"
            />
            <button onClick={handleSend} disabled={loading}
              className="px-3 py-2 rounded-xl bg-[#38bdf8]/10 border border-[#38bdf8]/30 hover:bg-[#38bdf8]/20 transition-all disabled:opacity-40">
              <Send className="w-4 h-4 text-[#38bdf8]" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}

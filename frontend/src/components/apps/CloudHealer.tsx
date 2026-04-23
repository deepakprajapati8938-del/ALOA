"use client";
import { useState, useRef, useEffect } from "react";
import { useWindows } from "@/contexts/WindowContext";
import { Cloud, GitBranch, Send, CheckCircle, Loader2, Upload } from "lucide-react";
import clsx from "clsx";

const API = "http://localhost:8000";
interface Message { role: "user"|"assistant"; content: string; hasChanges?: boolean; pendingFile?: string; }

export default function CloudHealer() {
  const { windows, closeWindow, toggleMinimize, focusWindow } = useWindows();
  const win = windows["cloudHealer"];
  const [repoUrl, setRepoUrl] = useState("");
  const [pat, setPat] = useState("");
  const [sessionActive, setSessionActive] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  if (!win?.isOpen || win.isMinimized) return null;

  async function handleClone() {
    if (!repoUrl.trim() || !pat.trim()) return;
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/cloud-healer/clone`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl, pat }),
      });
      const d = await r.json();
      if (d.status === "success") {
        setSessionActive(true);
        setMessages([{ role: "assistant", content: `✅ Cloned — ${d.file_count} files.\n\nDescribe the issue or paste an error.` }]);
      } else { setMessages([{ role: "assistant", content: `❌ ${d.detail}` }]); }
    } catch (e) { setMessages([{ role: "assistant", content: "❌ Cannot reach backend." }]); console.error(e); }
    setLoading(false);
  }

  async function handleSend() {
    if (!input.trim() || loading) return;
    const msg = input.trim(); setInput("");
    setMessages(p => [...p, { role: "user", content: msg }]);
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/cloud-healer/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      const d = await r.json();
      setMessages(p => [...p, { role: "assistant", content: d.response, hasChanges: d.has_changes, pendingFile: d.pending_file }]);
    } catch (e) { setMessages(p => [...p, { role: "assistant", content: "❌ Error." }]); console.error(e); }
    setLoading(false);
  }

  async function handleApply() {
    setLoading(true);
    const r = await fetch(`${API}/api/cloud-healer/apply`, { method: "POST" });
    const d = await r.json();
    setMessages(p => [...p, { role: "assistant", content: d.message }]);
    setLoading(false);
  }

  async function handlePush() {
    setLoading(true);
    const r = await fetch(`${API}/api/cloud-healer/push`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ commit_message: "ALOA Cloud Healer: Applied fixes" }),
    });
    const d = await r.json();
    setMessages(p => [...p, { role: "assistant", content: d.message }]);
    setLoading(false);
  }

  return (
    <div className="fixed top-20 left-56 w-[660px] h-[480px] rounded-2xl border border-[rgba(52,211,153,0.3)] bg-[rgba(5,15,10,0.92)] backdrop-blur-2xl shadow-[0_0_60px_rgba(52,211,153,0.1)] flex flex-col overflow-hidden"
      style={{ zIndex: win.zIndex }} onMouseDown={() => focusWindow("cloudHealer")}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(52,211,153,0.15)] bg-[rgba(52,211,153,0.05)]">
        <div className="flex items-center gap-2">
          <Cloud className="w-4 h-4 text-[#34d399]" />
          <span className="font-orbitron text-sm text-[#34d399]">CLOUD HEALER</span>
        </div>
        <div className="flex gap-2">
          <button onClick={() => toggleMinimize("cloudHealer")} className="w-3 h-3 rounded-full bg-yellow-400" />
          <button onClick={() => closeWindow("cloudHealer")} className="w-3 h-3 rounded-full bg-red-500" />
        </div>
      </div>
      {!sessionActive ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-5 p-8">
          <GitBranch className="w-12 h-12 text-[#34d399]/50" />
          <h2 className="font-orbitron text-lg text-white">Cloud Healer</h2>
          <p className="text-sm text-white/40 text-center">Debug any GitHub repo with AI — no local setup required.</p>
          <div className="w-full max-w-md space-y-3">
            <input value={repoUrl} onChange={e => setRepoUrl(e.target.value)} placeholder="https://github.com/user/repo"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-white/20 focus:outline-none focus:border-[#34d399]/40" />
            <input value={pat} onChange={e => setPat(e.target.value)} type="password" placeholder="GitHub Personal Access Token"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-white/20 focus:outline-none focus:border-[#34d399]/40" />
            <button onClick={handleClone} disabled={loading}
              className="w-full py-2 rounded-xl bg-[#34d399]/10 border border-[#34d399]/30 text-[#34d399] text-sm hover:bg-[#34d399]/20 disabled:opacity-40 flex items-center justify-center gap-2">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><GitBranch className="w-4 h-4" /> Clone & Analyze</>}
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 font-mono text-xs">
            {messages.map((m, i) => (
              <div key={i} className={clsx("rounded-xl px-4 py-3 max-w-[90%] whitespace-pre-wrap",
                m.role === "user" ? "ml-auto bg-[rgba(52,211,153,0.1)] border border-[rgba(52,211,153,0.2)] text-white"
                  : "bg-white/5 border border-white/10 text-white/80")}>
                {m.content}
                {m.hasChanges && (
                  <button onClick={handleApply} className="mt-2 flex items-center gap-1 text-green-400 text-xs hover:text-green-300">
                    <CheckCircle className="w-3 h-3" /> Apply to {m.pendingFile}
                  </button>
                )}
              </div>
            ))}
            {loading && <div className="text-white/30 animate-pulse">AI analyzing...</div>}
            <div ref={endRef} />
          </div>
          <div className="flex gap-2 p-3 border-t border-white/10">
            <button onClick={handlePush} disabled={loading}
              className="px-3 py-2 rounded-xl bg-green-900/30 border border-green-500/30 text-green-400 text-xs hover:bg-green-900/50 disabled:opacity-40 flex items-center gap-1">
              <Upload className="w-3 h-3" /> Push
            </button>
            <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && handleSend()}
              placeholder="Describe bug or paste error..."
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-xs text-white placeholder-white/20 focus:outline-none focus:border-[#34d399]/40" />
            <button onClick={handleSend} disabled={loading}
              className="px-3 py-2 rounded-xl bg-[#34d399]/10 border border-[#34d399]/30 hover:bg-[#34d399]/20 disabled:opacity-40">
              <Send className="w-4 h-4 text-[#34d399]" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}

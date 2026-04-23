"use client";
import { useState } from "react";
import { useWindows } from "@/contexts/WindowContext";
import { FileText, Sparkles, BarChart3, Loader2, CheckCircle } from "lucide-react";
import clsx from "clsx";

const API = "http://localhost:8000";
type Tab = "extract" | "generate" | "analyze";

export default function ResumeEngine() {
  const { windows, closeWindow, toggleMinimize, focusWindow } = useWindows();
  const win = windows["resumeEngine"];
  const [tab, setTab] = useState<Tab>("extract");
  const [rawText, setRawText] = useState("");
  const [profile, setProfile] = useState<Record<string, unknown> | null>(null);
  const [template, setTemplate] = useState("ats_classic");
  const [html, setHtml] = useState("");
  const [jd, setJd] = useState("");
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  if (!win?.isOpen || win.isMinimized) return null;

  async function handleExtract() {
    if (!rawText.trim()) return;
    setLoading(true); setMsg("");
    try {
      const r = await fetch(`${API}/api/resume/extract`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw_text: rawText }),
      });
      const d = await r.json();
      if (d.status === "success") { setProfile(d.profile); setMsg("✅ Profile extracted!"); setTab("generate"); }
      else setMsg(`❌ ${d.detail}`);
    } catch (e) { setMsg("❌ Backend error."); console.error(e); }
    setLoading(false);
  }

  async function handleGenerate() {
    if (!profile) return;
    setLoading(true); setMsg("");
    try {
      const r = await fetch(`${API}/api/resume/generate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, template }),
      });
      const d = await r.json();
      if (d.status === "success") { setHtml(d.html); setMsg("✅ Resume generated!"); }
      else setMsg(`❌ ${d.detail}`);
    } catch (e) { setMsg("❌ Backend error."); console.error(e); }
    setLoading(false);
  }

  async function handleAnalyze() {
    if (!profile || !jd.trim()) return;
    setLoading(true); setMsg("");
    try {
      const r = await fetch(`${API}/api/resume/analyze`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile, job_description: jd }),
      });
      const d = await r.json();
      if (d.status === "success") { setAnalysis(d.analysis); setMsg("✅ ATS analysis complete!"); }
      else setMsg(`❌ ${d.detail}`);
    } catch (e) { setMsg("❌ Backend error."); console.error(e); }
    setLoading(false);
  }

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "extract", label: "Extract", icon: <Sparkles className="w-3.5 h-3.5" /> },
    { id: "generate", label: "Generate", icon: <FileText className="w-3.5 h-3.5" /> },
    { id: "analyze", label: "ATS Score", icon: <BarChart3 className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="fixed top-20 left-36 w-[680px] h-[520px] rounded-2xl border border-[rgba(167,139,250,0.3)] bg-[rgba(10,5,20,0.92)] backdrop-blur-2xl shadow-[0_0_60px_rgba(167,139,250,0.1)] flex flex-col overflow-hidden"
      style={{ zIndex: win.zIndex }} onMouseDown={() => focusWindow("resumeEngine")}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(167,139,250,0.15)] bg-[rgba(167,139,250,0.05)]">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-[#a78bfa]" />
          <span className="font-orbitron text-sm text-[#a78bfa]">RESUME ENGINE</span>
        </div>
        <div className="flex gap-2">
          <button onClick={() => toggleMinimize("resumeEngine")} className="w-3 h-3 rounded-full bg-yellow-400" />
          <button onClick={() => closeWindow("resumeEngine")} className="w-3 h-3 rounded-full bg-red-500" />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-white/10 px-4">
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={clsx("flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold border-b-2 -mb-px transition-colors",
              tab === t.id ? "border-[#a78bfa] text-[#a78bfa]" : "border-transparent text-white/30 hover:text-white/60")}>
            {t.icon}{t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-5">
        {tab === "extract" && (
          <div className="space-y-3 h-full flex flex-col">
            <p className="text-xs text-white/40">Paste your LinkedIn bio, old resume, or career summary. AI will extract a structured profile.</p>
            <textarea value={rawText} onChange={e => setRawText(e.target.value)}
              placeholder="John Doe, Senior Software Engineer with 5 years experience in React, Node.js..."
              className="flex-1 w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none focus:border-[#a78bfa]/40 resize-none" rows={10} />
            <button onClick={handleExtract} disabled={loading}
              className="py-2.5 rounded-xl bg-[#a78bfa]/10 border border-[#a78bfa]/30 text-[#a78bfa] text-sm hover:bg-[#a78bfa]/20 disabled:opacity-40 flex items-center justify-center gap-2">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Sparkles className="w-4 h-4" /> Extract Profile</>}
            </button>
            {msg && <p className="text-xs text-center text-white/60">{msg}</p>}
          </div>
        )}

        {tab === "generate" && (
          <div className="space-y-4">
            {!profile && <p className="text-sm text-white/40">← Go to Extract tab first to build your profile.</p>}
            {profile && (
              <>
                <div className="rounded-xl bg-green-950/30 border border-green-500/20 px-4 py-2 text-xs text-green-400 flex items-center gap-2">
                  <CheckCircle className="w-3 h-3" /> Profile loaded: {(profile as { personal?: { full_name?: string } }).personal?.full_name || "Unknown"}
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-white/40 uppercase tracking-widest">Template</label>
                  <select value={template} onChange={e => setTemplate(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white focus:outline-none">
                    <option value="ats_classic">ATS Classic</option>
                    <option value="modern_professional">Modern Professional</option>
                    <option value="creative_twocolumn">Creative Two-Column</option>
                  </select>
                </div>
                <button onClick={handleGenerate} disabled={loading}
                  className="w-full py-2.5 rounded-xl bg-[#a78bfa]/10 border border-[#a78bfa]/30 text-[#a78bfa] text-sm hover:bg-[#a78bfa]/20 disabled:opacity-40 flex items-center justify-center gap-2">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><FileText className="w-4 h-4" /> Generate Resume</>}
                </button>
                {html && (
                  <div className="space-y-2">
                    <p className="text-xs text-green-400">✅ Resume generated! Preview below.</p>
                    <iframe srcDoc={html} className="w-full h-56 rounded-xl border border-white/10 bg-white" title="Resume Preview" />
                  </div>
                )}
                {msg && <p className="text-xs text-white/60">{msg}</p>}
              </>
            )}
          </div>
        )}

        {tab === "analyze" && (
          <div className="space-y-3">
            {!profile && <p className="text-sm text-white/40">← Extract your profile first.</p>}
            {profile && (
              <>
                <p className="text-xs text-white/40">Paste a job description to get your ATS match score and recommendations.</p>
                <textarea value={jd} onChange={e => setJd(e.target.value)}
                  placeholder="We are looking for a Senior React Developer with experience in TypeScript, Node.js..."
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/20 focus:outline-none resize-none" rows={5} />
                <button onClick={handleAnalyze} disabled={loading}
                  className="w-full py-2.5 rounded-xl bg-[#a78bfa]/10 border border-[#a78bfa]/30 text-[#a78bfa] text-sm hover:bg-[#a78bfa]/20 disabled:opacity-40 flex items-center justify-center gap-2">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><BarChart3 className="w-4 h-4" /> Analyze ATS Score</>}
                </button>
                {analysis && (
                  <div className="rounded-xl bg-white/5 border border-white/10 p-4 space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="text-4xl font-orbitron text-[#a78bfa]">{(analysis as { score?: number }).score ?? "–"}</div>
                      <div>
                        <div className="text-sm text-white font-semibold">ATS Score</div>
                        <div className="text-xs text-white/40">out of 100</div>
                      </div>
                    </div>
                    {((analysis as { recommendations?: string[] }).recommendations ?? []).length > 0 && (
                      <div>
                        <p className="text-xs text-white/40 mb-1 uppercase tracking-widest">Recommendations</p>
                        <ul className="space-y-1">
                          {((analysis as { recommendations?: string[] }).recommendations ?? []).slice(0, 5).map((r, i) => (
                            <li key={i} className="text-xs text-white/70">• {r}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
                {msg && <p className="text-xs text-white/60">{msg}</p>}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

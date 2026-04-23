"use client";
import { useState } from "react";
import { useWindows } from "@/contexts/WindowContext";
import { Rocket, CheckCircle, XCircle, Loader2, ExternalLink } from "lucide-react";
import clsx from "clsx";

const API = "http://localhost:8000";

interface DeployResult { platform: string; success: boolean; url: string; message: string; error: string; }
interface Plan { framework_display: string; deploy_target: string; build_command: string; start_command: string; project_name: string; }

export default function AutoDeployer() {
  const { windows, closeWindow, toggleMinimize, focusWindow } = useWindows();
  const win = windows["autoDeployer"];
  const [folderPath, setFolderPath] = useState("");
  const [githubPat, setGithubPat] = useState("");
  const [vercelToken, setVercelToken] = useState("");
  const [renderKey, setRenderKey] = useState("");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [results, setResults] = useState<DeployResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<"idle"|"planned"|"done">("idle");

  if (!win?.isOpen || win.isMinimized) return null;

  async function handleAnalyze() {
    if (!folderPath.trim()) return;
    setLoading(true); setPlan(null); setResults([]);
    try {
      const r = await fetch(`${API}/api/deployer/analyze`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: folderPath }),
      });
      const d = await r.json();
      if (d.status === "success") { setPlan(d); setStep("planned"); }
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function handleDeploy() {
    if (!plan || !githubPat.trim()) return;
    setLoading(true); setResults([]);
    try {
      const r = await fetch(`${API}/api/deployer/deploy`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          folder_path: folderPath, github_pat: githubPat,
          vercel_token: vercelToken, render_api_key: renderKey,
        }),
      });
      const d = await r.json();
      setResults(d.results || []);
      setStep("done");
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  return (
    <div className="fixed top-24 left-48 w-[620px] h-[500px] rounded-2xl border border-[rgba(251,146,60,0.3)] bg-[rgba(15,10,5,0.92)] backdrop-blur-2xl shadow-[0_0_60px_rgba(251,146,60,0.1)] flex flex-col overflow-hidden"
      style={{ zIndex: win.zIndex }} onMouseDown={() => focusWindow("autoDeployer")}>
      <div className="flex items-center justify-between px-4 py-3 border-b border-[rgba(251,146,60,0.15)] bg-[rgba(251,146,60,0.05)]">
        <div className="flex items-center gap-2">
          <Rocket className="w-4 h-4 text-[#fb923c]" />
          <span className="font-orbitron text-sm text-[#fb923c]">AUTO DEPLOYER</span>
        </div>
        <div className="flex gap-2">
          <button onClick={() => toggleMinimize("autoDeployer")} className="w-3 h-3 rounded-full bg-yellow-400" />
          <button onClick={() => closeWindow("autoDeployer")} className="w-3 h-3 rounded-full bg-red-500" />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {/* Step 1: Path */}
        <div className="space-y-2">
          <label className="text-xs text-white/40 uppercase tracking-widest">Project Folder</label>
          <div className="flex gap-2">
            <input value={folderPath} onChange={e => setFolderPath(e.target.value)}
              placeholder="C:\path\to\project"
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-white/20 focus:outline-none focus:border-[#fb923c]/40" />
            <button onClick={handleAnalyze} disabled={loading}
              className="px-4 py-2 rounded-xl bg-[#fb923c]/10 border border-[#fb923c]/30 text-[#fb923c] text-sm hover:bg-[#fb923c]/20 disabled:opacity-40">
              {loading && step === "idle" ? <Loader2 className="w-4 h-4 animate-spin" /> : "Analyze"}
            </button>
          </div>
        </div>

        {/* Detected plan */}
        {plan && (
          <div className="rounded-xl bg-white/5 border border-white/10 p-4 space-y-2 text-sm">
            <p className="text-[#fb923c] font-semibold">{plan.framework_display}</p>
            <div className="grid grid-cols-2 gap-2 text-xs text-white/60">
              <span>Deploy target: <span className="text-white">{plan.deploy_target}</span></span>
              <span>Project: <span className="text-white">{plan.project_name}</span></span>
              <span className="col-span-2">Build: <span className="text-white font-mono">{plan.build_command}</span></span>
              <span className="col-span-2">Start: <span className="text-white font-mono">{plan.start_command}</span></span>
            </div>
          </div>
        )}

        {/* Step 2: Tokens */}
        {plan && (
          <div className="space-y-2">
            <label className="text-xs text-white/40 uppercase tracking-widest">Credentials</label>
            <input value={githubPat} onChange={e => setGithubPat(e.target.value)} type="password"
              placeholder="GitHub Personal Access Token (required)"
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-white/20 focus:outline-none focus:border-[#fb923c]/40" />
            {(plan.deploy_target === "vercel" || plan.deploy_target === "both") && (
              <input value={vercelToken} onChange={e => setVercelToken(e.target.value)} type="password"
                placeholder="Vercel Token (optional)"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-white/20 focus:outline-none" />
            )}
            {(plan.deploy_target === "render" || plan.deploy_target === "both") && (
              <input value={renderKey} onChange={e => setRenderKey(e.target.value)} type="password"
                placeholder="Render API Key (optional)"
                className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-white placeholder-white/20 focus:outline-none" />
            )}
            <button onClick={handleDeploy} disabled={loading || !githubPat.trim()}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-[#fb923c]/20 to-[#f97316]/20 border border-[#fb923c]/40 text-[#fb923c] font-semibold text-sm hover:from-[#fb923c]/30 hover:to-[#f97316]/30 disabled:opacity-40 flex items-center justify-center gap-2 transition-all">
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Deploying...</> : <><Rocket className="w-4 h-4" /> Deploy Now</>}
            </button>
          </div>
        )}

        {/* Results */}
        {results.length > 0 && (
          <div className="space-y-2">
            <label className="text-xs text-white/40 uppercase tracking-widest">Results</label>
            {results.map((r, i) => (
              <div key={i} className={clsx("rounded-xl px-4 py-3 flex items-center justify-between text-sm border",
                r.success ? "bg-green-950/30 border-green-500/30" : "bg-red-950/30 border-red-500/30")}>
                <div className="flex items-center gap-2">
                  {r.success ? <CheckCircle className="w-4 h-4 text-green-400" /> : <XCircle className="w-4 h-4 text-red-400" />}
                  <span className="capitalize text-white/80">{r.platform}</span>
                  <span className="text-xs text-white/40">{r.message}</span>
                </div>
                {r.url && <a href={r.url} target="_blank" rel="noreferrer" className="text-[#fb923c] hover:text-[#fb923c]/70">
                  <ExternalLink className="w-3 h-3" />
                </a>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

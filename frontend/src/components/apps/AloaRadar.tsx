"use client";

import Window from "@/components/shared/Window";
import { useCommandLog } from "@/contexts/CommandLogContext";
import { Radar, RefreshCw } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import clsx from "clsx";

interface IntelBrief {
  date?: string;
  from_cache?: boolean;
  report?: Record<string, string> | string;
  [key: string]: any;
}

export default function AloaRadar() {
  const { addLog } = useCommandLog();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [intel, setIntel] = useState<IntelBrief | null>(null);

  const fetchIntel = useCallback(async (forceRefresh = false) => {
    setIsRefreshing(true);
    if (forceRefresh) addLog("📡 ALOA Radar", "Scan Screen", "Intel gathering in progress...");
    try {
      const res = await fetch("http://localhost:8000/api/aloa-radar/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force_refresh: forceRefresh })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Scan failed");

      // Backend returns { status, brief, answer }
      // brief is the full object from build_brief() containing:
      //   { date, hackernews, github, devto, reddit, packages, report, from_cache, ... }
      // brief.report is the AI-generated report dict (or a raw string if LLM returned plain text)
      // answer is a copy of brief.report
      const brief = data.brief;

      // Detect if the LLM returned an error string instead of structured data
      if (brief && typeof brief === "string" && brief.startsWith("⚠️")) {
        throw new Error(brief);
      }

      setIntel(brief);
      if (forceRefresh) addLog("📡 ALOA Radar", "Scan Screen", "Intel Received ✅");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Scan failed";
      addLog("📡 ALOA Radar", "Error", message);
      if (forceRefresh) alert(message);
    } finally {
      setIsRefreshing(false);
    }
  }, [addLog]);

  useEffect(() => {
    Promise.resolve().then(() => fetchIntel(false));
  }, [fetchIntel]);

  // Normalize the report: it could be a dict or a raw markdown string from the LLM
  const report = intel?.report;
  const hasReport = report && typeof report === "object" && Object.keys(report).length > 0;
  const isRawString = report && typeof report === "string" && report.length > 0;

  return (
    <Window id="aloaRadar" title="ALOA Radar" icon={<Radar className="w-4 h-4 text-[var(--neon-purple)]" />} defaultPosition={{ x: 80, y: 140 }}>
      <div className="flex flex-col h-full">
        {/* Top Header */}
        <div className="p-4 flex justify-between items-center border-b border-[rgba(192,132,252,0.2)]">
          <div className="font-orbitron text-lg text-[var(--neon-purple)] font-bold tracking-widest drop-shadow-[0_0_8px_rgba(192,132,252,0.4)]">
            DAILY INTEL BRIEF
          </div>
          <div className="flex items-center gap-3">
            {intel?.from_cache && (
              <span className="text-[10px] bg-yellow-500/20 text-yellow-300 border border-yellow-500/50 px-2 py-0.5 rounded-full font-semibold">
                ● From Cache
              </span>
            )}
            <span className="text-xs text-[var(--color-text-dim)]">
              {intel?.date || new Date().toLocaleDateString()}
            </span>
            <button
              onClick={() => fetchIntel(true)}
              className="flex items-center gap-1 bg-white/5 border border-[var(--neon-purple)]/50 text-[var(--neon-purple)] px-2 py-1 rounded-md text-xs hover:bg-[var(--neon-purple)]/10 transition-all hover:shadow-[0_0_10px_rgba(192,132,252,0.3)]"
            >
              <RefreshCw className={clsx("w-3 h-3", isRefreshing && "animate-spin")} /> Refresh
            </button>
          </div>
        </div>

        {/* Intel Grid */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className={clsx("grid grid-cols-1 gap-4 transition-opacity duration-300", isRefreshing && "opacity-20")}>
            {hasReport ? (
              Object.entries(report).map(([key, value]) => (
                <div key={key} className="bg-white/5 border border-white/5 border-l-2 border-l-[var(--neon-purple)] p-4 rounded-lg">
                  <h3 className="text-[var(--neon-purple)] font-semibold mb-2 flex items-center gap-2 uppercase text-xs tracking-widest">
                    {key === "CURRENT AFFAIRS" && "🌍 "}
                    {key === "TECH NEWS" && "💻 "}
                    {key === "TRENDING TECH" && "🔥 "}
                    {key === "GENERAL KNOWLEDGE" && "🧠 "}
                    {key === "SUGGESTIONS" && "💡 "}
                    {key}
                  </h3>
                  <p className="text-xs text-[var(--color-text-dim)] leading-relaxed whitespace-pre-wrap">{value as string}</p>
                </div>
              ))
            ) : isRawString ? (
              <div className="bg-white/5 border border-white/5 border-l-2 border-l-[var(--neon-purple)] p-4 rounded-lg">
                <h3 className="text-[var(--neon-purple)] font-semibold mb-2 flex items-center gap-2 uppercase text-xs tracking-widest">
                  📡 AI REPORT
                </h3>
                <p className="text-xs text-[var(--color-text-dim)] leading-relaxed whitespace-pre-wrap">{report}</p>
              </div>
            ) : (
              <div className="h-40 flex flex-col items-center justify-center text-white/20 font-orbitron border-2 border-dashed border-white/5 rounded-xl">
                {isRefreshing ? "GATHERING INTEL..." : "NO INTEL FOUND"}
              </div>
            )}
          </div>
        </div>
      </div>
    </Window>
  );
}

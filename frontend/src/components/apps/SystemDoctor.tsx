"use client";

import Window from "@/components/shared/Window";
import { useCommandLog } from "@/contexts/CommandLogContext";
import { Activity, Trash2, ShieldX, Rocket } from "lucide-react";
import { useEffect, useState } from "react";

interface SystemProcess {
  name: string;
  cpu_percent?: number;
  memory_percent?: number;
}

export default function SystemDoctor() {
  const { addLog } = useCommandLog();
  const [cpu, setCpu] = useState(0);
  const [ram, setRam] = useState(0);
  const [processes, setProcesses] = useState<SystemProcess[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchStats = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/system-doctor/stats");
      const data = await res.json();
      setCpu(data.cpu_total || 0);
      setRam(data.ram_total || 0);
      setProcesses(data.top_apps || []);
    } catch (err) {
      console.error("Failed to fetch system stats:", err);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchStats();
    const interval = setInterval(fetchStats, 10000); // refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const handleClean = async () => {
    setIsLoading(true);
    addLog("🩺 System Doctor", "Clean Junk", "Initiating cleanup...");
    try {
      const res = await fetch("http://localhost:8000/api/system-doctor/clean", { method: "POST" });
      const data = await res.json();
      addLog("🩺 System Doctor", "Clean Junk", data.message || "Done");
    } catch (err) {
      console.error(err);
      addLog("🩺 System Doctor", "Clean Junk", "Error connecting to backend");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKill = async () => {
    const p = window.prompt("Enter process name to kill:");
    if (!p) return;
    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/system-doctor/kill", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ process_name: p })
      });
      const data = await res.json();
      addLog("🩺 System Doctor", `Kill ${p}`, data.message || "Terminated");
      fetchStats();
    } catch (err) {
      console.error(err);
      addLog("🩺 System Doctor", `Kill ${p}`, "Error connecting to backend");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Window id="sysDoctor" title="System Doctor" icon={<Activity className="w-4 h-4 text-[var(--neon-pink)]" />} defaultPosition={{ x: 200, y: 80 }}>
      <div className="flex flex-col h-full">
        {/* SVG Gradient Definition */}
        <svg className="w-0 h-0 absolute" aria-hidden="true" focusable="false">
          <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--neon-purple)" />
            <stop offset="100%" stopColor="var(--neon-pink)" />
          </linearGradient>
        </svg>

        {/* Gauges */}
        <div className="flex justify-around p-5 border-b border-[rgba(192,132,252,0.2)]">
          <Gauge value={cpu} label="CPU LOAD" />
          <Gauge value={ram} label="RAM USAGE" />
        </div>

        {/* Processes Table */}
        <div className="flex-1 overflow-y-auto p-4">
          <h3 className="text-xs text-[var(--color-text-dim)] tracking-widest mb-3">TOP PROCESSES</h3>
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="text-[var(--neon-purple)] font-semibold border-b border-white/5">
                <th className="pb-2">Process Name</th>
                <th className="pb-2">CPU%</th>
                <th className="pb-2">RAM%</th>
              </tr>
            </thead>
            <tbody>
              {processes.slice(0, 5).map((p, i) => (
                <tr key={i} className="border-b border-white/5 last:border-0">
                  <td className="py-2">{p.name}</td>
                  <td className="py-2">{p.cpu_percent?.toFixed(1) || "-"}</td>
                  <td className="py-2">{p.memory_percent?.toFixed(1) || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Action Buttons */}
        <div className="p-4 flex gap-3 bg-black/20">
          <button
            onClick={handleClean}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 bg-white/5 border border-[var(--neon-pink)]/50 text-[var(--neon-pink)] py-2 rounded-md hover:bg-[var(--neon-pink)]/10 hover:shadow-[0_0_15px_rgba(244,114,182,0.3)] transition-all font-semibold disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" /> Clean Junk
          </button>
          <button
            onClick={handleKill}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 bg-white/5 border border-rose-500/50 text-rose-500 py-2 rounded-md hover:bg-rose-500/10 hover:shadow-[0_0_15px_rgba(244,63,94,0.3)] transition-all font-semibold disabled:opacity-50"
          >
            <ShieldX className="w-4 h-4" /> Kill Process
          </button>
          <button
            onClick={() => addLog("🩺 System Doctor", "Startup Apps", "Opened configuration")}
            className="flex-1 flex items-center justify-center gap-2 bg-white/5 border border-[var(--neon-purple)]/50 text-[var(--neon-purple)] py-2 rounded-md hover:bg-[var(--neon-purple)]/10 hover:shadow-[0_0_15px_rgba(192,132,252,0.3)] transition-all font-semibold"
          >
            <Rocket className="w-4 h-4" /> Startup Apps
          </button>
        </div>
      </div>
    </Window>
  );
}

function Gauge({ value, label }: { value: number; label: string }) {
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <div className="relative w-[120px] h-[120px] flex flex-col items-center justify-center">
      <svg viewBox="0 0 120 120" className="absolute inset-0 -rotate-90">
        <circle cx="60" cy="60" r={radius} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke="url(#gaugeGradient)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="z-10 font-orbitron text-2xl font-bold drop-shadow-[0_0_10px_rgba(192,132,252,0.5)]">
        {value}%
      </div>
      <div className="z-10 text-[10px] text-[var(--color-text-dim)] mt-1 tracking-wider">{label}</div>
    </div>
  );
}

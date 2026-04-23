"use client";

import { useWindows } from "@/contexts/WindowContext";
import { Bot, Activity, ClipboardList, GraduationCap, Radar, Terminal as TerminalIcon, Monitor, Bug, Cloud, Rocket, FileText } from "lucide-react";
import { useEffect, useState, useCallback, useRef } from "react";
import clsx from "clsx";

type HealthStatus = "online" | "partial" | "offline";

interface HealthFeatures {
  [key: string]: boolean;
}

interface HealthData {
  features: HealthFeatures;
  groq: boolean;
  openrouter: boolean;
  gemini: boolean;
}

export default function Taskbar() {
  const { windows, openWindow } = useWindows();
  const [time, setTime] = useState("");
  const [healthStatus, setHealthStatus] = useState<HealthStatus>("offline");
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [showHealthPopover, setShowHealthPopover] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString("en-US", { hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch("http://localhost:8000/api/health");
      if (!res.ok) {
        setHealthStatus("offline");
        setHealthData(null);
        return;
      }
      const data: HealthData = await res.json();
      setHealthData(data);

      // Determine overall status from features
      if (data.features) {
        const featureValues = Object.values(data.features);
        const allOnline = featureValues.every(Boolean);
        const someOnline = featureValues.some(Boolean);

        if (allOnline) {
          setHealthStatus("online");
        } else if (someOnline) {
          setHealthStatus("partial");
        } else {
          setHealthStatus("offline");
        }
      } else {
        setHealthStatus("online");
      }
    } catch {
      setHealthStatus("offline");
      setHealthData(null);
    }
  }, []);

  useEffect(() => {
    Promise.resolve().then(() => fetchHealth());
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, [fetchHealth]);

  // Close popover on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setShowHealthPopover(false);
      }
    };
    if (showHealthPopover) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showHealthPopover]);

  const statusDotColor = {
    online: "bg-green-500 shadow-[0_0_8px_#22c55e]",
    partial: "bg-yellow-500 shadow-[0_0_8px_#eab308]",
    offline: "bg-red-500 shadow-[0_0_8px_#ef4444]",
  }[healthStatus];

  const statusLabel = {
    online: "AI Online",
    partial: "Partial",
    offline: "Offline",
  }[healthStatus];

  // Pretty feature name mapping
  const featureDisplayNames: Record<string, string> = {
    app_manager: "App Manager",
    system_doctor: "System Doctor",
    attendance: "Attendance",
    lecture_notes: "Lecture Notes",
    aloa_radar: "ALOA Radar",
    exam_pilot: "Exam Pilot",
    code_healer: "Code Healer",
    cloud_healer: "Cloud Healer",
    auto_deployer: "Auto Deployer",
    resume_engine: "Resume Engine",
  };

  const apps = [
    { id: "appManager",   label: "App Manager",   icon: Bot },
    { id: "sysDoctor",    label: "System Doctor",  icon: Activity },
    { id: "attendance",   label: "Attendance",     icon: ClipboardList },
    { id: "lectureNotes", label: "Lecture Notes",  icon: GraduationCap },
    { id: "aloaRadar",    label: "ALOA Radar",     icon: Radar },
    { id: "examPilot",    label: "Exam Pilot",     icon: Monitor },
    { id: "codeHealer",   label: "Code Healer",    icon: Bug },
    { id: "cloudHealer",  label: "Cloud Healer",   icon: Cloud },
    { id: "autoDeployer", label: "Deployer",       icon: Rocket },
    { id: "resumeEngine", label: "Resume",         icon: FileText },
    { id: "terminal",     label: "Terminal",       icon: TerminalIcon },
  ] as const;

  return (
    <div className="fixed bottom-0 left-0 w-full h-[56px] bg-[var(--color-taskbar-bg)] backdrop-blur-3xl border-t border-[rgba(192,132,252,0.3)] z-[100] flex justify-between items-center px-4">
      {/* Left: Logo */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="font-orbitron font-bold text-xl bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-pink)] bg-clip-text text-transparent drop-shadow-[0_0_10px_rgba(192,132,252,0.3)]">
          ALOA
        </div>
        <span className="text-sm font-semibold tracking-widest text-white/90 hidden lg:block">THE ALOA</span>
      </div>

      {/* Center: App Icons */}
      <div className="flex gap-1 h-full items-center overflow-x-auto">
        {apps.map((app) => {
          const state = windows[app.id];
          const isActive = state.isOpen && !state.isMinimized;
          return (
            <button
              key={app.id}
              onClick={() => openWindow(app.id)}
              className={clsx(
                "group relative flex flex-col items-center justify-center px-2 py-1 rounded-xl border border-transparent transition-all duration-200 shrink-0",
                "hover:scale-110 hover:bg-white/10 hover:border-[rgba(192,132,252,0.2)] hover:shadow-[0_0_20px_rgba(192,132,252,0.4)]"
              )}
            >
              <app.icon className="w-5 h-5 text-white mb-0.5 group-hover:text-[var(--neon-purple)] transition-colors" />
              <span className="text-[9px] text-[var(--color-text-dim)] font-inter leading-none">{app.label}</span>

              {state.isOpen && (
                <div
                  className={clsx(
                    "absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full",
                    isActive ? "bg-[var(--neon-pink)] shadow-[0_0_5px_var(--neon-pink)]" : "bg-white/40"
                  )}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Right: Status & Clock */}
      <div className="flex items-center gap-3 shrink-0">
        <div className="relative" ref={popoverRef}>
          <button
            onClick={() => setShowHealthPopover((prev) => !prev)}
            className="flex items-center gap-2 text-xs text-[var(--color-text-dim)] bg-white/5 px-3 py-1 rounded-full border border-white/10 hover:bg-white/10 transition-all cursor-pointer"
          >
            <div className={clsx("w-2 h-2 rounded-full", statusDotColor, healthStatus !== "offline" && "animate-pulse")} />
            <span className="hidden sm:inline">{statusLabel}</span>
          </button>

          {/* Health Popover */}
          {showHealthPopover && healthData?.features && (
            <div className="absolute bottom-full right-0 mb-2 w-[220px] bg-[var(--color-taskbar-bg)] backdrop-blur-xl border border-[rgba(192,132,252,0.3)] rounded-xl shadow-[0_0_30px_rgba(0,0,0,0.5)] p-3 z-[200]">
              <div className="font-orbitron text-[10px] text-[var(--neon-purple)] tracking-widest mb-2 pb-1.5 border-b border-white/10">
                SYSTEM STATUS
              </div>

              {/* Provider Status */}
              <div className="mb-2 pb-2 border-b border-white/5">
                <div className="text-[9px] text-white/30 tracking-wider mb-1">PROVIDERS</div>
                {(["groq", "openrouter", "gemini"] as const).map((provider) => (
                  <div key={provider} className="flex items-center justify-between py-0.5">
                    <span className="text-[10px] text-white/60 capitalize">{provider}</span>
                    <div className={clsx("w-1.5 h-1.5 rounded-full", healthData[provider] ? "bg-green-500" : "bg-red-500/60")} />
                  </div>
                ))}
              </div>

              {/* Feature Status */}
              <div className="text-[9px] text-white/30 tracking-wider mb-1">FEATURES</div>
              {Object.entries(healthData.features).map(([key, online]) => (
                <div key={key} className="flex items-center justify-between py-0.5">
                  <span className="text-[10px] text-white/60">{featureDisplayNames[key] || key}</span>
                  <div className={clsx("w-1.5 h-1.5 rounded-full", online ? "bg-green-500" : "bg-red-500/60")} />
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="font-orbitron text-lg text-[var(--neon-purple)] drop-shadow-[0_0_10px_rgba(192,132,252,0.5)] w-[80px] text-right">
          {time}
        </div>
      </div>
    </div>
  );
}

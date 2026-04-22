"use client";

import { useWindows } from "@/contexts/WindowContext";
import { Bot, Activity, ClipboardList, GraduationCap, Radar, Terminal as TerminalIcon } from "lucide-react";
import { useEffect, useState } from "react";
import clsx from "clsx";

export default function Taskbar() {
  const { windows, openWindow } = useWindows();
  const [time, setTime] = useState("");

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString("en-US", { hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const apps = [
    { id: "appManager", label: "App Manager", icon: Bot },
    { id: "sysDoctor", label: "System Doctor", icon: Activity },
    { id: "attendance", label: "Attendance", icon: ClipboardList },
    { id: "lectureNotes", label: "Lecture Notes", icon: GraduationCap },
    { id: "aloaRadar", label: "ALOA Radar", icon: Radar },
    { id: "terminal", label: "Terminal", icon: TerminalIcon },
  ] as const;

  return (
    <div className="fixed bottom-0 left-0 w-full h-[56px] bg-[var(--color-taskbar-bg)] backdrop-blur-3xl border-t border-[rgba(192,132,252,0.3)] z-[100] flex justify-between items-center px-5">
      
      {/* Left: Logo */}
      <div className="flex items-center gap-3">
        <div className="font-orbitron font-bold text-xl bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-pink)] bg-clip-text text-transparent drop-shadow-[0_0_10px_rgba(192,132,252,0.3)]">
          ALOA
        </div>
        <span className="text-sm font-semibold tracking-widest text-white/90">THE ALOA</span>
      </div>

      {/* Center: App Icons */}
      <div className="flex gap-4 h-full items-center">
        {apps.map((app) => {
          const state = windows[app.id];
          const isActive = state.isOpen && !state.isMinimized;
          return (
            <button
              key={app.id}
              onClick={() => openWindow(app.id)}
              className={clsx(
                "group relative flex flex-col items-center justify-center px-3 py-1 rounded-xl border border-transparent transition-all duration-200",
                "hover:scale-110 hover:bg-white/10 hover:border-[rgba(192,132,252,0.2)] hover:shadow-[0_0_20px_rgba(192,132,252,0.4)]"
              )}
            >
              <app.icon className="w-6 h-6 text-white mb-0.5 group-hover:text-[var(--neon-purple)] transition-colors" />
              <span className="text-[10px] text-[var(--color-text-dim)] font-inter">{app.label}</span>
              
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
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs text-[var(--color-text-dim)] bg-white/5 px-3 py-1 rounded-full border border-white/10">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_#22c55e]" />
          AI Online
        </div>
        <div className="font-orbitron text-lg text-[var(--neon-purple)] drop-shadow-[0_0_10px_rgba(192,132,252,0.5)] w-[90px] text-right">
          {time}
        </div>
      </div>
    </div>
  );
}

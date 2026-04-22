"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

export interface LogEntry {
  id: string;
  app: string;
  action: string;
  result: string;
  time: string;
}

interface CommandLogContextProps {
  logs: LogEntry[];
  addLog: (app: string, action: string, result: string) => void;
}

const initialLogs: LogEntry[] = [
  { id: "1", app: "🤖 App Manager", action: "Open Spotify", result: "Generated: start spotify ··· confirmed ✅", time: "10:42:05" },
  { id: "2", app: "🩺 System Doctor", action: "CPU: 87% spike", result: "Suggested: kill chrome.exe ··· action taken", time: "10:45:12" },
  { id: "3", app: "📡 ALOA Radar", action: "Brief refresh triggered", result: "5 new intel items loaded ··· cached", time: "11:00:00" },
  { id: "4", app: "🎓 Lecture Notes", action: "youtube.com/watch?v=xyz", result: "Notes generated ··· PDF ready ✅", time: "11:15:30" },
];

const CommandLogContext = createContext<CommandLogContextProps | undefined>(undefined);

export const CommandLogProvider = ({ children }: { children: ReactNode }) => {
  const [logs, setLogs] = useState<LogEntry[]>(initialLogs);

  const addLog = (app: string, action: string, result: string) => {
    const newLog: LogEntry = {
      id: Date.now().toString() + Math.random().toString(36).substring(7),
      app,
      action,
      result,
      time: new Date().toLocaleTimeString('en-US', { hour12: false }),
    };
    setLogs((prev) => [...prev, newLog]);
  };

  return (
    <CommandLogContext.Provider value={{ logs, addLog }}>
      {children}
    </CommandLogContext.Provider>
  );
};

export const useCommandLog = () => {
  const context = useContext(CommandLogContext);
  if (!context) throw new Error("useCommandLog must be used within CommandLogProvider");
  return context;
};

"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

export type WindowId =
  | "appManager"
  | "sysDoctor"
  | "attendance"
  | "lectureNotes"
  | "aloaRadar"
  | "terminal"
  | "examPilot"
  | "codeHealer"
  | "cloudHealer"
  | "autoDeployer"
  | "resumeEngine";

export interface WindowState {
  id: WindowId;
  isOpen: boolean;
  isMinimized: boolean;
  zIndex: number;
}

interface WindowContextProps {
  windows: Record<WindowId, WindowState>;
  openWindow: (id: WindowId) => void;
  closeWindow: (id: WindowId) => void;
  toggleMinimize: (id: WindowId) => void;
  focusWindow: (id: WindowId) => void;
}

const defaultWindows: Record<WindowId, WindowState> = {
  appManager:    { id: "appManager",    isOpen: false, isMinimized: false, zIndex: 10 },
  sysDoctor:     { id: "sysDoctor",     isOpen: false, isMinimized: false, zIndex: 10 },
  attendance:    { id: "attendance",    isOpen: false, isMinimized: false, zIndex: 10 },
  lectureNotes:  { id: "lectureNotes",  isOpen: false, isMinimized: false, zIndex: 10 },
  aloaRadar:     { id: "aloaRadar",     isOpen: false, isMinimized: false, zIndex: 10 },
  terminal:      { id: "terminal",      isOpen: false, isMinimized: false, zIndex: 10 },
  examPilot:     { id: "examPilot",     isOpen: false, isMinimized: false, zIndex: 10 },
  codeHealer:    { id: "codeHealer",    isOpen: false, isMinimized: false, zIndex: 10 },
  cloudHealer:   { id: "cloudHealer",   isOpen: false, isMinimized: false, zIndex: 10 },
  autoDeployer:  { id: "autoDeployer",  isOpen: false, isMinimized: false, zIndex: 10 },
  resumeEngine:  { id: "resumeEngine",  isOpen: false, isMinimized: false, zIndex: 10 },
};

const WindowContext = createContext<WindowContextProps | undefined>(undefined);

export const WindowProvider = ({ children }: { children: ReactNode }) => {
  const [windows, setWindows] = useState<Record<WindowId, WindowState>>(defaultWindows);
  const [, setMaxZIndex] = useState(10);

  const focusWindow = (id: WindowId) => {
    setMaxZIndex((prevMax) => {
      const newMax = prevMax + 1;
      setWindows((prevWindows) => ({
        ...prevWindows,
        [id]: { ...prevWindows[id], zIndex: newMax },
      }));
      return newMax;
    });
  };

  const openWindow = (id: WindowId) => {
    setMaxZIndex((prevMax) => {
      const newMax = prevMax + 1;
      setWindows((prevWindows) => {
        const isCurrentlyOpen = prevWindows[id].isOpen;
        if (isCurrentlyOpen && !prevWindows[id].isMinimized) {
          return { ...prevWindows, [id]: { ...prevWindows[id], zIndex: newMax } };
        }
        return { ...prevWindows, [id]: { ...prevWindows[id], isOpen: true, isMinimized: false, zIndex: newMax } };
      });
      return newMax;
    });
  };

  const closeWindow = (id: WindowId) => {
    setWindows((prev) => ({ ...prev, [id]: { ...prev[id], isOpen: false } }));
  };

  const toggleMinimize = (id: WindowId) => {
    setWindows((prev) => ({
      ...prev,
      [id]: { ...prev[id], isMinimized: !prev[id].isMinimized },
    }));
  };

  return (
    <WindowContext.Provider value={{ windows, openWindow, closeWindow, toggleMinimize, focusWindow }}>
      {children}
    </WindowContext.Provider>
  );
};

export const useWindows = () => {
  const context = useContext(WindowContext);
  if (!context) throw new Error("useWindows must be used within WindowProvider");
  return context;
};

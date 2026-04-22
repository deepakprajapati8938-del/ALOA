"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";

export type WindowId = "appManager" | "sysDoctor" | "attendance" | "lectureNotes" | "aloaRadar" | "terminal";

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
  appManager: { id: "appManager", isOpen: false, isMinimized: false, zIndex: 10 },
  sysDoctor: { id: "sysDoctor", isOpen: false, isMinimized: false, zIndex: 10 },
  attendance: { id: "attendance", isOpen: false, isMinimized: false, zIndex: 10 },
  lectureNotes: { id: "lectureNotes", isOpen: false, isMinimized: false, zIndex: 10 },
  aloaRadar: { id: "aloaRadar", isOpen: false, isMinimized: false, zIndex: 10 },
  terminal: { id: "terminal", isOpen: false, isMinimized: false, zIndex: 10 },
};

const WindowContext = createContext<WindowContextProps | undefined>(undefined);

export const WindowProvider = ({ children }: { children: ReactNode }) => {
  const [windows, setWindows] = useState<Record<WindowId, WindowState>>(defaultWindows);
  const [maxZIndex, setMaxZIndex] = useState(10);

  const focusWindow = (id: WindowId) => {
    setMaxZIndex((prev) => prev + 1);
    setWindows((prev) => ({
      ...prev,
      [id]: { ...prev[id], zIndex: maxZIndex + 1 },
    }));
  };

  const openWindow = (id: WindowId) => {
    setMaxZIndex((prev) => prev + 1);
    setWindows((prev) => {
      const isCurrentlyOpen = prev[id].isOpen;
      if (isCurrentlyOpen && !prev[id].isMinimized) {
        // Just focus
        return {
          ...prev,
          [id]: { ...prev[id], zIndex: maxZIndex + 1 },
        };
      }
      return {
        ...prev,
        [id]: { ...prev[id], isOpen: true, isMinimized: false, zIndex: maxZIndex + 1 },
      };
    });
  };

  const closeWindow = (id: WindowId) => {
    setWindows((prev) => ({
      ...prev,
      [id]: { ...prev[id], isOpen: false },
    }));
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

"use client";

import { motion, AnimatePresence, useDragControls } from "framer-motion";
import { useWindows, WindowId } from "@/contexts/WindowContext";
import { X, Minus, Square } from "lucide-react";
import React from "react";

interface WindowProps {
  id: WindowId;
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultPosition?: { x: number; y: number };
}

export default function Window({ id, title, icon, children, defaultPosition = { x: 100, y: 100 } }: WindowProps) {
  const { windows, closeWindow, toggleMinimize, focusWindow } = useWindows();
  const state = windows[id];
  const dragControls = useDragControls();

  if (!state.isOpen) return null;

  return (
    <AnimatePresence>
      {!state.isMinimized && (
        <motion.div
          drag
          dragMomentum={false}
          dragControls={dragControls}
          dragListener={false}
          initial={{ scale: 0.95, opacity: 0, x: defaultPosition.x, y: defaultPosition.y }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          transition={{ duration: 0.2 }}
          onMouseDown={() => focusWindow(id)}
          style={{ zIndex: state.zIndex }}
          className="absolute glass-window rounded-2xl w-[520px] h-[420px] flex flex-col overflow-hidden"
        >
          {/* Titlebar (Drag Handle) */}
          <div 
            onPointerDown={(e) => dragControls.start(e)}
            className="h-[40px] bg-[var(--color-taskbar-bg)] border-b border-[var(--neon-purple)] flex items-center justify-between px-4 cursor-grab active:cursor-grabbing shrink-0 relative overflow-hidden"
          >
            {/* Shimmer effect */}
            <div className="absolute top-0 -left-full w-1/2 h-full bg-gradient-to-r from-transparent via-white/5 to-transparent animate-[titleShimmer_4s_infinite_linear]" />
            
            <div className="flex items-center gap-2 font-orbitron text-sm text-white z-10">
              {icon}
              {title}
            </div>
            <div className="flex gap-2 z-10">
              <button
                onMouseDown={(e) => e.stopPropagation()}
                onClick={() => toggleMinimize(id)}
                className="w-3 h-3 rounded-full bg-yellow-500 hover:scale-125 transition-transform shadow-[0_0_5px_#eab308] flex items-center justify-center group"
              >
                <Minus className="w-2 h-2 opacity-0 group-hover:opacity-100 text-yellow-900" />
              </button>
              <button
                onMouseDown={(e) => e.stopPropagation()}
                className="w-3 h-3 rounded-full bg-green-500 hover:scale-125 transition-transform shadow-[0_0_5px_#22c55e] flex items-center justify-center group"
              >
                <Square className="w-2 h-2 opacity-0 group-hover:opacity-100 text-green-900" />
              </button>
              <button
                onMouseDown={(e) => e.stopPropagation()}
                onClick={() => closeWindow(id)}
                className="w-3 h-3 rounded-full bg-rose-500 hover:scale-125 transition-transform shadow-[0_0_5px_#f43f5e] flex items-center justify-center group"
              >
                <X className="w-2 h-2 opacity-0 group-hover:opacity-100 text-rose-900" />
              </button>
            </div>
          </div>

          {/* Content Area */}
          <div className="flex-grow relative overflow-hidden flex flex-col bg-transparent">
            {children}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

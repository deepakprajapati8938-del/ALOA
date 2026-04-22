"use client";

import { motion } from "framer-motion";
import { useEffect, useState } from "react";

export default function BootScreen() {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
    }, 2500);
    return () => clearTimeout(timer);
  }, []);

  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 1 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5, delay: 2.5 }}
      className="fixed inset-0 z-[9999] bg-[#0a0514] flex flex-col items-center justify-center"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="text-center"
      >
        <h1 className="font-orbitron text-7xl font-bold text-[var(--neon-purple)] drop-shadow-[0_0_20px_rgba(192,132,252,0.4)] mb-4">
          ALOA
        </h1>
        <p className="font-inter text-[var(--color-text-dim)] tracking-[0.2em] mb-10 text-xl">
          AI LAPTOP ASSISTANT — OS v1.0
        </p>
        
        <div className="w-[300px] h-[2px] bg-white/10 relative overflow-hidden mx-auto">
          <motion.div
            initial={{ width: "0%" }}
            animate={{ width: "100%" }}
            transition={{ duration: 2.3, ease: "linear" }}
            className="absolute top-0 left-0 h-full bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-pink)]"
          />
        </div>
      </motion.div>
    </motion.div>
  );
}

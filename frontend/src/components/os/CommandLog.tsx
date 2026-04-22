"use client";

import { useCommandLog } from "@/contexts/CommandLogContext";

export default function CommandLog() {
  const { logs } = useCommandLog();

  return (
    <div className="fixed bottom-[56px] left-0 w-full h-[40px] bg-white/[0.03] backdrop-blur-md border-t border-[rgba(192,132,252,0.2)] z-[90] flex items-center overflow-hidden font-mono text-[12px] text-[var(--neon-purple)] whitespace-nowrap">
      <div className="inline-block whitespace-nowrap pl-full animate-ticker hover:[animation-play-state:paused]">
        {logs.map((log) => (
          <span key={log.id} className="inline-block mr-10">
            {log.app} → &quot;{log.action}&quot; → {log.result} ··· [{log.time}]
          </span>
        ))}
      </div>
      <style jsx>{`
        @keyframes ticker {
          0% { transform: translateX(100vw); }
          100% { transform: translateX(-100%); }
        }
        .animate-ticker {
          animation: ticker 30s linear infinite;
          padding-left: 100vw;
        }
      `}</style>
    </div>
  );
}

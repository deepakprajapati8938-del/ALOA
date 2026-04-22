"use client";

import Window from "@/components/shared/Window";
import { useCommandLog } from "@/contexts/CommandLogContext";
import { Terminal as TerminalIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import clsx from "clsx";
import { useWindows } from "@/contexts/WindowContext";

interface TerminalLine {
  id: string;
  text: string;
  type: "system" | "user" | "response";
}

const BOOT_SEQUENCE = [
  "ALOA OS v1.0 — Terminal Active",
  "> Initializing feature modules... OK",
  "> Groq API: Connected ✅",
  "> Gemini API: Connected ✅",
  "> Loading watchlist... radar_watchlist.json found",
  "> System scan: CPU 42% | RAM 67% | Disk 55%",
  "> All systems nominal. ALOA is ready."
];

export default function Terminal() {
  const { addLog } = useCommandLog();
  const { windows } = useWindows();
  const [lines, setLines] = useState<TerminalLine[]>([]);
  const [input, setInput] = useState("");
  const [isBooting, setIsBooting] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  
  // Track if we've booted so we don't boot again if closed/reopened (optional, but standard OS behavior)
  const hasBooted = useRef(false);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines, isBooting]);

  useEffect(() => {
    if (windows.terminal.isOpen && !hasBooted.current) {
      hasBooted.current = true;
      let delay = 0;
      
      BOOT_SEQUENCE.forEach((text, i) => {
        setTimeout(() => {
          setLines((prev) => [
            ...prev,
            { id: `boot-${i}`, text, type: "system" }
          ]);
          
          if (i === BOOT_SEQUENCE.length - 1) {
            setTimeout(() => {
              setIsBooting(false);
              inputRef.current?.focus();
            }, 500);
          }
        }, delay);
        delay += 600;
      });
    }
  }, [windows.terminal.isOpen]);

  const handleCommand = async () => {
    if (!input.trim() || isBooting) return;
    
    const cmd = input.trim();
    setLines((prev) => [...prev, { id: Date.now().toString(), text: `> ${cmd}`, type: "user" }]);
    setInput("");
    addLog("⌨️ Terminal", cmd, "Processing...");

    try {
      // 1. Generate the actual system command from natural language
      const genRes = await fetch("http://localhost:8000/api/app-manager/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: cmd })
      });
      const genData = await genRes.json();
      if (!genRes.ok) throw new Error(genData.detail || "Generation failed");
      
      const generatedCmd = genData.command;
      
      // Only show the generated command if it differs from the user input (i.e. AI actually generated something)
      if (generatedCmd !== cmd && !generatedCmd.startsWith("start ")) {
        setLines((prev) => [
          ...prev,
          { id: Date.now().toString() + "-gen", text: `[System]: Executing \`${generatedCmd}\``, type: "system" }
        ]);
      }
      
      addLog("⌨️ Terminal", generatedCmd, "Executing");

      // 2. Execute the generated command
      const res = await fetch("http://localhost:8000/api/app-manager/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: generatedCmd })
      });
      const data = await res.json();
      
      if (!res.ok) throw new Error(data.detail || "Execution failed");
      
      setLines((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), text: data.message || "Execution complete", type: "response" }
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Execution failed";
      setLines((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), text: "Error: " + message, type: "response" }
      ]);
      addLog("⌨️ Terminal", "Error", message);
    }
  };

  return (
    <Window id="terminal" title="Terminal" icon={<TerminalIcon className="w-4 h-4 text-white" />} defaultPosition={{ x: 350, y: 180 }}>
      <div 
        className="flex flex-col h-full bg-black/80 font-mono text-sm p-4 overflow-hidden"
        onClick={() => !isBooting && inputRef.current?.focus()}
      >
        <div ref={scrollRef} className="flex-1 overflow-y-auto flex flex-col gap-1 pb-2">
          {lines.map((line, i) => (
            <div
              key={line.id}
              className={clsx(
                "animate-in fade-in duration-300",
                line.type === "system" && (i % 2 === 0 ? "text-[var(--neon-purple)]" : "text-[var(--neon-pink)]"),
                line.type === "user" && "text-[var(--neon-purple)]",
                line.type === "response" && "text-[var(--neon-pink)]"
              )}
            >
              {line.text}
            </div>
          ))}

          {!isBooting && (
            <div className="flex text-[var(--color-text-base)] mt-2">
              <span className="mr-2">&gt;</span>
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCommand()}
                className="flex-1 bg-transparent border-none outline-none text-[var(--color-text-base)]"
                autoComplete="off"
                spellCheck="false"
              />
              {/* Fake cursor for focus styling if wanted, native caret is fine too */}
            </div>
          )}
        </div>
      </div>
    </Window>
  );
}

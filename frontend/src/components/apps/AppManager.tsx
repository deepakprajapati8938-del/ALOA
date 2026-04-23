"use client";

import Window from "@/components/shared/Window";
import { useCommandLog } from "@/contexts/CommandLogContext";
import { Bot, Send, AlertTriangle } from "lucide-react";
import { useState, useRef, useEffect } from "react";

interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  actionable?: boolean;
  isError?: boolean;
}

/**
 * Strip known prefixes like "Generated command: " or "Generated: " from
 * an AI message so the raw command is sent to /api/app-manager/execute.
 */
function extractCommand(messageText: string): string {
  return messageText
    .replace(/^Generated command:\s*/i, "")
    .replace(/^Generated:\s*/i, "")
    .replace(/\s*\(Executed\)\s*$/i, "")
    .replace(/\s*\(Cancelled\)\s*$/i, "")
    .trim();
}

/**
 * Detect if an LLM response is an error sentinel from the fallback chain.
 * The upgraded backend returns { command: "⚠️ All LLM providers failed..." }
 * on failure instead of a 500 error.
 */
function isLLMError(text: string): boolean {
  return text.startsWith("⚠️") || text.startsWith("AI ERROR");
}

export default function AppManager() {
  const { addLog } = useCommandLog();
  const [messages, setMessages] = useState<Message[]>([
    { id: "1", sender: "user", text: "Open Spotify" },
    { id: "2", sender: "ai", text: "Generated command: start spotify", actionable: true },
    { id: "3", sender: "user", text: "Download VLC" },
    { id: "4", sender: "ai", text: "Generated: winget install VLC media player -e --silent", actionable: true },
  ]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    const userMsg = input.trim();
    setMessages((prev) => [...prev, { id: Date.now().toString(), sender: "user", text: userMsg }]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/app-manager/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: userMsg }),
      });
      const data = await res.json();

      // Handle HTTP error responses (400, 502, 500) from upgraded backend
      if (!res.ok) {
        setMessages((prev) => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            sender: "ai",
            text: data.detail || `Server error (${res.status})`,
            actionable: false,
            isError: true,
          },
        ]);
        return;
      }

      const commandText = data.command || "Error generating command";
      const errorDetected = isLLMError(commandText);

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          sender: "ai",
          text: errorDetected ? commandText : `Generated command: ${commandText}`,
          // Never mark LLM error strings as actionable
          actionable: !errorDetected && !!data.command,
          isError: errorDetected,
        },
      ]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), sender: "ai", text: "Connection error. Is backend running?", isError: true }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirm = async (command: string, msgId: string) => {
    // Strip any "Generated command: " prefix before sending to the execute endpoint
    const cleanCmd = extractCommand(command);
    addLog("🤖 App Manager", cleanCmd, "Executing...");

    try {
      const res = await fetch("http://localhost:8000/api/app-manager/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cleanCmd }),
      });

      if (res.ok) {
        addLog("🤖 App Manager", cleanCmd, "Action executed ✅");
        setMessages((prev) => prev.map(m => m.id === msgId ? { ...m, actionable: false, text: `${m.text} (Executed)` } : m));
      } else {
        const data = await res.json().catch(() => ({}));
        addLog("🤖 App Manager", cleanCmd, data.detail || "Failed ❌");
      }
    } catch (err) {
      console.error(err);
      addLog("🤖 App Manager", cleanCmd, "Connection error ❌");
    }
  };

  const handleCancel = (msgId: string) => {
    setMessages((prev) => prev.map(m => m.id === msgId ? { ...m, actionable: false, text: `${m.text} (Cancelled)` } : m));
  };

  return (
    <Window id="appManager" title="App Manager" icon={<Bot className="w-4 h-4 text-[var(--neon-purple)]" />} defaultPosition={{ x: 150, y: 50 }}>
      <div className="flex flex-col h-full">
        {/* Chat Area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 scroll-smooth">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`max-w-[85%] p-3 rounded-xl text-sm leading-relaxed ${
                msg.sender === "user"
                  ? "self-end bg-white/5 border border-[var(--neon-pink)] rounded-br-sm"
                  : msg.isError
                    ? "self-start bg-rose-500/5 border border-rose-500/50 rounded-bl-sm"
                    : "self-start bg-white/5 border border-[var(--neon-purple)] rounded-bl-sm"
              }`}
            >
              {msg.isError && (
                <div className="flex items-center gap-1.5 mb-1.5 text-rose-400 text-xs font-semibold">
                  <AlertTriangle className="w-3 h-3" /> LLM Error
                </div>
              )}
              <span className={msg.isError ? "text-rose-300/80" : ""}>{msg.text}</span>
              {msg.actionable && (
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={() => handleConfirm(msg.text, msg.id)}
                    className="px-3 py-1 bg-white/5 hover:bg-white/10 border border-[var(--neon-purple)] text-[var(--neon-purple)] rounded-md transition-all hover:shadow-[0_0_10px_var(--neon-purple)]"
                  >
                    Confirm ✅
                  </button>
                  <button
                    onClick={() => handleCancel(msg.id)}
                    className="px-3 py-1 bg-white/5 hover:bg-white/10 border border-rose-500/50 text-rose-400 rounded-md transition-all hover:shadow-[0_0_10px_rgba(244,63,94,0.4)]"
                  >
                    Cancel ❌
                  </button>
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="self-start bg-white/5 border border-[var(--neon-purple)] rounded-bl-sm p-3 rounded-xl text-sm leading-relaxed text-white/50 animate-pulse">
              ALOA is thinking...
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-[rgba(192,132,252,0.2)] bg-black/20 flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            disabled={isLoading}
            placeholder="Tell ALOA what to do... (Hinglish supported)"
            className="flex-1 bg-white/5 border-b border-[rgba(192,132,252,0.3)] focus:border-[var(--neon-purple)] focus:shadow-[0_4px_10px_rgba(192,132,252,0.1)] outline-none px-3 py-2 rounded-t-md text-sm transition-all"
          />
          <button
            onClick={handleSend}
            className="bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-pink)] px-4 py-2 rounded-md font-semibold text-white hover:shadow-[0_0_15px_var(--neon-purple)] transition-all flex items-center justify-center"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </Window>
  );
}

"use client";

import Window from "@/components/shared/Window";
import { useCommandLog } from "@/contexts/CommandLogContext";
import { ClipboardList, UploadCloud, Save } from "lucide-react";
import { useState } from "react";
import clsx from "clsx";

interface Student {
  id: string;
  name: string;
  present: boolean;
}

export default function Attendance() {
  const { addLog } = useCommandLog();
  const [students, setStudents] = useState<Student[]>([]);
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [filePath, setFilePath] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLoad = async () => {
    if (!filePath) return alert("Please enter a file path");
    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/attendance/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Load failed");
      
      const loadedStudents: Student[] = data.students.map((s: string) => {
        const match = s.match(/\[(.*?)\] (.*)/);
        return {
          id: match ? match[1] : Math.random().toString(),
          name: match ? match[2] : s,
          present: true
        };
      });
      setStudents(loadedStudents);
      addLog("📋 Attendance", "Load File", data.message);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Load failed";
      addLog("📋 Attendance", "Load Error", message);
      alert(message);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleAttendance = (id: string) => {
    setStudents((prev) =>
      prev.map((s) => (s.id === id ? { ...s, present: !s.present } : s))
    );
  };

  const handleSave = async () => {
    if (students.length === 0) return alert("No students loaded");
    setIsLoading(true);
    
    // Convert current student states to the comma-separated tokens expected by the backend
    // Actually the backend expects absent tokens
    const absentInputs = students
      .filter(s => !s.present)
      .map(s => s.id)
      .join(" ");

    try {
      const res = await fetch("http://localhost:8000/api/attendance/mark", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          absent_inputs: absentInputs,
          date: date
        })
      });
      const data = await res.json();
      addLog("📋 Attendance", "Save Attendance", data.message);
      alert(data.message);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Save error";
      addLog("📋 Attendance", "Save Error", message);
      alert(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Window id="attendance" title="Attendance" icon={<ClipboardList className="w-4 h-4 text-[var(--neon-purple)]" />} defaultPosition={{ x: 250, y: 110 }}>
      <div className="flex flex-col h-full">
        {/* Top Controls */}
        <div className="flex gap-4 p-4 border-b border-[rgba(192,132,252,0.2)]">
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="bg-white/5 border-b border-[rgba(192,132,252,0.3)] focus:border-[var(--neon-purple)] outline-none px-3 py-2 rounded-t-md text-sm w-1/3"
            style={{ colorScheme: "dark" }}
          />
          <input
            type="text"
            placeholder="Subject Name"
            className="flex-1 bg-white/5 border-b border-[rgba(192,132,252,0.3)] focus:border-[var(--neon-purple)] outline-none px-3 py-2 rounded-t-md text-sm"
          />
        </div>

        {/* Middle Content */}
          <div className="flex gap-4 p-4 border-b border-[rgba(192,132,252,0.2)]">
            <input
              type="text"
              placeholder="Full Path to Excel File (e.g. C:\Data\students.xlsx)"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
              className="flex-1 bg-white/5 border-b border-[rgba(192,132,252,0.3)] focus:border-[var(--neon-purple)] outline-none px-3 py-2 rounded-t-md text-sm"
            />
            <button
              onClick={handleLoad}
              disabled={isLoading}
              className="bg-[var(--neon-purple)]/20 border border-[var(--neon-purple)] text-[var(--neon-purple)] px-4 py-1 rounded-md text-sm hover:bg-[var(--neon-purple)]/40 transition-all disabled:opacity-50"
            >
              Load
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
            {students.length === 0 ? (
              <div className="border-2 border-dashed border-[rgba(192,132,252,0.4)] rounded-xl p-6 flex flex-col items-center justify-center text-[var(--color-text-dim)]">
                <UploadCloud className="w-8 h-8 mb-2 opacity-70" />
                <span className="text-sm">Enter file path above and click Load</span>
              </div>
            ) : null}

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {students.map((st) => (
              <button
                key={st.id}
                onClick={() => toggleAttendance(st.id)}
                className={clsx(
                  "p-3 rounded-lg border text-left transition-all",
                  st.present
                    ? "bg-green-500/10 border-green-500/30 shadow-[0_0_10px_rgba(34,197,94,0.1)]"
                    : "bg-rose-500/10 border-rose-500/30 shadow-[0_0_10px_rgba(244,63,94,0.1)]"
                )}
              >
                <div className={clsx("font-mono text-xs mb-1", st.present ? "text-green-300" : "text-rose-300")}>
                  #{st.id}
                </div>
                <div className={clsx("font-semibold text-sm", !st.present && "text-rose-200")}>
                  {st.name}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="p-4 bg-black/20">
          <button
            onClick={handleSave}
            disabled={isLoading || students.length === 0}
            className="w-full flex justify-center items-center gap-2 bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-pink)] py-3 rounded-md font-bold text-white hover:shadow-[0_0_15px_var(--neon-purple)] transition-all disabled:opacity-50"
          >
            <Save className="w-4 h-4" /> Save Attendance
          </button>
        </div>
      </div>
    </Window>
  );
}

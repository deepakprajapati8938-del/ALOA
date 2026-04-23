import BootScreen from "@/components/os/BootScreen";
import Taskbar from "@/components/os/Taskbar";
import CommandLog from "@/components/os/CommandLog";
import AppManager from "@/components/apps/AppManager";
import SystemDoctor from "@/components/apps/SystemDoctor";
import Attendance from "@/components/apps/Attendance";
import LectureNotes from "@/components/apps/LectureNotes";
import AloaRadar from "@/components/apps/AloaRadar";
import Terminal from "@/components/apps/Terminal";
import ExamPilot from "@/components/apps/ExamPilot";
import CodeHealer from "@/components/apps/CodeHealer";
import CloudHealer from "@/components/apps/CloudHealer";
import AutoDeployer from "@/components/apps/AutoDeployer";
import ResumeEngine from "@/components/apps/ResumeEngine";
import AuroraWake from "@/components/shared/AuroraWake";

export default function Home() {
  return (
    <main className="relative w-full h-screen overflow-hidden text-white">
      {/* L1 - Background Video Layer */}
      <video
        autoPlay
        loop
        muted
        playsInline
        className="fixed inset-0 w-full h-full object-cover z-0"
        src="/background.mp4"
      />
      {/* Video Overlay */}
      <div className="fixed inset-0 bg-[rgba(10,5,20,0.65)] z-[1]" />

      {/* Global CRT Scanlines */}
      <div className="scanlines" />

      <AuroraWake />

      {/* Boot Screen Overlay */}
      <BootScreen />

      {/* L2 - Desktop Surface (Windows Render Here) */}
      <div className="fixed inset-0 z-10 w-full h-[calc(100vh-56px)] bg-[linear-gradient(rgba(192,132,252,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(192,132,252,0.04)_1px,transparent_1px)] bg-[size:40px_40px]">

        {/* Feature 1–5 (original) */}
        <AppManager />
        <SystemDoctor />
        <Attendance />
        <LectureNotes />
        <AloaRadar />
        <Terminal />

        {/* Feature 5–10 (new) */}
        <ExamPilot />
        <CodeHealer />
        <CloudHealer />
        <AutoDeployer />
        <ResumeEngine />

      </div>

      {/* L3 - System Bar */}
      <CommandLog />
      <Taskbar />
    </main>
  );
}

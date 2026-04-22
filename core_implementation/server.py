import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from features.feature_1.core import command_chain as app_manager_chain, execute_command, launch_app
from features.feature_2.core import get_detailed_system_stats, kill_specific_process, audit_junk_files, execute_cleanup
from features.feature_3.core import load_and_view_data, process_absentees, save_final_attendance
from features.feature_4.core import get_video_id, fetch_transcript, generate_structured_notes, save_notes_to_file
from features.feature_10.core import build_brief, load_watchlist, DEFAULT_WATCHLIST
from features.feature_5.core import capture_screen as capture_quiz_screen, get_ai_answer as solve_quiz # Keep just in case

app = FastAPI(title="ALOA OS Backend API")

# Setup CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- APP MANAGER ROUTES ---
class AppManagerRequest(BaseModel):
    user_input: str

class AppManagerResponse(BaseModel):
    command: str

@app.post("/api/app-manager/generate", response_model=AppManagerResponse)
async def generate_app_command(req: AppManagerRequest):
    try:
        raw_cmd = app_manager_chain.invoke({"input": req.user_input})
        final_cmd = raw_cmd.strip().replace("```bash", "").replace("```powershell", "").replace("```", "").strip()
        return AppManagerResponse(command=final_cmd)
    except RuntimeError as e:
        if "missing" in str(e).lower():
            # Fallback for demonstration when no API keys are provided
            mock_cmd = f"start {req.user_input.split()[-1]}"
            if "install" in req.user_input.lower() or "download" in req.user_input.lower():
                mock_cmd = f'winget install "{req.user_input.split()[-1]}" -e --silent'
            return AppManagerResponse(command=mock_cmd)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ExecuteRequest(BaseModel):
    command: str

@app.post("/api/app-manager/execute")
async def execute_app_command(req: ExecuteRequest):
    try:
        # Avoid user confirmation popups (Tkinter) by directly executing
        execute_command(req.command)
        return {"status": "success", "message": "Command executed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- SYSTEM DOCTOR ROUTES ---
@app.get("/api/system-doctor/stats")
async def get_system_stats():
    try:
        stats = get_detailed_system_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class KillProcessRequest(BaseModel):
    process_name: str

@app.post("/api/system-doctor/kill")
async def kill_process(req: KillProcessRequest):
    try:
        result = kill_specific_process(req.process_name)
        return {"status": "success", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/system-doctor/clean")
async def clean_junk():
    try:
        result = execute_cleanup()
        return {"status": "success", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ATTENDANCE ROUTES ---
class AttendanceLoadRequest(BaseModel):
    file_path: str

@app.post("/api/attendance/load")
async def load_attendance(req: AttendanceLoadRequest):
    try:
        students, message = load_and_view_data(req.file_path)
        if students is None:
            raise HTTPException(status_code=400, detail=message)
        return {"students": students, "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AttendanceMarkRequest(BaseModel):
    absent_inputs: str
    date: str

@app.post("/api/attendance/mark")
async def mark_attendance(req: AttendanceMarkRequest):
    try:
        absent_names, absent_indices, not_found = process_absentees(req.absent_inputs)
        result = save_final_attendance(absent_indices, req.date)
        return {
            "status": "success",
            "message": result,
            "absent_names": absent_names,
            "not_found": not_found
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- LECTURE NOTES ROUTES ---
class LectureNotesRequest(BaseModel):
    url: str

@app.post("/api/lecture-notes/generate")
async def generate_lecture_notes(req: LectureNotesRequest):
    try:
        video_id = get_video_id(req.url)
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        
        transcript = fetch_transcript(video_id)
        if transcript.startswith("ERROR:"):
            raise HTTPException(status_code=400, detail=transcript)
            
        notes = generate_structured_notes(transcript)
        if notes == "NOT_EDUCATIONAL":
            return {"status": "skipped", "message": "Video is not educational"}
            
        title = f"Lecture_Notes_{video_id}"
        md_file, pdf_file, status = save_notes_to_file(title, notes)
        
        return {
            "status": "success",
            "notes": notes,
            "md_file": md_file,
            "pdf_file": pdf_file
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ALOA RADAR ROUTES ---
class RadarScanRequest(BaseModel):
    force_refresh: bool = False

@app.post("/api/aloa-radar/scan")
async def scan_radar(req: RadarScanRequest = RadarScanRequest()):
    try:
        watchlist = load_watchlist() or DEFAULT_WATCHLIST
        brief = build_brief(watchlist, force_refresh=req.force_refresh)
        return {
            "status": "success",
            "brief": brief,
            "answer": brief.get("report") # Map to the same field name used in the frontend for compatibility
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

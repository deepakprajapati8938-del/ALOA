import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# ADD: Centralized cache
from utils.cache import api_cache, DYNAMIC, SEMI_STATIC, STATIC, content_hash

# ADD: Semantic Memory
from utils.memory import aloa_memory

# ADD: Llama.cpp Integrations
from optimized_llama import optimized_llama
from llama_cli_integration import llama_cli
from llama_integration import llama_aloa
from performance_config import performance_config, performance_monitor

from features.feature_1.core import command_chain as app_manager_chain, execute_command, launch_app
from features.feature_2.core import get_detailed_system_stats, kill_specific_process, audit_junk_files, execute_cleanup
from features.feature_3.core import load_and_view_data, process_absentees, save_final_attendance
from features.feature_4.core import get_video_id, fetch_transcript, generate_structured_notes, save_notes_to_file
from features.feature_10.core import build_brief, load_watchlist, DEFAULT_WATCHLIST
from features.feature_5.core import get_ai_answer as solve_quiz
from features.feature_6.core import ALOAAgent, scan_source_files, detect_project_type, auto_detect_run_command
from features.feature_7.core import CloudHealerAgent, setup_cloud_workspace
from features.feature_8.core import detect_deployment_plan, init_and_push_to_github, deploy_to_vercel
from features.feature_9.core import extract_profile_from_text, generate_resume_html, analyze_ats, list_profiles

import tempfile

# ── Stateful sessions (in-memory, per-process) ────────────────────────────────
_code_healer_sessions: dict = {}
_cloud_healer_session: dict = {}   # single shared session

app = FastAPI(title="ALOA OS Backend API")

# Setup CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _http_error(e: Exception) -> HTTPException:
    """Map common errors to correct HTTP status codes."""
    msg = str(e).lower()
    if "invalid" in msg or "missing" in msg or "not found" in msg:
        return HTTPException(status_code=400, detail=str(e))
    if "api" in msg or "groq" in msg or "openrouter" in msg or "gemini" in msg:
        return HTTPException(status_code=502, detail=f"LLM upstream error: {e}")
    return HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """
    Pings each feature's dependency. The frontend can use this
    to show which features are available before the user clicks.
    """
    import psutil  # noqa: F401

    status = {
        "groq":        bool(os.getenv("GROQ_API_KEY")),
        "openrouter":  bool(os.getenv("OPENROUTER_API_KEY")),
        "gemini":      bool(os.getenv("GEMINI_API_KEY_1")),
        "psutil":      True,
        "features": {
            "app_manager":   bool(os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY")),
            "system_doctor": True,
            "attendance":    True,
            "lecture_notes": bool(os.getenv("GEMINI_API_KEY_1")),
            "aloa_radar":    bool(os.getenv("GROQ_API_KEY")),
            "exam_pilot":    bool(os.getenv("GEMINI_API_KEY_F5_1") or os.getenv("GEMINI_API_KEY_1")),
            "code_healer":   bool(os.getenv("GEMINI_API_KEY_1") or os.getenv("OPENROUTER_API_KEY")),
            "cloud_healer":  bool(os.getenv("OPENROUTER_API_KEY")),
            "auto_deployer": bool(os.getenv("OPENROUTER_API_KEY")),
            "resume_engine": bool(os.getenv("GEMINI_API_KEY_1") or os.getenv("OPENROUTER_API_KEY")),
        }
    }
    return status

# ─────────────────────────────────────────────
# KNOWLEDGE GRAPH (MEMORY) API
# ─────────────────────────────────────────────
@app.get("/api/memory/query")
async def memory_query(q: Optional[str] = None):
    """Query the semantic memory graph. If no query, returns all facts."""
    try:
        if q:
            facts = aloa_memory.query_related(q)
        else:
            # Return a generic dump of the most common nodes for frontend viewing
            facts = aloa_memory.query_related("User") + aloa_memory.query_related("ALOA")
        return {"status": "success", "facts": list(set(facts))}
    except Exception as e:
        raise _http_error(e)

@app.post("/api/memory/clear")
async def memory_clear():
    """Wipes the semantic memory graph."""
    try:
        import networkx as nx
        aloa_memory.graph = nx.MultiDiGraph()
        aloa_memory.save()
        return {"status": "success", "message": "Memory wiped."}
    except Exception as e:
        raise _http_error(e)


# ─────────────────────────────────────────────
# FEATURE 1 — APP MANAGER
# ─────────────────────────────────────────────
class AppManagerRequest(BaseModel):
    user_input: str

class AppManagerResponse(BaseModel):
    command: str

@app.post("/api/app-manager/generate", response_model=AppManagerResponse)
async def generate_app_command(req: AppManagerRequest):
    cache_key = f"app_manager:{content_hash(req.user_input)}"
    cached = api_cache.get(cache_key)
    if cached is not None:
        return AppManagerResponse(command=cached)
    try:
        raw_cmd = app_manager_chain.invoke({"input": req.user_input})
        final_cmd = raw_cmd.strip().replace("```bash", "").replace("```powershell", "").replace("```", "").strip()
        api_cache.set(cache_key, final_cmd, DYNAMIC)
        return AppManagerResponse(command=final_cmd)
    except RuntimeError as e:
        if "missing" in str(e).lower():
            mock_cmd = f"start {req.user_input.split()[-1]}"
            if "install" in req.user_input.lower() or "download" in req.user_input.lower():
                mock_cmd = f'winget install "{req.user_input.split()[-1]}" -e --silent'
            return AppManagerResponse(command=mock_cmd)
        raise _http_error(e)
    except Exception as e:
        raise _http_error(e)

class ExecuteRequest(BaseModel):
    command: str

@app.post("/api/app-manager/execute")
async def execute_app_command(req: ExecuteRequest):
    try:
        execute_command(req.command)
        return {"status": "success", "message": "Command executed successfully"}
    except Exception as e:
        raise _http_error(e)


# ─────────────────────────────────────────────
# FEATURE 2 — SYSTEM DOCTOR
# ─────────────────────────────────────────────
@app.get("/api/system-doctor/stats")
async def get_system_stats():
    cache_key = "system_doctor:stats"
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        stats = get_detailed_system_stats()
        api_cache.set(cache_key, stats, DYNAMIC)
        return stats
    except Exception as e:
        raise _http_error(e)

class KillProcessRequest(BaseModel):
    process_name: str

@app.post("/api/system-doctor/kill")
async def kill_process(req: KillProcessRequest):
    try:
        result = kill_specific_process(req.process_name)
        return {"status": "success", "message": result}
    except Exception as e:
        raise _http_error(e)

@app.post("/api/system-doctor/clean")
async def clean_junk():
    try:
        result = execute_cleanup()
        return {"status": "success", "message": result}
    except Exception as e:
        raise _http_error(e)


# ─────────────────────────────────────────────
# FEATURE 3 — ATTENDANCE
# ─────────────────────────────────────────────
class AttendanceLoadRequest(BaseModel):
    file_path: str

@app.post("/api/attendance/load")
async def load_attendance(req: AttendanceLoadRequest):
    try:
        students, message = load_and_view_data(req.file_path)
        if students is None:
            raise HTTPException(status_code=400, detail=message)
        return {"students": students, "message": message}
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)

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
        raise _http_error(e)


# ─────────────────────────────────────────────
# FEATURE 4 — LECTURE NOTES
# ─────────────────────────────────────────────
class LectureNotesRequest(BaseModel):
    url: str

@app.post("/api/lecture-notes/generate")
async def generate_lecture_notes(req: LectureNotesRequest):
    cache_key = f"lecture_notes:{content_hash(req.url)}"
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached
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

        result = {
            "status": "success",
            "notes": notes,
            "md_file": md_file,
            "pdf_file": pdf_file
        }
        api_cache.set(cache_key, result, STATIC)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)


# ─────────────────────────────────────────────
# FEATURE 5 — EXAM PILOT
# ─────────────────────────────────────────────
class ExamAnswerRequest(BaseModel):
    context_text: str

@app.post("/api/exam-pilot/answer")
async def exam_pilot_answer(req: ExamAnswerRequest):
    """Solve a quiz question from OCR-extracted text."""
    cache_key = f"exam_pilot:{content_hash(req.context_text)}"
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        result = solve_quiz(req.context_text)
        response_data = {"status": "success", "answer": result}
        api_cache.set(cache_key, response_data, SEMI_STATIC)
        return response_data
    except Exception as e:
        raise _http_error(e)


# ─────────────────────────────────────────────
# FEATURE 6 — CODE HEALER
# ─────────────────────────────────────────────
class CodeHealerInitRequest(BaseModel):
    folder_path: str

class CodeHealerChatRequest(BaseModel):
    folder_path: str
    message: str

class CodeHealerApplyRequest(BaseModel):
    folder_path: str

@app.post("/api/code-healer/init")
async def code_healer_init(req: CodeHealerInitRequest):
    """Scan a project folder and create a Code Healer session."""
    try:
        fp = req.folder_path
        if not os.path.isdir(fp):
            raise HTTPException(status_code=400, detail=f"Folder not found: {fp}")
        source_files = scan_source_files(fp)
        proj_type, default_run_cmd = detect_project_type(fp)
        run_cmd, _ = auto_detect_run_command(fp, source_files, proj_type, default_run_cmd)
        agent = ALOAAgent(fp, source_files, proj_type, run_cmd or "")
        _code_healer_sessions[fp] = agent
        return {
            "status": "success",
            "project_type": proj_type,
            "run_command": run_cmd,
            "file_count": len(source_files),
            "files": [os.path.relpath(f, fp) for f in source_files[:50]],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)

@app.post("/api/code-healer/chat")
async def code_healer_chat(req: CodeHealerChatRequest):
    """Send a message to the Code Healer agent."""
    try:
        agent = _code_healer_sessions.get(req.folder_path)
        if not agent:
            raise HTTPException(status_code=400, detail="No active session. Call /init first.")
        response = agent.send_message(req.message, purpose="chat")
        fix_file, _ = agent.parse_fix_from_response(response)
        return {
            "status": "success",
            "response": response,
            "has_fix": fix_file is not None,
            "fix_file": fix_file,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)

@app.post("/api/code-healer/apply")
async def code_healer_apply(req: CodeHealerApplyRequest):
    """Apply the last suggested fix."""
    try:
        agent = _code_healer_sessions.get(req.folder_path)
        if not agent:
            raise HTTPException(status_code=400, detail="No active session.")
        success, message = agent.apply_fix()
        return {"status": "success" if success else "error", "message": message}
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)


# ─────────────────────────────────────────────
# FEATURE 7 — CLOUD HEALER
# ─────────────────────────────────────────────
class CloudHealerCloneRequest(BaseModel):
    repo_url: str
    pat: str

class CloudHealerChatRequest(BaseModel):
    message: str

class CloudHealerPushRequest(BaseModel):
    commit_message: str = "ALOA Cloud Healer: Applied fix"

@app.post("/api/cloud-healer/clone")
async def cloud_healer_clone(req: CloudHealerCloneRequest):
    """Clone a GitHub repo and initialize a Cloud Healer session."""
    try:
        dest = os.path.join(tempfile.gettempdir(), "aloa_cloud_workspace")
        success, msg = setup_cloud_workspace(req.repo_url, req.pat, dest)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        agent = CloudHealerAgent(dest)
        _cloud_healer_session["agent"] = agent
        _cloud_healer_session["dest"] = dest
        return {
            "status": "success",
            "message": msg,
            "file_tree": agent.file_tree,
            "file_count": len(agent.source_files),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)

@app.post("/api/cloud-healer/chat")
async def cloud_healer_chat(req: CloudHealerChatRequest):
    """Send a message to the Cloud Healer agent."""
    try:
        agent = _cloud_healer_session.get("agent")
        if not agent:
            raise HTTPException(status_code=400, detail="No active session. Clone a repo first.")
        ai_text, has_changes = agent.chat(req.message)
        return {
            "status": "success",
            "response": ai_text,
            "has_changes": has_changes,
            "pending_file": agent.get_pending_file(),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)

@app.post("/api/cloud-healer/apply")
async def cloud_healer_apply():
    """Apply pending changes from the Cloud Healer agent."""
    try:
        agent = _cloud_healer_session.get("agent")
        if not agent:
            raise HTTPException(status_code=400, detail="No active session.")
        success, message = agent.apply_pending_changes()
        return {"status": "success" if success else "error", "message": message}
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)

@app.post("/api/cloud-healer/push")
async def cloud_healer_push(req: CloudHealerPushRequest):
    """Push fixes to GitHub."""
    try:
        from features.feature_7.core import push_to_cloud
        dest = _cloud_healer_session.get("dest")
        if not dest:
            raise HTTPException(status_code=400, detail="No active session.")
        success, msg = push_to_cloud(dest, req.commit_message)
        return {"status": "success" if success else "error", "message": msg}
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)


# ─────────────────────────────────────────────
# FEATURE 8 — AUTO DEPLOYER
# ─────────────────────────────────────────────
class DeployerAnalyzeRequest(BaseModel):
    folder_path: str

class DeployerDeployRequest(BaseModel):
    folder_path: str
    github_pat: str
    vercel_token: Optional[str] = ""
    render_api_key: Optional[str] = ""
    is_private: bool = False

@app.post("/api/deployer/analyze")
async def deployer_analyze(req: DeployerAnalyzeRequest):
    """Detect the project framework and suggest a deployment plan."""
    try:
        if not os.path.isdir(req.folder_path):
            raise HTTPException(status_code=400, detail=f"Folder not found: {req.folder_path}")
        plan = detect_deployment_plan(req.folder_path)
        return {
            "status": "success",
            "framework": plan.framework,
            "framework_display": plan.framework_display,
            "deploy_target": plan.deploy_target,
            "build_command": plan.build_command,
            "start_command": plan.start_command,
            "project_name": plan.project_name,
            "is_fullstack": plan.is_fullstack,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)

@app.post("/api/deployer/deploy")
async def deployer_deploy(req: DeployerDeployRequest):
    """Run the full deploy pipeline: GitHub push → Vercel/Render deploy."""
    try:
        if not os.path.isdir(req.folder_path):
            raise HTTPException(status_code=400, detail=f"Folder not found: {req.folder_path}")
        plan = detect_deployment_plan(req.folder_path)
        results = []

        gh_result = init_and_push_to_github(
            req.folder_path, req.github_pat, plan.project_name, req.is_private
        )
        results.append({
            "platform": "github", "success": gh_result.success,
            "url": gh_result.url, "message": gh_result.message, "error": gh_result.error
        })

        if not gh_result.success:
            return {"status": "partial", "results": results}

        if plan.deploy_target in ("vercel", "both") and req.vercel_token:
            vr = deploy_to_vercel(req.folder_path, req.vercel_token,
                                   plan.project_name, plan.framework, gh_result.url)
            results.append({
                "platform": "vercel", "success": vr.success,
                "url": vr.url, "message": vr.message, "error": vr.error
            })

        if plan.deploy_target in ("render", "both") and req.render_api_key:
            try:
                from features.feature_8.core import deploy_to_render as _render
                rr = _render(req.folder_path, req.render_api_key,
                              plan.project_name, plan.start_command, plan.build_command)
                results.append({
                    "platform": "render", "success": rr.success,
                    "url": rr.url, "message": rr.message, "error": rr.error
                })
            except (ImportError, AttributeError) as ie:
                results.append({
                    "platform": "render", "success": False,
                    "url": "", "message": str(ie), "error": str(ie)
                })

        all_ok = all(r["success"] for r in results)
        return {"status": "success" if all_ok else "partial", "results": results}
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)


# ─────────────────────────────────────────────
# FEATURE 9 — RESUME ENGINE
# ─────────────────────────────────────────────
class ResumeExtractRequest(BaseModel):
    raw_text: str

class ResumeGenerateRequest(BaseModel):
    profile: Dict[str, Any]
    template: str = "ats_classic"

class ResumeAnalyzeRequest(BaseModel):
    profile: Dict[str, Any]
    job_description: str

@app.post("/api/resume/extract")
async def resume_extract(req: ResumeExtractRequest):
    """Extract a structured profile from raw text."""
    cache_key = f"resume_extract:{content_hash(req.raw_text)}"
    cached = api_cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        profile = extract_profile_from_text(req.raw_text)
        if not profile:
            raise HTTPException(status_code=422, detail="Could not extract profile.")
        
        response_data = {"status": "success", "profile": profile}
        api_cache.set(cache_key, response_data, SEMI_STATIC)
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)

@app.post("/api/resume/generate")
async def resume_generate(req: ResumeGenerateRequest):
    """Generate a resume HTML from a profile dict."""
    try:
        html = generate_resume_html(req.profile, req.template)
        return {"status": "success", "html": html}
    except Exception as e:
        raise _http_error(e)

@app.post("/api/resume/analyze")
async def resume_analyze(req: ResumeAnalyzeRequest):
    """Run ATS analysis against a job description."""
    try:
        result = analyze_ats(req.profile, req.job_description)
        if "error" in result:
            raise HTTPException(status_code=502, detail=result["error"])
        return {"status": "success", "analysis": result}
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)

@app.get("/api/resume/profiles")
async def resume_list_profiles():
    """List saved resume profiles."""
    try:
        return {"status": "success", "profiles": list_profiles()}
    except Exception as e:
        raise _http_error(e)


# ─────────────────────────────────────────────
# FEATURE 10 — ALOA RADAR
# ─────────────────────────────────────────────
class RadarScanRequest(BaseModel):
    force_refresh: bool = False

@app.post("/api/aloa-radar/scan")
async def scan_radar(req: RadarScanRequest = RadarScanRequest()):
    cache_key = "radar:brief"
    if not req.force_refresh:
        cached = api_cache.get(cache_key)
        if cached is not None:
            return cached
    try:
        watchlist = load_watchlist() or DEFAULT_WATCHLIST
        brief = build_brief(watchlist, force_refresh=req.force_refresh)
        result = {
            "status": "success",
            "brief": brief,
            "answer": brief.get("report")
        }
        api_cache.set(cache_key, result, SEMI_STATIC)
        return result
    except Exception as e:
        raise _http_error(e)


# ─────────────────────────────────────────────
# LLAMA.CPP LOCAL AI INTEGRATION
# ─────────────────────────────────────────────
class LlamaGenerateRequest(BaseModel):
    prompt: str
    session_id: str = "default"
    task: str = "general"
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    repeat_penalty: float = 1.1

_working_memory: dict = {}

@app.post("/api/llama/generate")
async def llama_generate(req: LlamaGenerateRequest):
    try:
        # Check API Cache
        cache_key = f"llama_generate:{content_hash(req.prompt + req.session_id + req.task)}"
        cached = api_cache.get(cache_key)
        if cached:
            return cached

        # 1. Semantic Memory Injection
        semantic_context = aloa_memory.get_semantic_context(req.prompt)
        
        # 2. Working Memory Injection
        session_history = _working_memory.get(req.session_id, [])
        history_text = "\n".join(session_history[-5:]) if session_history else ""
        
        # 3. Construct Context-Aware Prompt
        final_prompt = req.prompt
        if semantic_context or history_text:
            context_blocks = []
            if semantic_context:
                context_blocks.append(semantic_context)
            if history_text:
                context_blocks.append(f"[Recent Conversation]:\n{history_text}")
            
            final_prompt = "\n\n".join(context_blocks) + f"\n\nUser: {req.prompt}"

        result = None
        provider = None
        
        # Try native integration first
        if optimized_llama.model_config:
            result = optimized_llama.generate_optimized(
                prompt=final_prompt,
                task=req.task,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                repeat_penalty=req.repeat_penalty
            )
            provider = "native"
            
        if not result or result.startswith("Error"):
            # Fallback to CLI
            result = llama_cli.generate(
                prompt=final_prompt,
                max_tokens=req.max_tokens,
                temperature=req.temperature
            )
            provider = "cli"
            
        # 4. Update Working Memory
        session_history.append(f"User: {req.prompt}")
        session_history.append(f"ALOA: {result}")
        _working_memory[req.session_id] = session_history[-10:] # keep last 5 pairs
        
        response_data = {"status": "success", "response": result, "provider": provider}
        
        # Cache identical requests for 60s
        api_cache.set(cache_key, response_data, 60)
        
        return response_data
    except Exception as e:
        raise _http_error(e)

@app.post("/api/llama/stream")
async def llama_stream(req: LlamaGenerateRequest):
    from fastapi.responses import StreamingResponse
    try:
        semantic_context = aloa_memory.get_semantic_context(req.prompt)
        session_history = _working_memory.get(req.session_id, [])
        history_text = "\n".join(session_history[-5:]) if session_history else ""
        
        final_prompt = req.prompt
        if semantic_context or history_text:
            context_blocks = []
            if semantic_context:
                context_blocks.append(semantic_context)
            if history_text:
                context_blocks.append(f"[Recent Conversation]:\n{history_text}")
            final_prompt = "\n\n".join(context_blocks) + f"\n\nUser: {req.prompt}"

        # We use the optimized llama for streaming
        def generate():
            full_response = ""
            for chunk in optimized_llama.generate_stream_optimized(
                prompt=final_prompt,
                task=req.task,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                top_p=req.top_p,
                repeat_penalty=req.repeat_penalty
            ):
                full_response += chunk
                yield chunk
                
            # Update Working Memory after stream finishes
            if full_response and not full_response.startswith("Error"):
                session_history.append(f"User: {req.prompt}")
                session_history.append(f"ALOA: {full_response}")
                _working_memory[req.session_id] = session_history[-10:]
                
        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        raise _http_error(e)

class ModelManageRequest(BaseModel):
    action: str  # load, unload
    model_name: str = "gemma-2b"

@app.post("/api/llama/models/manage")
async def llama_manage_models(req: ModelManageRequest):
    try:
        if req.action == "load":
            success = optimized_llama.load_model_async(req.model_name)
            return {"status": "success" if success else "error", "message": f"Model {req.model_name} load status: {success}"}
        elif req.action == "unload":
            optimized_llama.unload_model()
            return {"status": "success", "message": "Model unloaded"}
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    except Exception as e:
        raise _http_error(e)

@app.get("/api/performance/stats")
async def performance_stats():
    try:
        stats = optimized_llama.get_performance_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        raise _http_error(e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

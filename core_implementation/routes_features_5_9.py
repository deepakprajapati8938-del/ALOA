
# ─────────────────────────────────────────────
# FEATURE 5 — EXAM PILOT
# ─────────────────────────────────────────────
class ExamAnswerRequest(BaseModel):
    context_text: str

@app.post("/api/exam-pilot/answer")
async def exam_pilot_answer(req: ExamAnswerRequest):
    try:
        result = solve_quiz(req.context_text)
        return {"status": "success", "answer": result}
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
    try:
        fp = req.folder_path
        if not os.path.isdir(fp):
            raise HTTPException(status_code=400, detail=f"Folder not found: {fp}")
        source_files = scan_source_files(fp)
        proj_type, default_run_cmd = detect_project_type(fp)
        run_cmd, _ = auto_detect_run_command(fp, source_files, proj_type, default_run_cmd)
        agent = ALOAAgent(fp, source_files, proj_type, run_cmd)
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

def _deploy_to_render_shim(folder_path, api_key, project_name, start_cmd, build_cmd):
    try:
        from features.feature_8.core import deploy_to_render as _render
        return _render(folder_path, api_key, project_name, start_cmd, build_cmd)
    except (ImportError, AttributeError):
        from features.feature_8.core import DeployResult
        return DeployResult(success=False, platform="render",
                            error="deploy_to_render not available in this build.")

@app.post("/api/deployer/analyze")
async def deployer_analyze(req: DeployerAnalyzeRequest):
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
    try:
        if not os.path.isdir(req.folder_path):
            raise HTTPException(status_code=400, detail=f"Folder not found: {req.folder_path}")
        plan = detect_deployment_plan(req.folder_path)
        results = []
        gh_result = init_and_push_to_github(
            req.folder_path, req.github_pat, plan.project_name, req.is_private
        )
        results.append({"platform": "github", "success": gh_result.success,
                         "url": gh_result.url, "message": gh_result.message,
                         "error": gh_result.error})
        if not gh_result.success:
            return {"status": "partial", "results": results}
        if plan.deploy_target in ("vercel", "both") and req.vercel_token:
            vr = deploy_to_vercel(req.folder_path, req.vercel_token,
                                   plan.project_name, plan.framework, gh_result.url)
            results.append({"platform": "vercel", "success": vr.success,
                             "url": vr.url, "message": vr.message, "error": vr.error})
        if plan.deploy_target in ("render", "both") and req.render_api_key:
            rr = _deploy_to_render_shim(req.folder_path, req.render_api_key,
                                         plan.project_name, plan.start_command, plan.build_command)
            results.append({"platform": "render", "success": rr.success,
                             "url": rr.url, "message": rr.message, "error": rr.error})
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
    try:
        profile = extract_profile_from_text(req.raw_text)
        if not profile:
            raise HTTPException(status_code=422, detail="Could not extract profile.")
        return {"status": "success", "profile": profile}
    except HTTPException:
        raise
    except Exception as e:
        raise _http_error(e)

@app.post("/api/resume/generate")
async def resume_generate(req: ResumeGenerateRequest):
    try:
        html = generate_resume_html(req.profile, req.template)
        return {"status": "success", "html": html}
    except Exception as e:
        raise _http_error(e)

@app.post("/api/resume/analyze")
async def resume_analyze(req: ResumeAnalyzeRequest):
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
    try:
        return {"status": "success", "profiles": list_profiles()}
    except Exception as e:
        raise _http_error(e)

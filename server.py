import json
import logging
import threading
from pathlib import Path, PurePosixPath

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool

from context import CONTEXT_FILE
from skill_library import SKILLS_ROOT, list_available_skills, read_skill_content


ROOT = Path(__file__).resolve().parent
APPS_ROOT = ROOT / "apps"
task_lock = threading.Lock()
templates = Jinja2Templates(directory=str(ROOT / "templates"))
main = FastAPI(title="Dev Agent", version="1.0.0")
main.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
logger = logging.getLogger(__name__)


def _get_db():
    from mongodb import DBOps

    return DBOps()


def _known_apps():
    contents = CONTEXT_FILE.read_text(encoding="utf-8") if CONTEXT_FILE.exists() else ""
    data = json.loads(contents) if contents.strip() else {"apps": []}
    apps = {}

    for entry in data.get("apps", []):
        for app_name, app_data in entry.items():
            apps[app_name] = {
                "name": app_name,
                "files": app_data.get("files", []),
                "context": app_data.get("context", []),
            }

    return sorted(apps.values(), key=lambda app: app["name"].casefold())


def _safe_parts(file_name):
    path = PurePosixPath(str(file_name).replace("\\", "/"))
    if (
        path.is_absolute()
        or not path.parts
        or path.parts[0].endswith(":")
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise ValueError(f"Invalid app file path: {file_name}")
    return path.parts


def _build_tree(file_names):
    root = {"name": "", "type": "directory", "children": {}}
    for file_name in sorted(set(file_names), key=str.casefold):
        parts = _safe_parts(file_name)
        node = root
        for index, part in enumerate(parts):
            is_file = index == len(parts) - 1
            node = node["children"].setdefault(
                part,
                {
                    "name": part,
                    "path": "/".join(parts[:index + 1]),
                    "type": "file" if is_file else "directory",
                    "children": {},
                },
            )
            if not is_file:
                node["type"] = "directory"
    return root["children"]


def _public_tree(nodes):
    result = []
    for node in sorted(nodes.values(), key=lambda item: (item["type"] != "directory", item["name"].casefold())):
        item = {"name": node["name"], "type": node["type"]}
        if node["type"] == "directory":
            item["children"] = _public_tree(node["children"])
        else:
            item["path"] = node["path"]
        result.append(item)
    return result


def _skill_summary(content):
    body = content
    if body.startswith("---"):
        _, _, body = body.partition("---")
        _, _, body = body.partition("---")

    paragraphs = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("```"):
            if paragraphs:
                break
            continue
        paragraphs.append(line)
    return " ".join(paragraphs) or "No description available."


def _skill_entry(path):
    content = read_skill_content(path)
    title = path.stem
    if title.endswith("_skill"):
        title = title[:-6]
    filename = path.relative_to(SKILLS_ROOT).as_posix()
    return {
        "filename": filename,
        "path": filename,
        "title": title.replace("_", " ").replace("-", " ").title(),
        "description": _skill_summary(content),
        "content": content,
    }


def _skill_path(filename):
    try:
        parts = _safe_parts(filename)
    except ValueError:
        return None
    if not filename.endswith(".md") or parts[-1] == "skill_template.md":
        return None
    path = SKILLS_ROOT.joinpath(*parts)
    try:
        resolved_path = path.resolve(strict=True)
        resolved_path.relative_to(SKILLS_ROOT.resolve())
    except (OSError, ValueError):
        return None
    return resolved_path if resolved_path.is_file() else None


@main.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@main.get("/projects/{app_name}")
async def project_page(request: Request, app_name: str):
    try:
        app_data = next((app for app in _known_apps() if app["name"] == app_name), None)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        logger.exception("Unable to load project %s", app_name)
        raise HTTPException(status_code=500, detail="Unable to load project metadata.") from error
    if app_data is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return templates.TemplateResponse(
        request=request,
        name="project.html",
        context={"request": request, "project": app_data},
    )


@main.get("/api/agents")
def list_agents():
    agents = _get_db().find_documents({})
    if isinstance(agents, str):
        logger.error("Unable to load agents: %s", agents)
        return JSONResponse({"error": "Unable to load agents from MongoDB."}, status_code=503)

    return [
        {
            "name": item.get("name", ""),
            "action": item.get("action", ""),
            "status": item.get("status", "inactive"),
        }
        for item in agents
    ]


@main.get("/api/skills")
def list_skills():
    try:
        return [
            _skill_entry(SKILLS_ROOT / filename)
            for filename in list_available_skills()
        ]
    except (OSError, UnicodeDecodeError) as error:
        logger.exception("Unable to load skills")
        return JSONResponse(
            {"error": "Unable to load skills. Check the backend logs for details."},
            status_code=500,
        )


@main.get("/api/skills/{filename:path}")
def get_skill(filename: str):
    path = _skill_path(filename)
    if path is None:
        return JSONResponse({"error": "Skill not found."}, status_code=404)
    try:
        return _skill_entry(path)
    except (OSError, UnicodeDecodeError) as error:
        logger.exception("Unable to load skill %s", filename)
        return JSONResponse(
            {"error": "Unable to load this skill. Check the backend logs for details."},
            status_code=500,
        )


def _generate_skill(topic):
    from gemini import generate_skills

    with task_lock:
        return generate_skills(topic)


@main.post("/api/skills")
async def create_skill(request: Request):
    try:
        payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse({"error": "Expected a JSON request body."}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "Expected a JSON request body."}, status_code=400)

    topic = payload.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        return JSONResponse({"error": "Describe the skill you want to add."}, status_code=400)
    if len(topic) > 300:
        return JSONResponse({"error": "Skill topics must be 300 characters or fewer."}, status_code=400)

    try:
        filename = await run_in_threadpool(_generate_skill, topic.strip())
        path = _skill_path(filename)
        if path is None:
            raise RuntimeError("The generated skill file could not be found.")
        return JSONResponse(_skill_entry(path), status_code=201)
    except FileExistsError:
        return JSONResponse(
            {"error": "A skill with a similar topic already exists. Choose a more specific topic."},
            status_code=409,
        )
    except ValueError as error:
        return JSONResponse({"error": str(error)}, status_code=400)
    except Exception:
        logger.exception("Skill generation failed")
        return JSONResponse(
            {"error": "Skill generation failed. Check the backend logs for details."},
            status_code=500,
        )


@main.get("/api/apps")
def list_apps():
    try:
        return _known_apps()
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        logger.exception("Unable to load app metadata")
        return JSONResponse({"error": f"Unable to load app metadata: {error}"}, status_code=500)


@main.get("/api/apps/{app_name}/files")
def app_files(app_name):
    try:
        app_data = next((app for app in _known_apps() if app["name"] == app_name), None)
        if app_data is None:
            return JSONResponse({"error": "App not found."}, status_code=404)
        return {
            "app": app_name,
            "tree": _public_tree(_build_tree(app_data["files"])),
            "file_count": len(app_data["files"]),
        }
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        logger.exception("Unable to load file tree for app %s", app_name)
        return JSONResponse({"error": f"Unable to load app file tree: {error}"}, status_code=500)


def _execute_project_chat(app_name, message, history):
    import agent as agent_runtime

    with task_lock:
        return agent_runtime.run_project_chat(app_name, message, history)


@main.post("/api/apps/{app_name}/chat")
async def project_chat(request: Request, app_name: str):
    try:
        payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse({"error": "Expected a JSON request body."}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "Expected a JSON request body."}, status_code=400)

    message = payload.get("message")
    history = payload.get("history", [])
    if not isinstance(message, str) or not message.strip():
        return JSONResponse({"error": "Enter a message for the project chat."}, status_code=400)
    if len(message) > 5000:
        return JSONResponse({"error": "Messages must be 5,000 characters or fewer."}, status_code=400)
    if not isinstance(history, list) or len(history) > 20:
        return JSONResponse({"error": "Chat history must contain at most 20 messages."}, status_code=400)
    if any(
        not isinstance(item, dict)
        or item.get("role") not in ("user", "assistant")
        or not isinstance(item.get("content"), str)
        for item in history
    ):
        return JSONResponse({"error": "Chat history contains an invalid message."}, status_code=400)
    if any(len(item["content"]) > 5000 for item in history):
        return JSONResponse({"error": "Chat history messages must be 5,000 characters or fewer."}, status_code=400)

    try:
        if not any(app["name"] == app_name for app in _known_apps()):
            return JSONResponse({"error": "Project not found."}, status_code=404)
        reply = await run_in_threadpool(
            _execute_project_chat,
            app_name,
            message.strip(),
            history,
        )
        return {"reply": reply}
    except Exception:
        logger.exception("Project chat failed for %s", app_name)
        return JSONResponse(
            {"error": "Project chat failed. Check the backend logs for details."},
            status_code=500,
        )


@main.get("/api/apps/{app_name}/file/{file_name:path}")
def read_app_file(app_name, file_name):
    try:
        app_data = next((app for app in _known_apps() if app["name"] == app_name), None)
        if app_data is None:
            return JSONResponse({"error": "App not found."}, status_code=404)

        parts = _safe_parts(file_name)
        normalized_name = "/".join(parts)
        known_files = {
            "/".join(_safe_parts(name))
            for name in app_data["files"]
        }
        if normalized_name not in known_files:
            return JSONResponse({"error": "File is not part of this app."}, status_code=404)

        local_file = (APPS_ROOT / app_name).joinpath(*parts).resolve()
        if local_file.is_relative_to(APPS_ROOT.resolve()) and local_file.is_file():
            content = local_file.read_text(encoding="utf-8")
        else:
            from grpc_utils.client import viewFiles

            content = viewFiles(app_name, file_name)
            if content == "Failure":
                return JSONResponse(
                    {"error": "Unable to retrieve this file from the app backend."},
                    status_code=502,
                )

        return {"path": normalized_name, "content": content}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as error:
        logger.exception("Unable to read app file %s/%s", app_name, file_name)
        return JSONResponse({"error": f"Unable to read app file: {error}"}, status_code=500)


def _execute_task(task, mode, agent_name):
    import agent as agent_runtime

    with task_lock:
        if mode == "plan":
            return agent_runtime.run_plan_task(task)

        message = agent_runtime.run_individual_task(task, agent_name=agent_name)
        return {
            "message": message,
            "app": agent_runtime.app_name,
        }


@main.post("/api/tasks")
async def create_task(request: Request):
    try:
        payload = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse({"error": "Expected a JSON request body."}, status_code=400)
    if not isinstance(payload, dict):
        return JSONResponse({"error": "Expected a JSON request body."}, status_code=400)

    task = payload.get("task")
    agent_name = payload.get("agent")
    mode = payload.get("mode", "individual")
    if not isinstance(task, str) or not task.strip():
        return JSONResponse({"error": "Describe the app or task you want to build."}, status_code=400)
    if len(task) > 10000:
        return JSONResponse(
            {"error": "Task descriptions must be 10,000 characters or fewer."},
            status_code=400,
        )
    if mode not in ("plan", "individual"):
        return JSONResponse({"error": "Mode must be 'plan' or 'individual'."}, status_code=400)
    if agent_name is not None and not isinstance(agent_name, str):
        return JSONResponse({"error": "Agent must be a name or null."}, status_code=400)

    try:
        result = await run_in_threadpool(
            _execute_task,
            task.strip(),
            mode,
            agent_name.strip() if agent_name else None,
        )
        return JSONResponse(result, status_code=201)
    except Exception:
        logger.exception("Task execution failed")
        return JSONResponse(
            {"error": "Task execution failed. Check the backend logs for details."},
            status_code=500,
        )


if __name__ == "__main__":
    uvicorn.run(main, host="127.0.0.1", port=5000)

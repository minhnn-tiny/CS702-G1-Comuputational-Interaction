"""HTTP API for the debugger UI."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

for env in (Path(__file__).resolve().parents[2] / ".env", Path(__file__).resolve().parents[4] / ".env"):
    load_dotenv(env, override=True)  # the repository .env wins over a stale key in the shell environment

from .manager import Manager  # noqa: E402  (after env is loaded)
from .serialize import inner_text  # noqa: E402
from .tasks import TASKS  # noqa: E402

manager = Manager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await manager.start(None)
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception) -> JSONResponse:
    """Every failure reaches the UI as JSON with a readable detail (shown as a toast), never as a blank 500."""
    manager.study.log("error", detail=f"{type(exc).__name__}: {exc}")
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {str(exc)[:400]}"})


class SendBody(BaseModel):
    type: str
    target: str = "group"
    content: str = ""
    source: str = "user"


class EditBody(BaseModel):
    timestamp: int
    content: str | None = None


class QueueBody(BaseModel):
    index: int
    content: str | None = None


class NameBody(BaseModel):
    name: str


class SessionBody(BaseModel):
    participant: str | None = None
    condition: str | None = None
    trial: str | None = None


class JudgeBody(BaseModel):
    session: int | None = None


class LogBody(BaseModel):
    event: str
    data: dict[str, Any] = {}


@app.get("/api/state")
async def state():
    return manager.state()


@app.get("/api/tasks")
async def tasks():
    return {k: {"task": v["task"], "web": v.get("web", "corpus")} for k, v in TASKS.items()}


@app.get("/api/recordings")
async def recordings():
    return manager.recordings()


@app.post("/api/task")
async def new_task(body: NameBody):
    if body.name not in TASKS:
        raise HTTPException(404, "unknown task")
    async with manager.lock:
        await manager.start(body.name)
    manager.study.log("task", task=body.name)
    return {"ok": True}


@app.post("/api/recordings/load")
async def load(body: NameBody):
    if body.name not in manager.recordings():
        raise HTTPException(404, "unknown recording")
    async with manager.lock:
        await manager.load_recording(body.name)
    manager.study.log("load", recording=body.name, task=manager.task_id)
    return {"ok": True}


@app.post("/api/recordings/save")
async def save(body: NameBody):
    name = "".join(ch for ch in body.name if ch.isalnum() or ch in "-_") or "run"
    return {"path": str(manager.save_recording(name))}


@app.post("/api/run")
async def run():
    manager.run()
    manager.study.log("run", queue=len(manager.queue))
    return {"ok": True}


@app.post("/api/stop")
async def stop():
    await manager.stop()
    manager.study.log("stop")
    return {"ok": True}


@app.post("/api/step")
async def step():
    async with manager.lock:
        manager.study.log("step", queue=len(manager.queue))
        await manager.step()
    return {"ok": True}


@app.post("/api/drop")
async def drop():
    async with manager.lock:
        manager.study.log("drop", index=0)
        await manager.drop()
    return {"ok": True}


@app.post("/api/queue/edit")
async def queue_edit(body: QueueBody):
    try:
        async with manager.lock:
            if body.content is None:
                await manager.drop_queued(body.index)
                manager.study.log("drop", index=body.index)
            else:
                before = manager.state()["queue"][body.index]["content"] if body.index < len(manager.queue) else None
                manager.edit_queued(body.index, body.content)
                manager.study.log("queue_edit", index=body.index, old=before, new=body.content)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/api/send")
async def send(body: SendBody):
    try:
        await manager.send(body.type, body.target, body.content, body.source)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))
    manager.study.log("send", type=body.type, target=body.target, source=body.source, content=body.content)
    return {"ok": True}


@app.post("/api/edit")
async def edit(body: EditBody):
    try:
        async with manager.lock:
            entry = manager.recorder.at(body.timestamp)
            before = manager.state()["current_session"]
            old_text = inner_text(entry.message) if entry is not None else None
            await manager.edit_and_revert(body.timestamp, body.content)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))
    manager.study.log("reset" if body.content is None else "edit", timestamp=body.timestamp, from_session=before,
                      to_session=before + 1, sender=str(getattr(entry, "sender", "")), old=old_text, new=body.content)
    return {"ok": True}


@app.post("/api/judge")
async def judge(body: JudgeBody):
    if manager.judging:
        raise HTTPException(409, "judge already running")
    if manager.running or manager.busy:
        raise HTTPException(409, "stop the run before judging")
    try:
        result = await manager.judge(body.session)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))
    manager.study.log("judge", session=body.session, suspects=[s["timestamp"] for s in result["suspects"]])
    return result


@app.post("/api/session")
async def session(body: SessionBody):
    manager.study.set(body.participant, body.condition, body.trial)
    return {"participant": manager.study.participant, "condition": manager.study.condition, "trial": manager.study.trial}


@app.post("/api/log")
async def log(body: LogBody):
    manager.study.log(body.event, **body.data)
    return {"ok": True}


dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if dist.exists():
    app.mount("/", StaticFiles(directory=dist, html=True), name="ui")

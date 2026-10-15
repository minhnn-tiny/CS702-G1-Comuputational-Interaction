"""HTTP API for the debugger UI."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

for env in (Path(__file__).resolve().parents[2] / ".env", Path(__file__).resolve().parents[4] / ".env"):
    load_dotenv(env)

from .manager import Manager  # noqa: E402  (after env is loaded)
from .tasks import TASKS  # noqa: E402

manager = Manager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await manager.start(None)
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class SendBody(BaseModel):
    type: str
    target: str = "group"
    content: str = ""
    source: str = "user"


class EditBody(BaseModel):
    timestamp: int
    content: str | None = None


class NameBody(BaseModel):
    name: str


@app.get("/api/state")
async def state():
    return manager.state()


@app.get("/api/tasks")
async def tasks():
    return {k: v["task"] for k, v in TASKS.items()}


@app.get("/api/recordings")
async def recordings():
    return manager.recordings()


@app.post("/api/task")
async def new_task(body: NameBody):
    if body.name not in TASKS:
        raise HTTPException(404, "unknown task")
    async with manager.lock:
        await manager.start(body.name)
    return {"ok": True}


@app.post("/api/recordings/load")
async def load(body: NameBody):
    async with manager.lock:
        await manager.load_recording(body.name)
    return {"ok": True}


@app.post("/api/recordings/save")
async def save(body: NameBody):
    return {"path": str(manager.save_recording(body.name))}


@app.post("/api/run")
async def run():
    manager.run()
    return {"ok": True}


@app.post("/api/stop")
async def stop():
    await manager.stop()
    return {"ok": True}


@app.post("/api/step")
async def step():
    async with manager.lock:
        await manager.step()
    return {"ok": True}


@app.post("/api/drop")
async def drop():
    async with manager.lock:
        await manager.drop()
    return {"ok": True}


@app.post("/api/send")
async def send(body: SendBody):
    try:
        await manager.send(body.type, body.target, body.content, body.source)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@app.post("/api/edit")
async def edit(body: EditBody):
    try:
        async with manager.lock:
            await manager.edit_and_revert(body.timestamp, body.content)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if dist.exists():
    app.mount("/", StaticFiles(directory=dist, html=True), name="ui")

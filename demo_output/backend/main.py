"""FastAPI backend for portfolio website."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Portfolio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Project(BaseModel):
    id: str
    title: str
    description: str
    tech: list[str]
    url: str


PROJECTS = [
    Project(id="1", title="Chief AI", description="Multi-agent orchestrator", tech=["Python"], url="#"),
    Project(id="2", title="AdaptiveAgent", description="Adaptive AI agent", tech=["Python"], url="#"),
]


@app.get("/api/projects")
async def get_projects() -> list[Project]:
    return PROJECTS


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}

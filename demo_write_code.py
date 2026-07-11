"""Demo: Chief-AI writing actual code (no opencode needed).

This shows the full pipeline:
1. Plan a goal
2. Route to specialist agents
3. Each agent writes real code
4. Synthesize into a complete project
"""

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from chief_ai import ChiefAI, MockExecutor
from chief_ai.core.registry import get_sub_agent


class CodeWritingExecutor(MockExecutor):
    """A demo executor that writes real code files per agent."""

    OUTPUT_DIR = "demo_output"

    def __init__(self):
        super().__init__()
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

    def run(self, sub_agent_id: str, prompt: str) -> str:
        agent = get_sub_agent(sub_agent_id)

        code_map = {
            "exec-strategy": self._write_strategy,
            "design-ui": self._write_ui_design,
            "eng-frontend": self._write_react_component,
            "eng-backend": self._write_fastapi_server,
            "eng-api": self._write_api_contract,
            "qa-testing": self._write_tests,
            "doc-readme": self._write_readme,
            "devops-cloud": self._write_dockerfile,
            "devops-docker": self._write_compose,
            "marketing-launch": self._write_launch_checklist,
        }

        writer = code_map.get(sub_agent_id)
        if writer:
            return writer()

        return (
            f"[{agent.name}] acknowledged task.\n"
            f"Department: {agent.department}\n"
            f"Focus: {', '.join(agent.tags[:3])}..."
        )

    def _write_strategy(self) -> str:
        content = """# Project Strategy: Portfolio Website

## Vision
A modern, fast portfolio showcasing projects and skills.

## Goals
1. Deploy live within 1 week
2. Mobile-first responsive design
3. SEO optimized
4. Clean, maintainable codebase

## Tech Stack
- Frontend: React + Vite + Tailwind CSS
- Hosting: Vercel (auto-deploy from GitHub)
- Analytics: Vercel Analytics

## Success Metrics
- Lighthouse score > 90
- Load time < 2s
- Mobile responsive on all devices
"""
        path = os.path.join(self.OUTPUT_DIR, "docs", "STRATEGY.md")
        self._save(path, content)
        return f"Strategy document written to {path}\n\nKey decisions: React + Vite + Tailwind, Vercel hosting."

    def _write_ui_design(self) -> str:
        content = """/* Design System - Portfolio Website */

:root {
  /* Colors */
  --color-primary: #3b82f6;
  --color-primary-dark: #2563eb;
  --color-bg: #0f172a;
  --color-surface: #1e293b;
  --color-text: #e2e8f0;
  --color-muted: #94a3b8;

  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 2rem;
  --space-xl: 4rem;

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

/* Layout */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-md);
}

/* Cards */
.card {
  background: var(--color-surface);
  border-radius: 12px;
  padding: var(--space-lg);
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(59, 130, 246, 0.15);
}

/* Grid */
.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--space-lg);
}
"""
        path = os.path.join(self.OUTPUT_DIR, "src", "styles.css")
        self._save(path, content)
        return f"Design system CSS written to {path}"

    def _write_react_component(self) -> str:
        content = '''import React from 'react';
import './styles.css';

interface ProjectCardProps {
  title: string;
  description: string;
  tech: string[];
  url: string;
  image?: string;
}

export function ProjectCard({ title, description, tech, url, image }: ProjectCardProps) {
  return (
    <a href={url} target="_blank" rel="noopener noreferrer" className="card">
      {image && <img src={image} alt={title} className="card-image" />}
      <h3 className="card-title">{title}</h3>
      <p className="card-description">{description}</p>
      <div className="card-tech">
        {tech.map((t) => (
          <span key={t} className="badge">{t}</span>
        ))}
      </div>
    </a>
  );
}

interface HeroProps {
  name: string;
  tagline: string;
}

export function Hero({ name, tagline }: HeroProps) {
  return (
    <section className="hero">
      <h1 className="hero-name">{name}</h1>
      <p className="hero-tagline">{tagline}</p>
      <div className="hero-actions">
        <a href="#projects" className="btn btn-primary">View Projects</a>
        <a href="#contact" className="btn btn-outline">Contact Me</a>
      </div>
    </section>
  );
}

export function App() {
  const projects = [
    {
      title: "Chief AI",
      description: "Multi-agent orchestrator with 55 specialist agents",
      tech: ["Python", "OpenCode", "Multi-Agent"],
      url: "https://github.com/yogendrachukka01/Chief-AI",
    },
    {
      title: "AdaptiveAgent",
      description: "AI agent that adapts to user behavior",
      tech: ["Python", "Machine Learning"],
      url: "https://github.com/yogendrachukka01/AdaptiveAgent",
    },
  ];

  return (
    <div className="container">
      <Hero name="Yogendra Chukka" tagline="Building AI-powered tools" />
      <section id="projects">
        <h2>Projects</h2>
        <div className="grid-2">
          {projects.map((p) => (
            <ProjectCard key={p.title} {...p} />
          ))}
        </div>
      </section>
    </div>
  );
}
'''
        path = os.path.join(self.OUTPUT_DIR, "src", "App.tsx")
        self._save(path, content)
        return f"React component written to {path}"

    def _write_fastapi_server(self) -> str:
        content = '''"""FastAPI backend for portfolio website."""

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
'''
        path = os.path.join(self.OUTPUT_DIR, "backend", "main.py")
        self._save(path, content)
        return f"FastAPI server written to {path}"

    def _write_api_contract(self) -> str:
        content = """openapi: 3.0.3
info:
  title: Portfolio API
  version: 1.0.0
paths:
  /api/projects:
    get:
      summary: Get all projects
      responses:
        "200":
          description: List of projects
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Project"
  /api/health:
    get:
      summary: Health check
      responses:
        "200":
          description: OK
components:
  schemas:
    Project:
      type: object
      properties:
        id:
          type: string
        title:
          type: string
        description:
          type: string
        tech:
          type: array
          items:
            type: string
        url:
          type: string
"""
        path = os.path.join(self.OUTPUT_DIR, "docs", "openapi.yaml")
        self._save(path, content)
        return f"API contract written to {path}"

    def _write_tests(self) -> str:
        content = '''"""Tests for portfolio API."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_projects():
    r = client.get("/api/projects")
    assert r.status_code == 200
    projects = r.json()
    assert len(projects) >= 2
    assert projects[0]["title"] == "Chief AI"
'''
        path = os.path.join(self.OUTPUT_DIR, "tests", "test_api.py")
        self._save(path, content)
        return f"Tests written to {path}"

    def _write_readme(self) -> str:
        content = """# Portfolio Website

A modern portfolio built with React + Vite + Tailwind CSS.

## Tech Stack
- **Frontend:** React, TypeScript, Tailwind CSS
- **Backend:** FastAPI (Python)
- **Hosting:** Vercel

## Getting Started

```bash
npm install
npm run dev
```

## Structure
```
src/
  App.tsx        # Main React components
  styles.css     # Design system
backend/
  main.py        # FastAPI server
tests/
  test_api.py    # API tests
```

## License
MIT
"""
        path = os.path.join(self.OUTPUT_DIR, "README.md")
        self._save(path, content)
        return f"README written to {path}"

    def _write_dockerfile(self) -> str:
        content = """FROM node:20-alpine AS frontend
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM python:3.12-slim AS backend
WORKDIR /app
COPY backend/ .
RUN pip install fastapi uvicorn

FROM python:3.12-slim
COPY --from=frontend /app/dist /app/static
COPY --from=backend /app /app
WORKDIR /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        path = os.path.join(self.OUTPUT_DIR, "Dockerfile")
        self._save(path, content)
        return f"Dockerfile written to {path}"

    def _write_compose(self) -> str:
        content = """version: "3.9"

services:
  frontend:
    build:
      context: .
      target: frontend
    ports:
      - "3000:3000"

  backend:
    build:
      context: .
      target: backend
    ports:
      - "8000:8000"
"""
        path = os.path.join(self.OUTPUT_DIR, "docker-compose.yml")
        self._save(path, content)
        return f"Docker Compose written to {path}"

    def _write_launch_checklist(self) -> str:
        content = """# Launch Checklist

## Pre-launch
- [ ] All tests passing
- [ ] Lighthouse score > 90
- [ ] Mobile responsive verified
- [ ] SEO meta tags in place
- [ ] Favicon and OG image set

## Deploy
- [ ] Push to main branch
- [ ] Vercel auto-deploy triggered
- [ ] Custom domain configured
- [ ] SSL certificate active

## Post-launch
- [ ] Share on LinkedIn
- [ ] Submit to Product Hunt
- [ ] Update GitHub README with live link
- [ ] Monitor analytics for 1 week
"""
        path = os.path.join(self.OUTPUT_DIR, "docs", "LAUNCH_CHECKLIST.md")
        self._save(path, content)
        return f"Launch checklist written to {path}"

    def _save(self, path: str, content: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def main():
    print("=" * 60)
    print("  Chief AI - Real Code Generation Demo")
    print("=" * 60)
    print()

    executor = CodeWritingExecutor()
    chief = ChiefAI(executor=executor)

    goal = "Build a portfolio website with React, FastAPI backend, and Docker"
    print(f"Goal: {goal}\n")

    print("--- Planning ---")
    plan = chief.plan(goal)
    print(plan.render())
    print()

    print("--- Executing ---")
    result = chief.execute(goal)
    print(result)

    print("\n--- Generated Files ---")
    for root, dirs, files in os.walk(CodeWritingExecutor.OUTPUT_DIR):
        for f in sorted(files):
            rel = os.path.relpath(os.path.join(root, f), CodeWritingExecutor.OUTPUT_DIR)
            size = os.path.getsize(os.path.join(root, f))
            print(f"  {rel:<40} {size:>6} bytes")

    print(f"\nDone! Files written to ./{CodeWritingExecutor.OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

"""Registry of every department and sub-agent in the Chief AI system.

This module is the single source of truth. The opencode agent files
(``.opencode/agents/*.md``) and ``opencode.json`` are generated from it, so
keep agent definitions here rather than hand-editing the generated files.
"""

from __future__ import annotations

from typing import Optional

from .types import Department, Permission, SubAgent

# ---------------------------------------------------------------------------
# Department permission / tool presets
# ---------------------------------------------------------------------------
# Each department defines a default tool set and the permission tiers its
# sub-agents are granted when compiled into opencode agents.


def _perms(*allowed: Permission) -> dict[Permission, bool]:
    return {p: (p in allowed) for p in Permission}


_DEPT_DEFAULTS: dict[str, tuple[list[str], dict[Permission, bool]]] = {
    "executive": (["read", "web"], _perms(Permission.READ, Permission.NETWORK)),
    "engineering": (
        ["read", "write", "bash", "web"],
        _perms(Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.NETWORK),
    ),
    "design": (["read", "write", "web"], _perms(Permission.READ, Permission.WRITE, Permission.NETWORK)),
    "devops": (
        ["read", "write", "bash", "web"],
        _perms(Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.NETWORK),
    ),
    "qa": (
        ["read", "write", "bash", "web"],
        _perms(Permission.READ, Permission.WRITE, Permission.EXECUTE, Permission.NETWORK),
    ),
    "documentation": (["read", "write", "web"], _perms(Permission.READ, Permission.WRITE, Permission.NETWORK)),
    "research": (["read", "web"], _perms(Permission.READ, Permission.NETWORK)),
    "marketing": (["read", "write", "web"], _perms(Permission.READ, Permission.WRITE, Permission.NETWORK)),
    "finance": (["read", "web"], _perms(Permission.READ, Permission.NETWORK)),
    "legal": (["read", "web"], _perms(Permission.READ, Permission.NETWORK)),
    "memory": (["read", "write"], _perms(Permission.READ, Permission.WRITE)),
}


def _prompt(name: str, department: str, description: str, tags: list[str]) -> str:
    focus = "\n".join(f"- {t}" for t in tags)
    return f"""You are **{name}**, a specialist sub-agent in the **{department}** \
department of the Chief AI system.

## Mandate
{description}

## Focus Areas
{focus}

## Operating Rules
- Stay strictly within your specialty. Route anything out of scope back to the Chief AI.
- Be concrete and actionable; produce deliverables other agents can integrate directly.
- Follow the project's existing conventions, tooling, and code style.
- When you write files or run commands, keep changes minimal and well-scoped.

## Output
Return a focused result: a one-line summary, the deliverable (code, plan, copy, or
findings), and any handoffs required by other sub-agents.
"""


class _Spec:
    def __init__(
        self,
        sid: str,
        name: str,
        description: str,
        tags: list[str],
        tools: Optional[list[str]] = None,
        perms: Optional[dict[Permission, bool]] = None,
        model: Optional[str] = None,
    ) -> None:
        self.sid = sid
        self.name = name
        self.description = description
        self.tags = tags
        self.tools = tools
        self.perms = perms
        self.model = model


# ---------------------------------------------------------------------------
# Department definitions
# ---------------------------------------------------------------------------

_EXECUTIVE = (
    "executive",
    "Executive AI",
    "Sets direction: strategy, product, startup guidance, and decision-making.",
    [
        _Spec("exec-strategy", "Strategy", "Defines goals, roadmaps, and strategic direction.",
              ["strategy", "goal", "roadmap", "vision", "objective", "plan"]),
        _Spec("exec-product", "Product Management", "Owns product requirements, scope, and prioritization.",
              ["product", "feature", "requirements", "prd", "spec", "prioritize", "scope"]),
        _Spec("exec-startup", "Startup Advisor", "Advises on MVP, validation, and early-stage startup strategy.",
              ["startup", "mvp", "validation", "founder", "incubator", "pitch"]),
        _Spec("exec-decision", "Decision Engine", "Evaluates tradeoffs and recommends decisions.",
              ["decision", "tradeoff", "evaluate", "choose", "option", "recommend"]),
    ],
)

_ENGINEERING = (
    "engineering",
    "Engineering AI",
    "Builds and architects software across frontend, backend, mobile, desktop, ML, data, and APIs.",
    [
        _Spec("eng-frontend", "Frontend Expert", "Builds user-facing web interfaces and components.",
              ["frontend", "front-end", "react", "vue", "css", "html", "component", "ui code", "web app"]),
        _Spec("eng-backend", "Backend Expert", "Builds servers, services, and business logic.",
              ["backend", "back-end", "server", "service", "business logic", "node", "python", "go"]),
        _Spec("eng-mobile", "Mobile Expert", "Builds iOS, Android, and cross-platform mobile apps.",
              ["mobile", "ios", "android", "react native", "flutter", "swift", "kotlin"]),
        _Spec("eng-desktop", "Desktop Expert", "Builds desktop applications (Electron, Tauri, native).",
              ["desktop", "electron", "tauri", "windows", "macos app", "linux app"]),
        _Spec("eng-ml", "AI/ML Engineer", "Builds models, LLM pipelines, and inference systems.",
              ["ai", "ml", "model", "llm", "train", "inference", "prompt", "vector"]),
        _Spec("eng-data", "Data Engineer", "Builds pipelines, warehouses, and ETL.",
              ["data", "pipeline", "etl", "warehouse", "datastore", "analytics"]),
        _Spec("eng-api", "API Architect", "Designs REST/GraphQL APIs and contracts.",
              ["api", "rest", "graphql", "endpoint", "contract", "schema"]),
        _Spec("eng-system", "System Architect", "Designs scalable, distributed system architecture.",
              ["architecture", "system", "scalability", "distributed", "microservice", "design"]),
    ],
)

_DESIGN = (
    "design",
    "Design AI",
    "Creates interfaces, brand, and motion across UI, UX, graphic, brand, and motion.",
    [
        _Spec("design-ui", "UI Designer", "Designs visual interfaces, layouts, and components.",
              ["ui", "interface", "visual", "layout", "screen", "component design", "mockup"]),
        _Spec("design-ux", "UX Researcher", "Researches users and validates usability.",
              ["ux", "research", "usability", "user", "interview", "journey", "persona"]),
        _Spec("design-graphic", "Graphic Designer", "Produces graphics, illustrations, and visual assets.",
              ["graphic", "logo", "illustration", "asset", "icon", "banner"]),
        _Spec("design-brand", "Brand Designer", "Defines brand identity, tone, and guidelines.",
              ["brand", "identity", "tone", "guideline", "style"]),
        _Spec("design-motion", "Motion Designer", "Creates animations, motion, and video assets.",
              ["motion", "animation", "video", "transition", "micro-interaction"]),
    ],
)

_DEVOPS = (
    "devops",
    "DevOps AI",
    "Operates infrastructure: Linux, containers, orchestration, cloud, networking, security.",
    [
        _Spec("devops-linux", "Linux", "Automates Linux systems and shell scripting.",
              ["linux", "bash", "shell", "script", "systemd", "cron"]),
        _Spec("devops-docker", "Docker", "Builds container images and Compose setups.",
              ["docker", "container", "image", "compose"]),
        _Spec("devops-k8s", "Kubernetes", "Orchestrates workloads with Kubernetes.",
              ["kubernetes", "k8s", "orchestrat", "helm", "pod", "cluster"]),
        _Spec("devops-cloud", "Cloud (AWS/GCP/Azure)", "Provisions cloud infrastructure and deployments.",
              ["aws", "gcp", "azure", "cloud", "deploy", "infrastructure", "terraform"]),
        _Spec("devops-network", "Networking", "Configures networking, DNS, and connectivity.",
              ["network", "dns", "vpc", "proxy", "subnet", "connectivity"]),
        _Spec("devops-security", "Security", "Hardens systems, manages IAM and secrets.",
              ["security", "hardening", "iam", "secret", "vault", "policy"]),
    ],
)

_QA = (
    "qa",
    "QA AI",
    "Ensures quality: testing, bug hunting, performance, and security audits.",
    [
        _Spec("qa-testing", "Testing", "Writes and runs automated tests.",
              ["test", "qa", "unit test", "e2e", "integration", "coverage"]),
        _Spec("qa-bug", "Bug Hunting", "Finds and reproduces defects.",
              ["bug", "defect", "crash", "error", "reproduce", "regression"]),
        _Spec("qa-perf", "Performance", "Profiles and optimizes performance.",
              ["performance", "latency", "optimize", "speed", "profiling", "bottleneck"]),
        _Spec("qa-securityaudit", "Security Audit", "Audits code and systems for vulnerabilities.",
              ["security audit", "vulnerability", "pentest", "cve", "owasp"]),
    ],
)

_DOCUMENTATION = (
    "documentation",
    "Documentation AI",
    "Produces PRDs, READMEs, API docs, and technical writing.",
    [
        _Spec("doc-prd", "PRDs", "Writes product requirement documents.",
              ["prd", "product requirement", "spec document"]),
        _Spec("doc-readme", "READMEs", "Writes and maintains READMEs and project docs.",
              ["readme", "documentation", "docs update", "getting started"]),
        _Spec("doc-apidocs", "API Docs", "Documents APIs and OpenAPI specs.",
              ["api doc", "openapi", "swagger", "endpoint doc"]),
        _Spec("doc-techwriting", "Technical Writing", "Authors tutorials, guides, and explanations.",
              ["technical writing", "tutorial", "guide", "explanation", "how-to"]),
    ],
)

_RESEARCH = (
    "research",
    "Research AI",
    "Investigates AI, markets, competitors, patents, and academia.",
    [
        _Spec("research-ai", "AI Research", "Tracks AI/ML research and new models.",
              ["ai research", "paper", "new model", "sota", "benchmark"]),
        _Spec("research-market", "Market Research", "Analyzes markets, trends, and sizing.",
              ["market research", "trend", "market size", "tsam", "sam"]),
        _Spec("research-competitor", "Competitor Analysis", "Benchmarks competitors and alternatives.",
              ["competitor", "benchmark", "vs ", "alternative", "landscape"]),
        _Spec("research-patent", "Patent Search", "Searches patents and IP landscape.",
              ["patent", "ip", "intellectual property", "prior art"]),
        _Spec("research-academic", "Academic Research", "Surveys academic literature.",
              ["academic", "literature", "survey", "citation", "arxiv"]),
    ],
)

_MARKETING = (
    "marketing",
    "Marketing AI",
    "Drives growth: SEO, LinkedIn, GitHub, portfolio, social, and launches.",
    [
        _Spec("marketing-seo", "SEO", "Optimizes search ranking and discovery.",
              ["seo", "search ranking", "keywords", "metadata"]),
        _Spec("marketing-linkedin", "LinkedIn", "Creates LinkedIn posts and presence.",
              ["linkedin", "post", "thought leadership"]),
        _Spec("marketing-github", "GitHub", "Manages GitHub presence and open source.",
              ["github", "repo", "open source", "contribution"]),
        _Spec("marketing-portfolio", "Portfolio", "Builds and refines personal portfolios.",
              ["portfolio", "personal site", "showcase"]),
        _Spec("marketing-social", "Social Media", "Creates social media content.",
              ["social media", "twitter", "x ", "instagram", "content"]),
        _Spec("marketing-launch", "Launch Strategy", "Plans launches and go-to-market.",
              ["launch", "release", "go-to-market", "gtm", "announcement"]),
    ],
)

_FINANCE = (
    "finance",
    "Finance AI",
    "Manages budgeting, pricing, revenue, and startup finance.",
    [
        _Spec("finance-budgeting", "Budgeting", "Plans budgets and spend.",
              ["budget", "cost", "spend", "expense", "forecast"]),
        _Spec("finance-pricing", "Pricing", "Designs pricing and monetization.",
              ["pricing", "price", "monetiz", "subscription", "tier"]),
        _Spec("finance-revenue", "Revenue", "Models revenue and sales.",
              ["revenue", "sales", "income", "mrr", "arr"]),
        _Spec("finance-startup", "Startup Finance", "Advises on runway, fundraising, and cap tables.",
              ["runway", "fundraising", "cap table", "equity", "valuation", "investor"]),
    ],
)

_LEGAL = (
    "legal",
    "Legal AI",
    "Handles licenses, privacy, terms, and compliance (advisory).",
    [
        _Spec("legal-license", "Licenses", "Advises on software and content licenses.",
              ["license", "licensing", "oss license", "mit", "apache"]),
        _Spec("legal-privacy", "Privacy", "Advises on privacy and data protection.",
              ["privacy", "gdpr", "ccpa", "data protection", "consent"]),
        _Spec("legal-terms", "Terms", "Drafts terms of service and policies.",
              ["terms", "tos", "terms of service", "policy", "agreement"]),
        _Spec("legal-compliance", "Compliance", "Advises on regulatory compliance.",
              ["compliance", "regulat", "hipaa", "soc2", "audit", "standard"]),
    ],
)

_MEMORY = (
    "memory",
    "Memory AI",
    "Retains context: long-term memory, knowledge graph, history, retrieval, learning.",
    [
        _Spec("memory-longterm", "Long-term Memory", "Stores durable facts and decisions.",
              ["remember", "recall", "fact", "long-term", "store"]),
        _Spec("memory-graph", "Knowledge Graph", "Maintains the entity/relationship graph.",
              ["knowledge graph", "entity", "relationship", "graph"]),
        _Spec("memory-history", "Project History", "Tracks project events and changes.",
              ["history", "timeline", "changelog", "event"]),
        _Spec("memory-context", "Context Retrieval", "Retrieves relevant context on demand.",
              ["context", "retrieve", "relevance", "search memory"]),
        _Spec("memory-learning", "Learning Engine", "Improves from feedback and outcomes.",
              ["learning", "feedback", "improve", "adapt"]),
    ],
)

_DEPARTMENT_SPECS = [
    _EXECUTIVE,
    _ENGINEERING,
    _DESIGN,
    _DEVOPS,
    _QA,
    _DOCUMENTATION,
    _RESEARCH,
    _MARKETING,
    _FINANCE,
    _LEGAL,
    _MEMORY,
]


def _build_registry() -> list[Department]:
    departments: list[Department] = []
    for dept_id, dept_name, dept_desc, specs in _DEPARTMENT_SPECS:
        defaults_tools, defaults_perms = _DEPT_DEFAULTS[dept_id]
        subs: list[SubAgent] = []
        for spec in specs:
            tools = spec.tools if spec.tools is not None else list(defaults_tools)
            perms = spec.perms if spec.perms is not None else dict(defaults_perms)
            subs.append(
                SubAgent(
                    id=spec.sid,
                    name=spec.name,
                    department=dept_id,
                    description=spec.description,
                    tags=spec.tags,
                    tools=tools,
                    permissions=perms,
                    model=spec.model,
                    prompt=_prompt(spec.name, dept_name, spec.description, spec.tags),
                )
            )
        departments.append(Department(id=dept_id, name=dept_name, description=dept_desc, sub_agents=subs))
    return departments


DEPARTMENTS: list[Department] = _build_registry()

# Flat lookup tables ---------------------------------------------------------
_REGISTRY: dict[str, SubAgent] = {s.id: s for d in DEPARTMENTS for s in d.sub_agents}
_DEPT_BY_ID: dict[str, Department] = {d.id: d for d in DEPARTMENTS}


def registry() -> list[Department]:
    """Return the full department tree."""
    return DEPARTMENTS


def list_departments() -> list[Department]:
    return DEPARTMENTS


def list_sub_agents() -> list[SubAgent]:
    return list(_REGISTRY.values())


def get_sub_agent(sub_id: str) -> SubAgent:
    if sub_id not in _REGISTRY:
        raise KeyError(f"Unknown sub-agent: {sub_id}")
    return _REGISTRY[sub_id]


def get_department(dept_id: str) -> Department:
    if dept_id not in _DEPT_BY_ID:
        raise KeyError(f"Unknown department: {dept_id}")
    return _DEPT_BY_ID[dept_id]

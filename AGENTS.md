# StreamEditor AI — Agent Instructions

> **This file is the mandatory entry point for all AI coding agents working on StreamEditor AI.**
> Read this file completely before making any changes to the codebase.

---

## Quick Start for Agents

Before touching any code, complete these steps **in order**:

1. **Read** `knowledge-vault/00_HOME/README.md` — project overview and navigation index
2. **Read** `knowledge-vault/01_PRODUCT/PRODUCT_VISION.md` — what we're building and why
3. **Read** the architecture document for the area you're changing (see `knowledge-vault/02_ARCHITECTURE/`)
4. **Read** relevant editorial documents if modifying editorial behavior (`knowledge-vault/03_EDITORIAL_BIBLE/`)
5. **Check** `knowledge-vault/00_HOME/PROJECT_STATUS.md` for current milestone, open tasks, and known blockers

> [!IMPORTANT]
> Skipping these reads is the most common cause of regressions and architectural drift.
> Do not proceed without completing them.

---

## Non-Negotiable Principles

### 1. AI Decides. Deterministic Software Executes.

LLMs and VLMs produce editorial decisions **only** through validated Pydantic schemas.

**An LLM MUST NEVER:**
- Execute arbitrary FFmpeg commands
- Generate arbitrary shell commands that get executed directly
- Modify media processing pipelines dynamically at runtime
- Bypass schema validation for any reason
- Directly mutate canonical editorial rules stored in the vault

Every AI editorial decision must pass through a validated `EditPlan`.
**The renderer executes the `EditPlan`. Not the model. Not a string. An `EditPlan`.**

```python
# WRONG — never do this
llm_response = model.generate("ffmpeg -i input.mp4 -ss 10 -t 5 output.mp4")
subprocess.run(llm_response, shell=True)  # ❌ NEVER

# RIGHT — model produces structured data, deterministic code executes
edit_plan: EditPlan = EditPlan.model_validate(llm_response_dict)  # ✅ validated
renderer.execute(edit_plan)  # ✅ deterministic, auditable
```

### 2. The Obsidian Vault IS the Source of Truth

If implementation and vault documentation disagree, treat it as a bug.

- Update the vault when behavior changes — not after, not later, **now**
- Only documents with `status: canonical` automatically affect production editing
- Documents with `status: draft | research | proposal` are work-in-progress — do not promote automatically
- Never copy-paste vault content into code — reference it via `VaultIndex`

### 3. Never Use shell=True or String-Interpolated Commands

All subprocess calls must use argument lists:

```python
# WRONG
subprocess.run(f"ffmpeg -i {input_path} {output_path}", shell=True)  # ❌

# RIGHT
subprocess.run(
    ["ffmpeg", "-i", str(input_path), str(output_path)],
    check=True,
    capture_output=True,
)  # ✅
```

---

## Coding Standards

| Topic | Standard |
|-------|----------|
| Python version | 3.12+ |
| Validation | Pydantic v2 — `model_validate()`, not `parse_obj()` |
| Web framework | FastAPI with async handlers |
| ORM | SQLAlchemy async (`async_sessionmaker`) |
| Subprocess | Argument lists only, never `shell=True` |
| Type checking | mypy strict — `make lint` must pass |
| Linting | ruff — `make lint` must pass |
| Logging | structlog — structured logging on every pipeline step |
| Paths | `StorageProvider` — no hardcoded paths ever |
| Model names | `ModelProvider` — no hardcoded model names in business logic |
| Tests | Every new module needs tests in `tests/` |

---

## Before Making Changes

Answer these questions before writing code:

| Question | If YES, action required |
|----------|------------------------|
| Does this change affect system architecture? | Create an ADR in `knowledge-vault/07_ADR/` |
| Does this change editorial behavior? | Update `knowledge-vault/03_EDITORIAL_BIBLE/` |
| Does this introduce a new dependency? | ADR required, document rationale |
| Does this change a schema? | Update `knowledge-vault/05_SCHEMAS/` |
| Does this add a new pipeline stage? | Update `knowledge-vault/02_ARCHITECTURE/JOB_SYSTEM.md` |
| Does this change a canonical rule? | Human approval required — do not auto-promote |

---

## After Making Changes

Complete **all** of these before marking a task done:

1. **`make test`** — all tests must pass (no skips without documented reason)
2. **`make lint`** — mypy strict and ruff must pass
3. **`make check-vault`** — vault consistency must pass
4. **Update** `knowledge-vault/00_HOME/PROJECT_STATUS.md` — current state, completed items
5. **Update** `knowledge-vault/11_CHANGELOG/CHANGELOG.md` — what changed and why
6. **Document** any technical debt incurred in `PROJECT_STATUS.md` under `## Technical Debt`
7. **Update** relevant vault docs if behavior changed — schemas, architecture, editorial rules

> [!WARNING]
> Do NOT mark work complete if `make test-all` fails.
> Do NOT mark work complete if vault docs are stale.

---

## Repository Structure

```
stream-editor-ai/
├── AGENTS.md                    ← YOU ARE HERE — read first
├── README.md                    ← Human-facing introduction
├── pyproject.toml               ← uv workspace root
├── Makefile                     ← Common commands
├── docker-compose.yml           ← Local dev services
├── .env.example                 ← Environment template
│
├── knowledge-vault/             ← SOURCE OF TRUTH (Obsidian vault)
│   ├── 00_HOME/                 ← Project status, glossary, navigation
│   │   ├── README.md            ← Read this second (after AGENTS.md)
│   │   └── PROJECT_STATUS.md   ← Current milestone, open tasks, debt
│   ├── 01_PRODUCT/              ← Product vision and principles
│   │   ├── PRODUCT_VISION.md   ← What we're building and why
│   │   ├── PRODUCT_PRINCIPLES.md
│   │   └── MVP_ACCEPTANCE_CRITERIA.md
│   ├── 02_ARCHITECTURE/         ← System design documents
│   │   ├── SYSTEM_OVERVIEW.md  ← High-level architecture
│   │   ├── JOB_SYSTEM.md       ← Pipeline stages
│   │   ├── MEDIA_PIPELINE.md   ← FFmpeg/proxy strategy
│   │   └── MODEL_PROVIDER_ARCHITECTURE.md
│   ├── 03_EDITORIAL_BIBLE/      ← Editorial rules (canonical docs affect prod)
│   │   ├── EDITORIAL_PHILOSOPHY.md
│   │   └── KEEP_VS_CUT.md
│   ├── 04_RESEARCH/             ← EditDNA research findings
│   │   ├── RawFindings/         ← status: research (never auto-promote)
│   │   └── Patterns/            ← status: hypothesis (human approval needed)
│   ├── 05_SCHEMAS/              ← Schema specifications
│   │   ├── TIMELINE_EVENT.md
│   │   ├── EDIT_PLAN.md
│   │   └── EFFECTS.md
│   ├── 06_AGENTS/               ← Agent role definitions
│   ├── 07_ADR/                  ← Architecture Decision Records
│   ├── 08_RUNBOOKS/             ← Operational guides
│   ├── 09_TESTING/              ← Test strategy and plans
│   ├── 10_ROADMAP/              ← Milestones and roadmap
│   └── 11_CHANGELOG/            ← Change history
│
├── apps/
│   ├── api/                     ← FastAPI backend
│   │   └── Dockerfile
│   ├── worker/                  ← Celery async worker
│   │   └── Dockerfile
│   └── web/                     ← Next.js frontend
│       └── Dockerfile
│
├── packages/
│   ├── contracts/               ← Pydantic schemas (shared across services)
│   ├── storage/                 ← StorageProvider abstraction
│   ├── models/                  ← ModelProvider abstraction (mock/gemini/anthropic)
│   ├── media/                   ← FFmpeg/FFprobe wrappers
│   ├── analysis/                ← Analysis pipeline (transcription, scene detect)
│   ├── editorial/               ← Editorial logic and EditPlan generation
│   ├── rendering/               ← Renderer (EditPlan → media output)
│   └── vault/                   ← Vault indexing (FTS5, canonical rule retrieval)
│
├── renderer/
│   └── remotion/                ← Remotion rich overlays (TypeScript)
│
├── scripts/
│   ├── check_vault.py           ← Vault consistency checker (run before commit)
│   └── generate_test_media.py   ← Synthetic test media generator
│
├── tests/
│   ├── fixtures/                ← Synthetic test assets (committed, small)
│   └── golden/                  ← Golden output references
│
└── .agents/
    └── skills/                  ← Agent skill definitions
        ├── vault-curator/
        ├── reference-research/
        ├── reverse-edit-analysis/
        ├── video-analysis/
        ├── editorial-planning/
        ├── rendering/
        └── validation/
```

---

## Current Milestone: M0 — Foundation

See `knowledge-vault/00_HOME/PROJECT_STATUS.md` for detailed status.

**M0 Definition of Done:**
- [ ] Repository structure established
- [ ] Core schema contracts defined (contracts package)
- [ ] StorageProvider abstraction
- [ ] ModelProvider abstraction (mock + at least one real provider)
- [ ] `make test` passes
- [ ] `make lint` passes
- [ ] `make check-vault` passes
- [ ] Docker Compose: postgres + redis + api + worker + web

**Next milestone:** M1 — Media Foundation (project creation, FFprobe, proxy generation)

---

## Milestone Completion Checklist

Before marking any milestone complete:

- [ ] All acceptance criteria verified (see `knowledge-vault/01_PRODUCT/MVP_ACCEPTANCE_CRITERIA.md`)
- [ ] `make test` passes with no skips
- [ ] `make lint` passes (mypy strict + ruff)
- [ ] `make check-vault` passes
- [ ] `PROJECT_STATUS.md` updated (milestone marked, next milestone set)
- [ ] `CHANGELOG.md` updated
- [ ] Technical debt documented if any was incurred
- [ ] README.md "How to Run" section accurate

---

## Keeping Work Resumable

Every agent session should leave the repository in a state where another agent can pick up:

1. **Commit frequently** with meaningful messages
2. **Leave no half-done migrations** — either complete or roll back
3. **Update PROJECT_STATUS.md** at the end of every session with current state
4. **Document blockers** explicitly — what is blocked, why, and what is needed
5. **Never leave tests broken** — if you must stop mid-feature, push to a feature branch and note it

---

## Agent Skills Reference

Detailed instructions for specific agent tasks are in `.agents/skills/`:

| Skill | Purpose |
|-------|---------|
| `vault-curator` | Maintain vault integrity, validate frontmatter, detect conflicts |
| `reference-research` | Analyze reference editing, create `ResearchFinding` schemas |
| `reverse-edit-analysis` | Compare VOD vs edited derivative, extract editorial patterns |
| `video-analysis` | Run analysis pipeline, produce `TimelineEvent` schemas |
| `editorial-planning` | Generate `EditPlan` from canonical rules + analysis |
| `rendering` | Execute `EditPlan` via validated FFmpeg argument lists |
| `validation` | Run full test/lint/vault suite, validate media outputs |
## Anti-Drift Rule

> Never invent new canonical editorial behavior merely to fill gaps in the specification.

When editorial behavior is unspecified:
- Make it configurable;
- Implement the neutral infrastructure;
- Or create a proposal.

Do not guess and canonize the guess.

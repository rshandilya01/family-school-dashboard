# Implementation Plan: Family School Dashboard

**Branch**: `001-family-dashboard` | **Date**: 2026-11-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-family-dashboard/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

A parent opens one local site and switches between two children or both. The home view lists assignments and events in a 14-date window (today through the next 13 days) and the eight newest communications. The parent can add, edit, and delete communications, events, assignments, and grades, rename the children, and load fictional sample data only when the household is empty.

Technical approach: one Python process. FastAPI renders Jinja2 HTML forms. Records live in a SQLite file created on startup. pytest covers child filtering, the upcoming window, and restart persistence.

## Technical Context

**Language/Version**: Python 3.11+ (this environment has 3.12)

**Primary Dependencies**: FastAPI, Jinja2, uvicorn, pytest, httpx (TestClient)

**Storage**: SQLite via the stdlib `sqlite3` module. File path from `DATABASE_PATH`, default `data/school.db`.

**Testing**: pytest with FastAPI TestClient against a temporary database file

**Target Platform**: Local computer. The server binds to `127.0.0.1` only.

**Project Type**: Local web application, server-rendered pages

**Performance Goals**: One parent, two children, household-scale lists. Home and list pages respond as a normal local page load.

**Constraints**: No login, no telemetry, no outbound calls to Canvas, email, or TalkingPoints. Database file and `.env` stay out of git. No frontend build and no component library.

**Scale/Scope**: At most two children. Five screens (home, communications, events, assignments, grades) plus child naming and sample data.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Local Only**: Pass. uvicorn host is `127.0.0.1`. No telemetry and no deploy target.
- **II. Children's Data Stays Out of Git**: Pass. `data/` and `.env` are ignored. Sample names are fictional.
- **III. Two Child Profiles Are First-Class**: Pass. Every list takes `child=all` or a child id. Shared rows use a null child id.
- **IV. This Slice Does Not Call School Systems**: Pass. No HTTP client for external systems. `source` defaults to `Manual`.
- **V. Smallest App That Meets the Spec**: Pass. One package, stdlib SQLite, tests for the filter and the date window. Stack is recorded here, not in the spec.

Post-design re-check: the data model and UI contract stay inside these gates. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/001-family-dashboard/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── ui.md
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── __init__.py
├── main.py          # routes, forms, page rendering
├── db.py            # schema, queries, upcoming window
├── seed.py          # fictional sample data command
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── communications.html
│   ├── events.html
│   ├── assignments.html
│   ├── grades.html
│   ├── children.html
│   └── confirm_delete.html
└── static/
    └── style.css

tests/
├── conftest.py
├── test_filtering.py
├── test_upcoming.py
└── test_persistence.py
```

**Structure Decision**: Single Python project at the repository root. Pages are server-rendered. There is no separate frontend project.

## Complexity Tracking

No constitution violations.

# Implementation Plan: Gmail School Mail

**Branch**: `002-gmail-school-mail` | **Date**: 2026-11-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-gmail-school-mail/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

The parent connects one Gmail mailbox on this computer, names school senders, domains, or labels, and runs a check by hand. Matching messages in the inbox or in archived mail become communications with source `Gmail`. Spam, trash, sent mail, and non-matching messages are not stored. Each copied message can open the original in Gmail. Edits and confirmed deletes stick.

Technical approach: the same local FastAPI process. A read-only Gmail client uses `httpx` and OAuth on `127.0.0.1`. Import rules and child scope live in a function that tests call with fictional messages, so the suite never contacts Google. The refresh token stays in `data/`, which is already ignored.

## Technical Context

**Language/Version**: Python 3.11+ (this environment has 3.12)

**Primary Dependencies**: FastAPI, Jinja2, uvicorn, pytest, httpx (TestClient and Gmail HTTPS). No Google client library.

**Storage**: Existing SQLite file (`DATABASE_PATH`, default `data/school.db`) for rules, the check date, import identity, and communications. Refresh token in `data/gmail_token.json`. Client id and secret in `.env`.

**Testing**: pytest with FastAPI TestClient and a fake mailbox. No live Gmail call in the suite.

**Target Platform**: Local computer. The server binds to `127.0.0.1` only.

**Project Type**: Local web application, server-rendered pages

**Performance Goals**: One parent runs a check over the school subset of one mailbox (about 30 days, not the whole archive). List pages stay ordinary local form posts.

**Constraints**: Read-only toward Gmail. No Canvas, TalkingPoints, notifications, or summaries. No telemetry and no public bind. Tokens, `.env`, and the database stay out of git. Checks run only from a POST while the process is open. Attached files are not written to disk.

**Scale/Scope**: One mailbox, at most two children, a short list of school rules. One new page plus sender and "Open in Gmail" on communications that were copied.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Local Only**: Pass. uvicorn still binds to `127.0.0.1`. The only new outbound calls are the parent's own Gmail read and the OAuth token exchange. That is the connector this spec allows, not telemetry and not a hosted dashboard.
- **II. Children's Data Stays Out of Git**: Pass. `data/` (database and `gmail_token.json`) and `.env` stay ignored. Sample data and tests use fictional messages. The OAuth client id is a blank name in `.env.example`, never a real secret.
- **III. Two Child Profiles Are First-Class**: Pass. A copied message stores one child id or null for both. Existing list filters are unchanged.
- **IV. Later connectors are read-only**: Pass. This is the later mail connector. The client may list and get messages. It must not send, reply, delete, archive, label, or change read state. Canvas and TalkingPoints are not called.
- **V. Smallest App That Meets the Spec**: Pass. Two modules on the existing app, stdlib HTML cleanup, and pytest around the import function. Stack stays in this plan.

Post-design re-check: the data model, UI contract, and quickstart stay inside these gates. The fake mailbox is the test double, not a second product. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/002-gmail-school-mail/
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
├── main.py                 # existing routes, plus Gmail pages
├── db.py                   # existing tables, plus mail columns and helpers
├── mail.py                 # rules, child scope, body text, import transaction
├── gmail.py                # OAuth and read-only Gmail calls
└── templates/
    ├── gmail.html
    ├── communications.html # sender and Open in Gmail
    └── base.html           # link to the mail page

tests/
├── conftest.py
└── test_gmail.py           # fictional mailbox, no network
```

**Structure Decision**: Single Python project at the repository root. `mail.py` decides what is stored. `gmail.py` is the only module that talks to Google. Tests replace that module with fictional messages.

## Complexity Tracking

No constitution violations.

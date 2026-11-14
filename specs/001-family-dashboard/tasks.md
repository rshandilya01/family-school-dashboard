# Tasks: Family School Dashboard

**Input**: Design documents from `/specs/001-family-dashboard/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required by the spec (FR-016) and the constitution for child filtering and the upcoming-date window. Persistence is covered because restart is a success criterion.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (for example US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- Single project at the repository root with `app/` and `tests/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create `pyproject.toml` with Python 3.11+, FastAPI, Jinja2, uvicorn, python-multipart, pytest, and httpx
- [X] T002 [P] Add `.gitignore` for `.venv/`, `__pycache__/`, `.pytest_cache/`, `data/`, and `.env`, plus `.env.example` with `DATABASE_PATH` and `PORT`
- [X] T003 [P] Add `README.md` with local run steps from `specs/001-family-dashboard/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema, app factory, and shared page chrome that every story uses

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create the SQLite schema and connection helpers in `app/db.py` for children, communications, events, assignments, and grades
- [X] T005 Add the FastAPI factory in `app/main.py` that binds templates, static files, and startup table creation, and serve it with uvicorn on `127.0.0.1`
- [X] T006 [P] Add `app/templates/base.html` and `app/static/style.css` with the child switcher and navigation that preserve the `child` query parameter
- [X] T007 [P] Add `tests/conftest.py` with a TestClient on a temporary database file

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - See what is coming up (Priority: P1) 🎯 MVP

**Goal**: Home shows the 14-date window and the eight newest communications, filtered by child

**Independent Test**: With records inserted, `GET /` hides yesterday, shows in-window items soonest first, and a child filter hides the other child's private items

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Upcoming window test in `tests/test_upcoming.py`
- [X] T009 [P] [US1] Child filter test for home in `tests/test_filtering.py`

### Implementation for User Story 1

- [X] T010 [US1] Upcoming and recent-communication queries in `app/db.py`
- [X] T011 [US1] Home route in `app/main.py` and `app/templates/home.html`

**Checkpoint**: User Story 1 is testable on its own

---

## Phase 4: User Story 2 - Keep communications (Priority: P1)

**Goal**: Add, edit, and delete communications for one child or both

**Independent Test**: A private communication shows for that child and Both, not for the other child; a blank title is rejected; confirmed delete removes it

### Tests for User Story 2

- [X] T012 [US2] Communication scope and validation test in `tests/test_filtering.py`

### Implementation for User Story 2

- [X] T013 [US2] Communication queries in `app/db.py`
- [X] T014 [US2] Communication routes in `app/main.py`, `app/templates/communications.html`, and `app/templates/confirm_delete.html`

**Checkpoint**: User Stories 1 and 2 work independently

---

## Phase 5: User Story 3 - Keep dates, milestones, and field trips (Priority: P2)

**Goal**: Add, edit, and delete events, including field-trip destination and note

**Independent Test**: A shared field trip appears for both children; a one-child milestone does not appear for the other child; a yesterday event stays on the events screen and off home

### Tests for User Story 3

- [X] T015 [US3] Event scope test in `tests/test_filtering.py`

### Implementation for User Story 3

- [X] T016 [US3] Event queries in `app/db.py`
- [X] T017 [US3] Event routes in `app/main.py` and `app/templates/events.html`

**Checkpoint**: Events participate in the home window and have their own screen

---

## Phase 6: User Story 4 - Keep assignments (Priority: P2)

**Goal**: Add, edit, and delete assignments with Not started and Done

**Independent Test**: An in-window assignment appears on that child's home and not the other child's; status Done persists

### Tests for User Story 4

- [X] T018 [US4] Assignment filter and status test in `tests/test_filtering.py`

### Implementation for User Story 4

- [X] T019 [US4] Assignment queries in `app/db.py`
- [X] T020 [US4] Assignment routes in `app/main.py` and `app/templates/assignments.html`

**Checkpoint**: Assignments are scoped to one child and show on home when due

---

## Phase 7: User Story 5 - Keep grades (Priority: P3)

**Goal**: Add, edit, and delete grades and mark the latest per child and subject

**Independent Test**: Two grades in one subject show the later recorded date as Current; the other child's grades stay hidden

### Tests for User Story 5

- [X] T021 [US5] Latest-grade and child-scope test in `tests/test_filtering.py`

### Implementation for User Story 5

- [X] T022 [US5] Grade queries in `app/db.py`
- [X] T023 [US5] Grade routes in `app/main.py` and `app/templates/grades.html`

**Checkpoint**: Grades are recorded and labeled without being averaged

---

## Phase 8: User Story 6 - Name the children and load sample data (Priority: P3)

**Goal**: Add up to two children, rename them, and load fictional sample data once

**Independent Test**: A third child is rejected, a blank name is rejected, sample data loads once, and a rename shows on the lists

### Tests for User Story 6

- [X] T024 [US6] Child cap, rename, and sample-data test in `tests/test_children.py`

### Implementation for User Story 6

- [X] T025 [US6] Child and sample-data functions in `app/db.py` and `app/seed.py`
- [X] T026 [US6] Children routes in `app/main.py` and `app/templates/children.html`

**Checkpoint**: An empty household can be named or filled with fictional records

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Restart behavior and the local run path

- [X] T027 Persistence test that posts a communication, field trip, assignment, and grade, then opens a new app on the same file, in `tests/test_persistence.py`
- [X] T028 Confirm `.gitignore` ignores `data/` and `.env`, and that the sample command in `README.md` matches `specs/001-family-dashboard/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories
- **User Stories (Phase 3+)**: Depend on Foundational. Implement in priority order P1 → P2 → P3
- **Polish (Phase 9)**: Depends on the user stories it restarts

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational. No dependency on later stories
- **User Story 2 (P1)**: After Foundational. Home already lists communications once this story's rows exist
- **User Story 3 (P2)**: After Foundational
- **User Story 4 (P2)**: After Foundational
- **User Story 5 (P3)**: After Foundational
- **User Story 6 (P3)**: After Foundational. Sample data uses the tables from earlier stories

### Parallel Opportunities

- T002 and T003 can run alongside each other after T001
- T008 and T009 can be written together before the home implementation
- Later stories share `app/db.py` and `app/main.py`, so those edits stay sequential

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete Phase 3 and run the upcoming and filter tests
3. Then add stories 2 through 6 and the persistence test

## Notes

- [P] tasks use different files
- Tests for a story are written before that story's routes
- This feature does not call Canvas, email, or TalkingPoints

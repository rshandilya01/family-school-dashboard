# Research: Family School Dashboard

## Decision: Python, FastAPI, Jinja2, stdlib SQLite

- **Decision**: One local process. FastAPI serves Jinja2 templates. `sqlite3` stores records. pytest drives the app through TestClient.
- **Rationale**: The approved plan asked for the smaller toolchain. `uv` is available, there is no Node requirement, and a later read-only Canvas client can be another Python module. Server-rendered forms cover add, edit, and delete without a frontend build.
- **Alternatives considered**: Next.js with a SQLite driver adds a Node toolchain and a client bundle this slice does not need. An ORM adds a dependency the five tables do not need.

## Decision: Null child id means both children

- **Decision**: `communications.child_id` and `events.child_id` are null when the item is shared. Assignments and grades always store a child id.
- **Rationale**: The spec says a shared item is stored once. A null scope matches "both" without a join table.
- **Alternatives considered**: A link table of child ids would allow more than two children. This household is capped at two, so the extra table is unused.

## Decision: Upcoming window in application code

- **Decision**: A record is upcoming when its date is greater than or equal to today and less than or equal to today plus 13 days. Home merges assignments and events, sorts by that date, then title. Recent communications are the eight newest by date, then id, with no window.
- **Rationale**: The spec defines 14 calendar dates starting today. Doing it in one function keeps the rule testable without a person clicking.
- **Alternatives considered**: "Next 14 days" excluding today would hide work due today. Including today through day 14 would be 15 dates.

## Decision: Grades are text, latest per child and subject

- **Decision**: `score_text` stores whatever the parent typed. On the grades screen, the latest row for each child and subject (by recorded date, then id) is marked current.
- **Rationale**: The spec forbids averaging or letter conversion. Marking latest per child avoids treating two children's "Math" as one subject when Both is selected.
- **Alternatives considered**: A numeric score plus a letter column forces a format the parent may not have. Latest-per-subject across both children would hide one child's grade.

## Decision: Delete is a confirm page

- **Decision**: Delete opens a confirmation page. A confirm post removes the row. A cancel link leaves it.
- **Rationale**: The spec requires confirmation. A second page works without JavaScript.
- **Alternatives considered**: A checkbox on the list is easier to miss. Immediate delete fails the requirement.

## Decision: Sample data is an explicit command and a page action

- **Decision**: `python -m app.seed` and a form on the children page call the same function. It inserts only when the children table is empty. Startup creates tables and does not seed.
- **Rationale**: Restart must keep the parent's data. A second run must not duplicate fictional rows.
- **Alternatives considered**: Seeding on every empty startup would surprise a parent who deleted the sample children to start clean, and would fight a test that wants an empty household.

## Decision: Bind address

- **Decision**: `uvicorn` listens on `127.0.0.1` and port `8000` unless `PORT` is set. Tests use TestClient and do not open a port.
- **Rationale**: Constitution principle I. A port override is only for the local process, not a public bind.
- **Alternatives considered**: `0.0.0.0` would expose school records on the network.

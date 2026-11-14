# Quickstart: Family School Dashboard

Validation guide for the local dashboard. Details of fields and routes are in [data-model.md](./data-model.md) and [contracts/ui.md](./contracts/ui.md).

## Prerequisites

- Python 3.11 or newer
- `uv` on the path

From the repository root:

```bash
uv sync
```

## Automated checks

```bash
uv run pytest
```

Expected: tests pass for child filtering, the upcoming window (yesterday hidden, in-window shown, soonest first), and records that remain after a new process opens the same database file.

## Run the app

```bash
uv run python -m app.seed
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The seed command is safe to repeat: the second run adds nothing.

## Manual checks

1. Home on Both shows the sample field trip and assignment, and does not show the sample item dated yesterday.
2. Choose one child. The other child's private assignment or message disappears. The shared field trip stays.
3. Add a communication, a field trip, an assignment, and a grade. Stop the process, start it again, and confirm all four are still listed.
4. Confirm `data/` is not tracked by git.

## Out of scope for this check

Canvas, email, and TalkingPoints are not configured and must not be called.

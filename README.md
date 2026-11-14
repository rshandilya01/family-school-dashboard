# family-school-dashboard

A local page for one parent to track two children's communications, dates, field trips, assignments, and grades. This version is filled in by hand. Sample data uses fictional children. Canvas, email, and TalkingPoints are not connected.

The app listens on `127.0.0.1` only. The database file stays in `data/` and is not committed.

## Run

```bash
uv sync
uv run python -m app.seed
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Running the sample command again does not add a second copy.

## Tests

```bash
uv run pytest
```

See `specs/001-family-dashboard/quickstart.md` for the manual checks.

"""SQLite storage for the local family dashboard."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

WINDOW_DAYS = 13
RECENT_LIMIT = 8

SCHEMA = """
CREATE TABLE IF NOT EXISTS children (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS communications (
    id INTEGER PRIMARY KEY,
    child_id INTEGER REFERENCES children(id),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    source TEXT NOT NULL,
    link TEXT,
    occurred_on TEXT NOT NULL,
    created_at TEXT NOT NULL,
    sender_name TEXT,
    sender_email TEXT
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    child_id INTEGER REFERENCES children(id),
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    destination TEXT,
    notes TEXT,
    event_on TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY,
    child_id INTEGER NOT NULL REFERENCES children(id),
    subject TEXT NOT NULL,
    title TEXT NOT NULL,
    due_on TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS grades (
    id INTEGER PRIMARY KEY,
    child_id INTEGER NOT NULL REFERENCES children(id),
    subject TEXT NOT NULL,
    score_text TEXT NOT NULL,
    term TEXT NOT NULL,
    recorded_on TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS school_mail_rules (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('sender', 'domain', 'label')),
    value TEXT NOT NULL CHECK (length(value) > 0 AND length(value) <= 200),
    created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS school_mail_rules_kind_value
    ON school_mail_rules (kind, lower(value));
CREATE TABLE IF NOT EXISTS gmail_imports (
    gmail_id TEXT PRIMARY KEY,
    communication_id INTEGER REFERENCES communications(id),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gmail_checkpoint (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_success_on TEXT
);
"""


def connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    columns = _columns(conn, "communications")
    if "sender_name" not in columns:
        conn.execute("ALTER TABLE communications ADD COLUMN sender_name TEXT")
    if "sender_email" not in columns:
        conn.execute("ALTER TABLE communications ADD COLUMN sender_email TEXT")
    conn.execute("INSERT OR IGNORE INTO gmail_checkpoint (id, last_success_on) VALUES (1, NULL)")
    conn.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_children(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT id, name FROM children ORDER BY id").fetchall()


def child_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) AS n FROM children").fetchone()["n"]


def add_child(conn: sqlite3.Connection, name: str) -> str | None:
    cleaned = name.strip()
    if not cleaned:
        return "Name is required."
    if len(cleaned) > 80:
        return "Name is too long."
    if child_count(conn) >= 2:
        return "This household already has two children."
    conn.execute(
        "INSERT INTO children (name, created_at) VALUES (?, ?)",
        (cleaned, _now()),
    )
    conn.commit()
    return None


def rename_child(conn: sqlite3.Connection, child_id: int, name: str) -> str | None:
    cleaned = name.strip()
    if not cleaned:
        return "Name is required."
    if len(cleaned) > 80:
        return "Name is too long."
    updated = conn.execute(
        "UPDATE children SET name = ? WHERE id = ?",
        (cleaned, child_id),
    )
    if updated.rowcount != 1:
        return "That child was not found."
    conn.commit()
    return None


def _required(value: str, label: str, limit: int) -> tuple[str | None, str | None]:
    cleaned = (value or "").strip()
    if not cleaned:
        return None, f"{label} is required."
    if len(cleaned) > limit:
        return None, f"{label} is too long."
    return cleaned, None


def _date(value: str, label: str) -> tuple[str | None, str | None]:
    cleaned = (value or "").strip()
    if not cleaned:
        return None, f"{label} is required."
    try:
        date.fromisoformat(cleaned)
    except ValueError:
        return None, f"{label} must be a date."
    return cleaned, None


def resolve_scope(conn: sqlite3.Connection, raw: str, *, shared_ok: bool) -> tuple[int | None, str | None]:
    if raw == "both" and shared_ok:
        return None, None
    if raw.isdigit():
        row = conn.execute("SELECT id FROM children WHERE id = ?", (int(raw),)).fetchone()
        if row:
            return row["id"], None
    if shared_ok:
        return None, "Choose a child or Both."
    return None, "Choose a child."


def scope_clause(mode: str, child_id: int | None, *, shared: bool) -> tuple[str, list]:
    if mode == "all":
        return "", []
    if mode == "missing":
        if shared:
            return " AND child_id IS NULL", []
        return " AND 0 = 1", []
    if shared:
        return " AND (child_id IS NULL OR child_id = ?)", [child_id]
    return " AND child_id = ?", [child_id]


def window_bounds(today: date | None = None) -> tuple[str, str]:
    start = today or date.today()
    return start.isoformat(), (start + timedelta(days=WINDOW_DAYS)).isoformat()


def child_label(children: list[sqlite3.Row], child_id: int | None) -> str:
    if child_id is None:
        return "Both"
    for child in children:
        if child["id"] == child_id:
            return child["name"]
    return "Unknown"


def upcoming_items(conn: sqlite3.Connection, mode: str, child_id: int | None, today: date | None = None) -> list[dict]:
    start, end = window_bounds(today)
    event_sql, event_params = scope_clause(mode, child_id, shared=True)
    assignment_sql, assignment_params = scope_clause(mode, child_id, shared=False)
    events = conn.execute(
        f"""
        SELECT id, child_id, kind, title, destination, notes, event_on
        FROM events
        WHERE event_on >= ? AND event_on <= ? {event_sql}
        """,
        [start, end, *event_params],
    ).fetchall()
    assignments = conn.execute(
        f"""
        SELECT id, child_id, subject, title, due_on, status
        FROM assignments
        WHERE due_on >= ? AND due_on <= ? {assignment_sql}
        """,
        [start, end, *assignment_params],
    ).fetchall()
    children = list_children(conn)
    items = []
    for event in events:
        items.append(
            {
                "on": event["event_on"],
                "kind": event["kind"],
                "title": event["title"],
                "detail": event["destination"] or "",
                "notes": event["notes"] or "",
                "who": child_label(children, event["child_id"]),
                "href": f"/events/{event['id']}/edit",
            }
        )
    for assignment in assignments:
        items.append(
            {
                "on": assignment["due_on"],
                "kind": "assignment",
                "title": assignment["title"],
                "detail": assignment["subject"],
                "notes": "",
                "who": child_label(children, assignment["child_id"]),
                "href": f"/assignments/{assignment['id']}/edit",
            }
        )
    items.sort(key=lambda item: (item["on"], item["title"]))
    return items


def recent_communications(conn: sqlite3.Connection, mode: str, child_id: int | None) -> list[sqlite3.Row]:
    clause, params = scope_clause(mode, child_id, shared=True)
    return conn.execute(
        f"""
        SELECT id, child_id, title, body, source, link, occurred_on
        FROM communications
        WHERE 1 = 1 {clause}
        ORDER BY occurred_on DESC, id DESC
        LIMIT {RECENT_LIMIT}
        """,
        params,
    ).fetchall()


def list_rows(conn: sqlite3.Connection, table: str, date_column: str, mode: str, child_id: int | None, *, shared: bool) -> list[sqlite3.Row]:
    clause, params = scope_clause(mode, child_id, shared=shared)
    return conn.execute(
        f"SELECT * FROM {table} WHERE 1 = 1 {clause} ORDER BY {date_column} DESC, id DESC",
        params,
    ).fetchall()


def get_row(conn: sqlite3.Connection, table: str, row_id: int) -> sqlite3.Row | None:
    return conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()


def save_communication(conn: sqlite3.Connection, data: dict, row_id: int | None = None) -> str | None:
    child_id, error = resolve_scope(conn, data["child_id"], shared_ok=True)
    if error:
        return error
    occurred_on, error = _date(data["occurred_on"], "Date")
    if error:
        return error
    title, error = _required(data["title"], "Title", 200)
    if error:
        return error
    body, error = _required(data["body"], "Body", 4000)
    if error:
        return error
    source, error = _required(data.get("source") or "Manual", "Source", 80)
    if error:
        return error
    link = (data.get("link") or "").strip() or None
    if link and len(link) > 500:
        return "Link is too long."
    values = (child_id, title, body, source, link, occurred_on)
    if row_id is None:
        conn.execute(
            """
            INSERT INTO communications
                (child_id, title, body, source, link, occurred_on, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (*values, _now()),
        )
    else:
        updated = conn.execute(
            """
            UPDATE communications
            SET child_id = ?, title = ?, body = ?, source = ?, link = ?, occurred_on = ?
            WHERE id = ?
            """,
            (*values, row_id),
        )
        if updated.rowcount != 1:
            return "That communication was not found."
    conn.commit()
    return None


def save_event(conn: sqlite3.Connection, data: dict, row_id: int | None = None) -> str | None:
    child_id, error = resolve_scope(conn, data["child_id"], shared_ok=True)
    if error:
        return error
    if data["kind"] not in {"field_trip", "milestone", "other"}:
        return "Choose a kind."
    event_on, error = _date(data["event_on"], "Date")
    if error:
        return error
    title, error = _required(data["title"], "Title", 200)
    if error:
        return error
    destination = (data.get("destination") or "").strip() or None
    notes = (data.get("notes") or "").strip() or None
    if destination and len(destination) > 200:
        return "Destination is too long."
    if notes and len(notes) > 1000:
        return "Note is too long."
    values = (child_id, data["kind"], title, destination, notes, event_on)
    if row_id is None:
        conn.execute(
            """
            INSERT INTO events
                (child_id, kind, title, destination, notes, event_on, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (*values, _now()),
        )
    else:
        updated = conn.execute(
            """
            UPDATE events
            SET child_id = ?, kind = ?, title = ?, destination = ?, notes = ?, event_on = ?
            WHERE id = ?
            """,
            (*values, row_id),
        )
        if updated.rowcount != 1:
            return "That event was not found."
    conn.commit()
    return None


def save_assignment(conn: sqlite3.Connection, data: dict, row_id: int | None = None) -> str | None:
    child_id, error = resolve_scope(conn, data["child_id"], shared_ok=False)
    if error:
        return error
    subject, error = _required(data["subject"], "Subject", 80)
    if error:
        return error
    title, error = _required(data["title"], "Title", 200)
    if error:
        return error
    due_on, error = _date(data["due_on"], "Due date")
    if error:
        return error
    status = data.get("status") or "not_started"
    if status not in {"not_started", "done"}:
        return "Choose a status."
    values = (child_id, subject, title, due_on, status)
    if row_id is None:
        conn.execute(
            """
            INSERT INTO assignments
                (child_id, subject, title, due_on, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (*values, _now()),
        )
    else:
        updated = conn.execute(
            """
            UPDATE assignments
            SET child_id = ?, subject = ?, title = ?, due_on = ?, status = ?
            WHERE id = ?
            """,
            (*values, row_id),
        )
        if updated.rowcount != 1:
            return "That assignment was not found."
    conn.commit()
    return None


def save_grade(conn: sqlite3.Connection, data: dict, row_id: int | None = None) -> str | None:
    child_id, error = resolve_scope(conn, data["child_id"], shared_ok=False)
    if error:
        return error
    subject, error = _required(data["subject"], "Subject", 80)
    if error:
        return error
    score, error = _required(data["score_text"], "Score", 40)
    if error:
        return error
    term, error = _required(data["term"], "Term", 40)
    if error:
        return error
    recorded_on, error = _date(data["recorded_on"], "Recorded date")
    if error:
        return error
    values = (child_id, subject, score, term, recorded_on)
    if row_id is None:
        conn.execute(
            """
            INSERT INTO grades
                (child_id, subject, score_text, term, recorded_on, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (*values, _now()),
        )
    else:
        updated = conn.execute(
            """
            UPDATE grades
            SET child_id = ?, subject = ?, score_text = ?, term = ?, recorded_on = ?
            WHERE id = ?
            """,
            (*values, row_id),
        )
        if updated.rowcount != 1:
            return "That grade was not found."
    conn.commit()
    return None


def delete_row(conn: sqlite3.Connection, table: str, row_id: int) -> None:
    if table == "communications":
        conn.execute(
            "UPDATE gmail_imports SET communication_id = NULL WHERE communication_id = ?",
            (row_id,),
        )
    conn.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
    conn.commit()


def list_rules(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT id, kind, value FROM school_mail_rules ORDER BY id"
    ).fetchall()


def add_rule(conn: sqlite3.Connection, kind: str, value: str) -> str | None:
    chosen = (kind or "").strip()
    raw = (value or "").strip()
    if chosen not in {"sender", "domain", "label"}:
        return "Choose a sender, domain, or label."
    if not raw:
        return "Value is blank."
    if len(raw) > 200:
        return "Value is too long."
    if chosen == "sender":
        local, separator, domain = raw.partition("@")
        if separator != "@" or not local or not domain or "@" in domain or " " in raw:
            return f'"{raw}" is not a sender.'
        stored = raw.casefold()
    elif chosen == "domain":
        stored = raw[1:] if raw.startswith("@") else raw
        stored = stored.casefold()
        if not stored or "@" in stored or " " in stored:
            return f'"{raw}" is not a domain.'
    else:
        stored = raw
    try:
        conn.execute(
            "INSERT INTO school_mail_rules (kind, value, created_at) VALUES (?, ?, ?)",
            (chosen, stored, _now()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return f'"{stored}" is already saved.'
    return None


def delete_rule(conn: sqlite3.Connection, rule_id: int) -> None:
    conn.execute("DELETE FROM school_mail_rules WHERE id = ?", (rule_id,))
    conn.commit()


def last_success_on(conn: sqlite3.Connection) -> date | None:
    row = conn.execute("SELECT last_success_on FROM gmail_checkpoint WHERE id = 1").fetchone()
    if row is None or not row["last_success_on"]:
        return None
    return date.fromisoformat(row["last_success_on"])


def gmail_communication_ids(conn: sqlite3.Connection) -> set[int]:
    rows = conn.execute(
        "SELECT communication_id FROM gmail_imports WHERE communication_id IS NOT NULL"
    ).fetchall()
    return {row["communication_id"] for row in rows}


def gmail_id_for(conn: sqlite3.Connection, communication_id: int) -> str | None:
    row = conn.execute(
        "SELECT gmail_id FROM gmail_imports WHERE communication_id = ?",
        (communication_id,),
    ).fetchone()
    return row["gmail_id"] if row else None


def latest_grade_ids(rows: list[sqlite3.Row]) -> set[int]:
    best: dict[tuple[int, str], sqlite3.Row] = {}
    for row in rows:
        key = (row["child_id"], row["subject"])
        current = best.get(key)
        if current is None or (row["recorded_on"], row["id"]) > (current["recorded_on"], current["id"]):
            best[key] = row
    return {row["id"] for row in best.values()}


def load_sample(conn: sqlite3.Connection, today: date | None = None) -> str | None:
    if child_count(conn) > 0:
        return "Sample data was not loaded because children already exist."
    today = today or date.today()
    add_child(conn, "Lila")
    add_child(conn, "Nora")
    children = {row["name"]: row["id"] for row in list_children(conn)}
    lila = children["Lila"]
    nora = children["Nora"]
    save_event(
        conn,
        {
            "child_id": "both",
            "kind": "field_trip",
            "event_on": (today + timedelta(days=3)).isoformat(),
            "title": "Science museum trip",
            "destination": "Science museum",
            "notes": "Permission slip",
        },
    )
    save_event(
        conn,
        {
            "child_id": str(lila),
            "kind": "milestone",
            "event_on": (today - timedelta(days=1)).isoformat(),
            "title": "Picture day",
            "destination": "",
            "notes": "",
        },
    )
    save_assignment(
        conn,
        {
            "child_id": str(lila),
            "subject": "Math",
            "title": "Worksheet 4",
            "due_on": (today + timedelta(days=1)).isoformat(),
            "status": "not_started",
        },
    )
    save_grade(
        conn,
        {
            "child_id": str(nora),
            "subject": "Reading",
            "score_text": "A-",
            "term": "Fall",
            "recorded_on": (today - timedelta(days=2)).isoformat(),
        },
    )
    save_communication(
        conn,
        {
            "child_id": str(lila),
            "occurred_on": (today - timedelta(days=1)).isoformat(),
            "title": "Teacher note",
            "body": "Please send a water bottle.",
            "source": "Manual",
            "link": "",
        },
    )
    return None

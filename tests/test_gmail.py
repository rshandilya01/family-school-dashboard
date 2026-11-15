import base64
import json
import re
import sqlite3
from datetime import date, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi.testclient import TestClient

from app.db import connect, init_db
from app.gmail import build_list_query, normalize
from app.main import create_app


class FakeMailbox:
    def __init__(self):
        self.messages = []
        self.calls = []
        self.error = None

    def list_messages(self, *, rules, since):
        self.calls.append(("list", [dict(rule) for rule in rules], since.isoformat()))
        if self.error:
            raise RuntimeError(self.error)
        return list(self.messages)

    def get_message(self, gmail_id):
        self.calls.append(("get", gmail_id))
        if self.error:
            raise RuntimeError(self.error)
        for message in self.messages:
            if message["id"] == gmail_id:
                return message
        return None


def _message(
    gmail_id,
    *,
    sender="Teacher <teacher@school.org>",
    subject="Library note",
    body="Please send the book.",
    sent_on=None,
    labels=None,
    inbox=True,
    spam=False,
    trash=False,
    sent=False,
    drafts=False,
    parts=None,
    html=None,
):
    name, email = sender.split("<", 1)
    return {
        "id": gmail_id,
        "from_name": name.strip().strip('"'),
        "from_email": email.rstrip(">").strip(),
        "subject": subject,
        "sent_on": sent_on or date.today().isoformat(),
        "labels": labels or [],
        "in_inbox": inbox,
        "in_spam": spam,
        "in_trash": trash,
        "in_sent": sent,
        "in_drafts": drafts,
        "in_chat": False,
        "plain": body,
        "html": html,
        "parts": parts or [],
    }


@pytest.fixture
def mailbox():
    return FakeMailbox()


@pytest.fixture
def token_path(tmp_path):
    return tmp_path / "gmail_token.json"


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "school.db"


@pytest.fixture
def client(db_path, mailbox, token_path):
    app = create_app(str(db_path), mailbox=mailbox, token_path=str(token_path))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("Gmail tests must not open a network connection")

    monkeypatch.setattr(httpx, "Client", refuse)
    monkeypatch.setattr(httpx, "get", refuse)
    monkeypatch.setattr(httpx, "post", refuse)


def _ids(client):
    client.post("/children", data={"name": "Lila"})
    client.post("/children", data={"name": "Nora"})
    html = client.get("/children").text
    found = dict(re.findall(r'data-child-name="([^"]+)" data-child-id="(\d+)"', html))
    return found["Lila"], found["Nora"]


def _connect(token_path, email="parent@home.test"):
    token_path.write_text(json.dumps({"refresh_token": "test-refresh", "email": email}))


def _rules(client, kind, value):
    response = client.post("/gmail/rules", data={"kind": kind, "value": value})
    assert response.status_code == 200
    return response


def _rows(db_path):
    conn = connect(str(db_path))
    try:
        return conn.execute(
            "SELECT id, child_id, title, body, source, sender_name, sender_email, link FROM communications ORDER BY id"
        ).fetchall()
    finally:
        conn.close()


def _counts(db_path):
    conn = connect(str(db_path))
    try:
        return {
            table: conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
            for table in ("communications", "events", "assignments", "grades")
        }
    finally:
        conn.close()


def test_existing_database_gains_mail_tables(tmp_path):
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE communications (
            id INTEGER PRIMARY KEY,
            child_id INTEGER,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            source TEXT NOT NULL,
            link TEXT,
            occurred_on TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    init_db(conn)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(communications)")}
    assert {"sender_name", "sender_email"} <= columns
    assert conn.execute("SELECT id, last_success_on FROM gmail_checkpoint").fetchone() == (1, None)
    conn.close()


def test_list_query_excludes_folders_outside_the_school_window():
    query = build_list_query(
        [
            {"kind": "sender", "value": "teacher@school.org"},
            {"kind": "domain", "value": "school.org"},
            {"kind": "label", "value": "field-trip"},
        ],
        date(2026, 11, 1),
    )
    for token in ("-in:spam", "-in:trash", "-in:sent", "-in:drafts", "-in:chats"):
        assert token in query
    assert "from:teacher@school.org" in query
    assert "label:field-trip" in query
    assert "after:2026/10/31" in query


def test_normalize_reads_text_and_does_not_keep_attachment_bytes():
    plain = base64.urlsafe_b64encode(b"Hello Nora").decode().rstrip("=")
    raw = {
        "id": "abc",
        "labelIds": ["INBOX"],
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [
                {"name": "From", "value": "Teacher <teacher@school.org>"},
                {"name": "Subject", "value": "Hello"},
                {"name": "Date", "value": "Sun, 15 Nov 2026 12:00:00 -0500"},
            ],
            "parts": [
                {"mimeType": "text/plain", "body": {"data": plain}},
                {
                    "mimeType": "text/html",
                    "body": {"data": base64.urlsafe_b64encode(b"<p>ignored</p>").decode().rstrip("=")},
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "slip.pdf",
                    "body": {"attachmentId": "ATT", "size": 10},
                },
            ],
        },
    }
    message = normalize(raw)
    assert message["from_email"] == "teacher@school.org"
    assert message["plain"] == "Hello Nora"
    assert message["parts"] == [{"filename": "slip.pdf", "disposition": ""}]
    assert "ATT" not in json.dumps(message["parts"])


def test_fictional_import_copies_school_mail_once(client, mailbox, token_path, db_path, tmp_path):
    lila, nora = _ids(client)
    _connect(token_path)
    _rules(client, "sender", "teacher@school.org")
    long_body = "N" * 5001
    mailbox.messages = [
        _message("one-child", subject="Nora library book", body="The book is due."),
        _message("neither", subject="Early dismissal", body="Friday is a half day."),
        _message(
            "other",
            sender="Stranger <stranger@example.net>",
            subject="ZEBRA-PICNIC-9941",
            body="Bring the zebra chips.",
        ),
        _message("blank", subject="  ", body="No title here."),
        _message("long", subject="Long note", body=long_body, parts=[{"filename": "slip.pdf", "disposition": "attachment"}]),
        _message("old", subject="Ancient note", body="Too old.", sent_on=(date.today() - timedelta(days=31)).isoformat()),
        _message("html-only", subject="Formatted", body=None, html="<p>Hello Nora</p><script>secret()</script>"),
    ]
    mailbox.messages[6]["plain"] = None
    before = {call[0] for call in mailbox.calls}
    assert before == set()
    assert client.get("/").status_code == 200
    assert mailbox.calls == []

    checked = client.post("/gmail/check")
    assert checked.status_code == 200
    rows = _rows(db_path)
    titles = {row["title"] for row in rows}
    assert titles == {"Nora library book", "Early dismissal", "(no subject)", "Long note", "Formatted"}
    blob = " ".join(f"{row['title']} {row['body']} {row['sender_email']}" for row in rows)
    assert "ZEBRA-PICNIC-9941" not in blob
    assert "zebra chips" not in blob
    assert "stranger@example.net" not in blob
    assert "Ancient note" not in blob

    by_title = {row["title"]: row for row in rows}
    assert by_title["Nora library book"]["child_id"] == int(nora)
    assert by_title["Early dismissal"]["child_id"] is None
    assert by_title["(no subject)"]["source"] == "Gmail"
    assert by_title["Long note"]["body"].startswith("N" * 5000)
    assert "This message was shortened." in by_title["Long note"]["body"]
    assert "This message has attachments." in by_title["Long note"]["body"]
    assert "secret()" not in by_title["Formatted"]["body"]
    assert "Hello Nora" in by_title["Formatted"]["body"]
    assert by_title["Nora library book"]["sender_email"] == "teacher@school.org"
    assert all(row["source"] == "Gmail" for row in rows)
    assert _counts(db_path) == {"communications": 5, "events": 0, "assignments": 0, "grades": 0}
    assert not (tmp_path / "slip.pdf").exists()

    home = client.get(f"/?child={nora}").text
    assert re.search(r"Nora library book.+Gmail", home, re.S)
    both = client.get("/communications?child=all").text
    assert "Early dismissal" in both
    assert "Nora library book" in both
    hidden = client.get(f"/communications?child={lila}").text
    assert "Nora library book" not in hidden
    assert "Early dismissal" in hidden
    assert "Open in Gmail" in client.get("/communications").text

    again = client.post("/gmail/check")
    assert again.status_code == 200
    assert len(_rows(db_path)) == 5
    assert {call[0] for call in mailbox.calls} <= {"list", "get"}

    copied = by_title["Nora library book"]
    opened = client.get(f"/communications/{copied['id']}/original", follow_redirects=False)
    assert opened.status_code == 302
    assert opened.headers["location"] == copied["link"]
    mailbox.messages = [message for message in mailbox.messages if message["id"] != "one-child"]
    missing = client.get(f"/communications/{copied['id']}/original")
    assert "The original could not be opened." in missing.text
    assert "Nora library book" in missing.text
    assert len(_rows(db_path)) == 5


def test_rules_folders_and_removed_rules(client, mailbox, token_path, db_path):
    _ids(client)
    _connect(token_path)
    mailbox.messages = [
        _message("sender", sender="Coach <coach@school.org>", subject="Practice", body="Bring shoes."),
    ]
    refused = client.post("/gmail/check")
    assert refused.status_code == 400
    assert "Name a sender, domain, or label." in refused.text
    assert _counts(db_path)["communications"] == 0
    assert mailbox.calls == []

    blank = client.post("/gmail/rules", data={"kind": "sender", "value": "  "})
    assert blank.status_code == 400
    assert "blank" in blank.text
    invalid = client.post("/gmail/rules", data={"kind": "domain", "value": "not a domain"})
    assert invalid.status_code == 400
    assert "not a domain" in invalid.text
    assert "not a domain" not in client.get("/gmail").text

    _rules(client, "domain", "@school.org")
    mailbox.messages = [
        _message("exact", sender="Teacher <teacher@school.org>", subject="Exact domain"),
        _message("sub", sender="Teacher <teacher@mail.school.org>", subject="Subdomain skipped"),
        _message("label-hit", sender="Office <office@example.net>", subject="Label hit", labels=["Field-Trip"]),
        _message("spam", subject="Spam note", spam=True, inbox=False),
        _message("trash", subject="Trash note", trash=True, inbox=False),
        _message("archived", subject="Archived note", inbox=False),
        _message("sent-box", subject="Sent note", sent=True, inbox=False),
        _message("from-self", sender="Parent <parent@home.test>", subject="My own note"),
    ]
    client.post("/gmail/check")
    titles = {row["title"] for row in _rows(db_path)}
    assert "Exact domain" in titles
    assert "Archived note" in titles
    assert "Subdomain skipped" not in titles
    assert "Spam note" not in titles
    assert "Trash note" not in titles
    assert "Sent note" not in titles
    assert "My own note" not in titles
    assert "Label hit" not in titles

    _rules(client, "label", "field-trip")
    client.post("/gmail/check")
    titles = {row["title"] for row in _rows(db_path)}
    assert "Label hit" in titles
    kept = len(titles)
    rule_page = client.get("/gmail").text
    rule_id = re.search(r"/gmail/rules/(\d+)/delete", rule_page).group(1)
    client.post(f"/gmail/rules/{rule_id}/delete")
    assert "Exact domain" in {row["title"] for row in _rows(db_path)}
    assert len(_rows(db_path)) == kept


def test_connect_disconnect_and_authorize_url(client, mailbox, token_path, db_path, monkeypatch):
    _ids(client)
    lonely = client.get("/gmail")
    assert "Gmail is not connected." in lonely.text
    assert 'type="password"' not in lonely.text
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("PORT", "8000")
    started = client.get("/gmail/connect", follow_redirects=False)
    assert started.status_code == 302
    parsed = urlparse(started.headers["location"])
    params = parse_qs(parsed.query)
    assert params["redirect_uri"][0] == "http://127.0.0.1:8000/gmail/callback"
    assert params["scope"][0] == "https://www.googleapis.com/auth/gmail.readonly"
    assert params["code_challenge_method"][0] == "S256"
    assert parsed.netloc == "accounts.google.com"

    _connect(token_path, "parent@home.test")
    _rules(client, "sender", "teacher@school.org")
    mailbox.messages = [_message("once", subject="One copy")]
    connected = client.get("/gmail")
    assert "parent@home.test" in connected.text
    assert "Gmail connected" in connected.text
    client.post("/gmail/check")
    assert len(_rows(db_path)) == 1

    calls = len(mailbox.calls)
    client.post("/gmail/disconnect")
    assert not token_path.exists()
    assert len(_rows(db_path)) == 1
    blocked = client.post("/gmail/check")
    assert blocked.status_code == 400
    assert "Gmail is not connected." in blocked.text
    assert len(mailbox.calls) == calls

    _connect(token_path, "parent@home.test")
    client.post("/gmail/check")
    assert len(_rows(db_path)) == 1
    assert {call[0] for call in mailbox.calls} <= {"list", "get"}


def test_edits_and_deletes_stick(client, mailbox, token_path, db_path):
    _lila, nora = _ids(client)
    _connect(token_path)
    _rules(client, "sender", "teacher@school.org")
    mailbox.messages = [
        _message("edit-me", subject="Original title", body="Short body."),
        _message("delete-me", subject="Delete me", body="Gone soon."),
    ]
    client.post("/gmail/check")
    rows = {row["title"]: row for row in _rows(db_path)}
    edited = rows["Original title"]
    removed = rows["Delete me"]
    saved = client.post(
        f"/communications/{edited['id']}",
        data={
            "child_id": nora,
            "occurred_on": date.today().isoformat(),
            "title": "Corrected title",
            "body": edited["body"],
            "source": "Gmail",
            "link": edited["link"] or "",
        },
    )
    assert saved.status_code == 200
    calls = len(mailbox.calls)
    client.post("/gmail/check")
    current = {row["id"]: row for row in _rows(db_path)}
    assert current[edited["id"]]["title"] == "Corrected title"
    assert current[edited["id"]]["child_id"] == int(nora)
    assert len(mailbox.calls) > calls

    confirm = client.get(f"/communications/{removed['id']}/delete")
    assert "Delete this?" in confirm.text
    client.get("/communications")
    assert "Delete me" in client.get("/communications").text

    client.post(f"/communications/{removed['id']}/delete")
    client.post("/gmail/check")
    titles = {row["title"] for row in _rows(db_path)}
    assert "Delete me" not in titles
    assert "Corrected title" in titles
    conn = connect(str(db_path))
    try:
        leftover = conn.execute(
            "SELECT communication_id FROM gmail_imports WHERE gmail_id = 'delete-me'"
        ).fetchone()
    finally:
        conn.close()
    assert leftover["communication_id"] is None
    assert {call[0] for call in mailbox.calls} <= {"list", "get"}


def test_failed_check_leaves_the_dashboard_alone(client, mailbox, token_path, db_path):
    client.post("/children", data={"name": "Lila"})
    today = date.today().isoformat()
    client.post(
        "/communications",
        data={
            "child_id": "1",
            "occurred_on": today,
            "title": "Already listed",
            "body": "Hand entered.",
            "source": "Manual",
            "link": "",
        },
    )
    _connect(token_path)
    _rules(client, "sender", "teacher@school.org")
    mailbox.messages = [_message("later", subject="After the failure")]
    mailbox.error = "the mailbox could not be read"
    failed = client.post("/gmail/check")
    assert failed.status_code == 400
    assert "the mailbox could not be read" in failed.text
    assert [row["title"] for row in _rows(db_path)] == ["Already listed"]
    conn = connect(str(db_path))
    try:
        assert conn.execute("SELECT last_success_on FROM gmail_checkpoint").fetchone()["last_success_on"] is None
    finally:
        conn.close()

    mailbox.error = None
    client.post("/gmail/check")
    client.post("/gmail/check")
    titles = [row["title"] for row in _rows(db_path)]
    assert titles.count("After the failure") == 1
    assert "Already listed" in titles


def test_names_match_as_whole_phrases(client, mailbox, token_path, db_path):
    client.post("/children", data={"name": "Ann"})
    client.post("/children", data={"name": "Mary Jane"})
    html = client.get("/children").text
    found = dict(re.findall(r'data-child-name="([^"]+)" data-child-id="(\d+)"', html))
    _connect(token_path)
    _rules(client, "sender", "teacher@school.org")
    mailbox.messages = [
        _message("anniversary", subject="Anniversary party", body="Bring a card."),
        _message("ann", subject="Note for Ann", body="Choir today."),
        _message("full", subject="Hello Mary Jane", body="Art show."),
        _message("one-word", subject="Mary won the prize", body="Congratulations."),
    ]
    client.post("/gmail/check")
    rows = {row["title"]: row["child_id"] for row in _rows(db_path)}
    assert rows["Anniversary party"] is None
    assert rows["Note for Ann"] == int(found["Ann"])
    assert rows["Hello Mary Jane"] == int(found["Mary Jane"])
    assert rows["Mary won the prize"] is None


def test_no_children_and_startup_do_not_check(mailbox, token_path, db_path):
    app = create_app(str(db_path), mailbox=mailbox, token_path=str(token_path))
    with TestClient(app) as client:
        assert mailbox.calls == []
        assert client.get("/").status_code == 200
        assert client.get("/gmail").status_code == 200
        assert mailbox.calls == []
        _connect(token_path)
        blocked = client.post("/gmail/check")
        assert blocked.status_code == 400
        assert "Add a child first." in blocked.text
        assert mailbox.calls == []

"""Decide which fictional or live messages become communications."""

from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser

from app.db import last_success_on, list_children, list_rules

BODY_LIMIT = 5000
WINDOW_DAYS = 30
GMAIL_LINK = "https://mail.google.com/mail/u/0/#all/{gmail_id}"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"script", "style"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)


def html_to_text(source: str) -> str:
    parser = _TextExtractor()
    parser.feed(source or "")
    parser.close()
    return "".join(parser.parts)


def readable_text(message: dict) -> str:
    plain = message.get("plain")
    if plain is not None:
        return plain
    return html_to_text(message.get("html") or "")


def has_attachment(message: dict) -> bool:
    for part in message.get("parts") or []:
        filename = (part.get("filename") or "").strip()
        disposition = (part.get("disposition") or "").lower()
        if filename or "attachment" in disposition:
            return True
    return False


def stored_body(message: dict) -> str:
    text = readable_text(message)
    chunks = []
    if text[:BODY_LIMIT]:
        chunks.append(text[:BODY_LIMIT])
    if len(text) > BODY_LIMIT:
        chunks.append("This message was shortened.")
    if has_attachment(message):
        chunks.append("This message has attachments.")
    return "\n".join(chunks)


def message_title(message: dict) -> str:
    subject = (message.get("subject") or "").strip()
    return subject or "(no subject)"


def sent_on(message: dict, today: date) -> date:
    raw = message.get("sent_on")
    if not raw:
        return today
    return date.fromisoformat(raw)


def _name_in_text(name: str, text: str) -> bool:
    pattern = re.compile(rf"(?<!\w){re.escape(name)}(?!\w)", re.IGNORECASE)
    return pattern.search(text) is not None


def child_id_for(children: list[sqlite3.Row], message: dict) -> int | None:
    names = [(child["id"], (child["name"] or "").strip()) for child in children]
    folded = [name.casefold() for _, name in names if name]
    if len(folded) >= 2 and len(set(folded)) == 1:
        return None
    text = f"{message.get('subject') or ''}\n{readable_text(message)}"
    matched = [child_id for child_id, name in names if len(name) >= 3 and _name_in_text(name, text)]
    if len(matched) == 1:
        return matched[0]
    return None


def _blocked_folder(message: dict) -> bool:
    return any(
        message.get(flag)
        for flag in ("in_spam", "in_trash", "in_sent", "in_drafts", "in_chat")
    )


def rule_matches(message: dict, rules: list[dict]) -> bool:
    email = (message.get("from_email") or "").casefold()
    labels = [(label or "").casefold() for label in message.get("labels") or []]
    for rule in rules:
        kind = rule["kind"]
        value = (rule["value"] or "").casefold()
        if kind == "sender" and email == value:
            return True
        if kind == "domain" and value and email.endswith("@" + value):
            return True
        if kind == "label" and value in labels:
            return True
    return False


def date_allowed(sent: date, today: date, previous: date | None) -> bool:
    if sent > today:
        return False
    in_window = (today - sent).days <= WINDOW_DAYS
    if previous is None:
        return in_window
    return sent > previous or in_window


def list_since(today: date, previous: date | None) -> date:
    start = today - timedelta(days=WINDOW_DAYS)
    if previous is not None and previous < start:
        return previous
    return start


def eligible(message: dict, *, rules: list[dict], address: str, today: date, previous: date | None) -> bool:
    if _blocked_folder(message):
        return False
    sender = (message.get("from_email") or "").casefold()
    if address and sender == address.casefold():
        return False
    if not rule_matches(message, rules):
        return False
    return date_allowed(sent_on(message, today), today, previous)


def run_check(conn: sqlite3.Connection, mailbox, *, address: str, today: date | None = None) -> None:
    today = today or date.today()
    rules = [dict(row) for row in list_rules(conn)]
    children = list_children(conn)
    previous = last_success_on(conn)
    messages = mailbox.list_messages(rules=rules, since=list_since(today, previous))
    known = {
        row["gmail_id"]
        for row in conn.execute("SELECT gmail_id FROM gmail_imports")
    }
    created = datetime.now(timezone.utc).isoformat()
    try:
        for message in messages:
            gmail_id = message["id"]
            if gmail_id in known:
                continue
            if not eligible(message, rules=rules, address=address, today=today, previous=previous):
                continue
            occurred = sent_on(message, today).isoformat()
            cursor = conn.execute(
                """
                INSERT INTO communications
                    (child_id, title, body, source, link, occurred_on, created_at, sender_name, sender_email)
                VALUES (?, ?, ?, 'Gmail', ?, ?, ?, ?, ?)
                """,
                (
                    child_id_for(children, message),
                    message_title(message),
                    stored_body(message),
                    GMAIL_LINK.format(gmail_id=gmail_id),
                    occurred,
                    created,
                    (message.get("from_name") or "").strip() or None,
                    (message.get("from_email") or "").strip() or None,
                ),
            )
            conn.execute(
                """
                INSERT INTO gmail_imports (gmail_id, communication_id, created_at)
                VALUES (?, ?, ?)
                """,
                (gmail_id, cursor.lastrowid, created),
            )
            known.add(gmail_id)
        conn.execute(
            "UPDATE gmail_checkpoint SET last_success_on = ? WHERE id = 1",
            (today.isoformat(),),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

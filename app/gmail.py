"""Read-only Gmail OAuth and message fetch. Tests use a fake mailbox instead."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from datetime import date, datetime
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlencode

import httpx

READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
LIST_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"


def read_token(path: str) -> dict | None:
    file = Path(path)
    if not file.is_file():
        return None
    try:
        data = json.loads(file.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not data.get("refresh_token") or not data.get("email"):
        return None
    return data


def write_token(path: str, refresh_token: str, email: str) -> None:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({"refresh_token": refresh_token, "email": email}))
    file.chmod(0o600)


def delete_token(path: str) -> None:
    Path(path).unlink(missing_ok=True)


def connected_address(path: str) -> str | None:
    token = read_token(path)
    if token is None:
        return None
    return token["email"]


def code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def new_oauth_state() -> tuple[str, str]:
    state = secrets.token_urlsafe(24)
    verifier = secrets.token_urlsafe(64)
    return state, verifier


def authorize_url(*, client_id: str, redirect_uri: str, state: str, verifier: str) -> str:
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": READONLY_SCOPE,
            "code_challenge": code_challenge(verifier),
            "code_challenge_method": "S256",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    return f"{AUTH_URL}?{query}"


def build_list_query(rules: list[dict], since: date) -> str:
    start = since.toordinal() - 1
    after = date.fromordinal(start).strftime("%Y/%m/%d")
    pieces = [
        "-in:spam",
        "-in:trash",
        "-in:sent",
        "-in:drafts",
        "-in:chats",
        f"after:{after}",
    ]
    terms = []
    for rule in rules:
        value = rule["value"]
        if rule["kind"] == "label":
            terms.append(f"label:{value}")
        else:
            terms.append(f"from:{value}")
    if terms:
        pieces.append("(" + " OR ".join(terms) + ")")
    return " ".join(pieces)


def _decode(data: str) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _walk(part: dict, texts: dict, attachments: list[dict]) -> None:
    filename = part.get("filename") or ""
    disposition = ""
    for header in part.get("headers") or []:
        if (header.get("name") or "").lower() == "content-disposition":
            disposition = header.get("value") or ""
    if filename or "attachment" in disposition.lower():
        attachments.append({"filename": filename, "disposition": disposition})
    body = (part.get("body") or {}).get("data")
    mime = part.get("mimeType") or ""
    if mime == "text/plain" and body and "plain" not in texts:
        texts["plain"] = _decode(body)
    elif mime == "text/html" and body and "html" not in texts:
        texts["html"] = _decode(body)
    for child in part.get("parts") or []:
        _walk(child, texts, attachments)


def normalize(api_message: dict, label_names: list[str] | None = None) -> dict:
    payload = api_message.get("payload") or {}
    headers = {
        (header.get("name") or "").lower(): header.get("value") or ""
        for header in payload.get("headers") or []
    }
    name, address = parseaddr(headers.get("from", ""))
    texts: dict[str, str] = {}
    attachments: list[dict] = []
    if payload:
        _walk(payload, texts, attachments)
    label_ids = set(api_message.get("labelIds") or [])
    sent = None
    if headers.get("date"):
        try:
            sent = parsedate_to_datetime(headers["date"]).astimezone().date().isoformat()
        except (TypeError, ValueError, OverflowError):
            sent = None
    if sent is None and api_message.get("internalDate"):
        sent = datetime.fromtimestamp(int(api_message["internalDate"]) / 1000).astimezone().date().isoformat()
    return {
        "id": api_message["id"],
        "from_name": name,
        "from_email": address,
        "subject": headers.get("subject"),
        "sent_on": sent,
        "labels": list(label_names or []),
        "in_inbox": "INBOX" in label_ids,
        "in_spam": "SPAM" in label_ids,
        "in_trash": "TRASH" in label_ids,
        "in_sent": "SENT" in label_ids,
        "in_drafts": "DRAFT" in label_ids,
        "in_chat": "CHAT" in label_ids,
        "plain": texts.get("plain"),
        "html": texts.get("html"),
        "parts": attachments,
    }


class GmailClient:
    """Live mailbox. Only the token endpoint, profile, list, and get are called."""

    def __init__(self, token_path: str) -> None:
        self.token_path = token_path
        self._access_token = ""

    @property
    def address(self) -> str:
        token = read_token(self.token_path)
        return token["email"] if token else ""

    def list_messages(self, *, rules: list[dict], since: date) -> list[dict]:
        label_names: dict[str, list[str]] = {}
        ordered: list[str] = []
        seen: set[str] = set()
        plain_rules = [rule for rule in rules if rule["kind"] != "label"]
        groups = []
        if plain_rules:
            groups.append((plain_rules, None))
        for rule in rules:
            if rule["kind"] == "label":
                groups.append(([rule], rule["value"]))
        for group, label in groups:
            for gmail_id in self._list_ids(build_list_query(group, since)):
                if label:
                    label_names.setdefault(gmail_id, [])
                    if label not in label_names[gmail_id]:
                        label_names[gmail_id].append(label)
                if gmail_id not in seen:
                    seen.add(gmail_id)
                    ordered.append(gmail_id)
        messages = []
        for gmail_id in ordered:
            message = self.get_message(gmail_id)
            if message is None:
                continue
            message["labels"] = label_names.get(gmail_id, [])
            messages.append(message)
        return messages

    def get_message(self, gmail_id: str) -> dict | None:
        response = self._request("GET", f"{LIST_URL}/{gmail_id}", params={"format": "full"})
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return normalize(response.json())

    def _list_ids(self, query: str) -> list[str]:
        ids: list[str] = []
        page = None
        while True:
            params = {"q": query, "maxResults": 100}
            if page:
                params["pageToken"] = page
            response = self._request("GET", LIST_URL, params=params)
            response.raise_for_status()
            payload = response.json()
            ids.extend(item["id"] for item in payload.get("messages") or [])
            page = payload.get("nextPageToken")
            if not page:
                return ids

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._bearer()}"
        with httpx.Client(timeout=30) as client:
            return client.request(method, url, headers=headers, **kwargs)

    def _bearer(self) -> str:
        if self._access_token:
            return self._access_token
        token = read_token(self.token_path)
        if token is None:
            raise RuntimeError("Gmail is not connected.")
        client_id = _env("GOOGLE_CLIENT_ID")
        client_secret = _env("GOOGLE_CLIENT_SECRET")
        with httpx.Client(timeout=30) as client:
            response = client.post(
                TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": token["refresh_token"],
                    "grant_type": "refresh_token",
                },
            )
        response.raise_for_status()
        self._access_token = response.json()["access_token"]
        return self._access_token


def _env(name: str) -> str:
    import os

    return os.environ.get(name, "")


def exchange_code(*, client_id: str, client_secret: str, code: str, verifier: str, redirect_uri: str) -> tuple[str, str]:
    with httpx.Client(timeout=30) as client:
        response = client.post(
            TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "code_verifier": verifier,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    response.raise_for_status()
    payload = response.json()
    refresh = payload.get("refresh_token") or ""
    access = payload.get("access_token") or ""
    if not refresh or not access:
        raise RuntimeError("Gmail did not return a permission.")
    return refresh, access


def fetch_address(access_token: str) -> str:
    with httpx.Client(timeout=30) as client:
        response = client.get(PROFILE_URL, headers={"Authorization": f"Bearer {access_token}"})
    response.raise_for_status()
    email = response.json().get("emailAddress") or ""
    if not email:
        raise RuntimeError("Gmail did not return a mailbox address.")
    return email

# Quickstart: Gmail School Mail

Validation guide for copying school mail into the local dashboard. Fields and routes are in [data-model.md](./data-model.md) and [contracts/ui.md](./contracts/ui.md).

## Prerequisites

- Python 3.11 or newer
- `uv` on the path
- The dashboard from `specs/001-family-dashboard/quickstart.md` already runs on `127.0.0.1`

From the repository root:

```bash
uv sync
```

Automated checks do not need a Google account. A live mailbox is only for the optional manual check below.

## Automated checks

```bash
uv run pytest
```

Expected:

- Existing child-filter, upcoming-window, and restart tests still pass.
- Fictional Gmail messages: a matching inbox or archived message is copied, a non-matching message is not stored, and spam or trash is not stored.
- A second check does not add a second copy. An edited title stays. A confirmed delete stays gone.
- A message that names one fictional child is hidden when the other child is selected, and a message that names neither child shows for both.
- A failed fictional read leaves the list and the last success date unchanged.
- The fake mailbox records no send, delete, archive, relabel, or read-state change.
- No test uses a real student name or opens a network connection to Gmail.

## Run the app

```bash
uv run python -m app.seed
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Sample data still does not connect a mailbox.

## Optional live mailbox

1. Create a Google desktop OAuth client whose redirect URI is `http://127.0.0.1:8000/gmail/callback`.
2. Put the client id and secret in `.env` as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. Do not commit that file.
3. Open `/gmail`, connect one mailbox, add one school sender, and run Check mail.
4. Confirm a matching message appears under Communications with source Gmail, and Open in Gmail opens that message.
5. Disconnect. The copied communication remains. Check mail copies nothing until you connect again.
6. Confirm `data/gmail_token.json` and `data/school.db` are not tracked by git.

## Out of scope for this check

Canvas, TalkingPoints, sending mail, and saving attachment files are not part of this feature.

# Research: Gmail School Mail

## Decision: Read Gmail with httpx, not a Google SDK

- **Decision**: Call the Gmail REST API with the `httpx` package already in the project. Scope is `https://www.googleapis.com/auth/gmail.readonly`. Allowed calls are the token endpoint, `users.getProfile`, `users.messages.list`, and `users.messages.get`. No send, modify, trash, batch modify, label create, or attachment download.
- **Rationale**: The constitution asks for the smallest app that meets the spec. `httpx` is already used by the test client. A readonly scope cannot send or change mail. `messages.get` does not clear the unread flag; the check must not call a method that does.
- **Alternatives considered**: `google-api-python-client` pulls a larger stack for a handful of GET requests. IMAP with an app password is a second login model and still has to avoid `STORE` so messages stay unread. A hosted relay would leave this computer.

## Decision: OAuth on this computer, token under data/

- **Decision**: Desktop OAuth with PKCE. The browser returns to `http://127.0.0.1:{port}/gmail/callback` on the running app. `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` live in `.env`. The refresh token and mailbox address live in `data/gmail_token.json`. Disconnect deletes that file. Copied communications and the import-identity rows stay.
- **Rationale**: The spec asks the parent to allow one mailbox and to take that permission away without deleting school records. `data/` and `.env` are already gitignored. The client id is the app registration; the refresh token is the mailbox permission.
- **Alternatives considered**: Storing the refresh token inside `school.db` mixes the permission with school records and makes "delete the permission" a row delete that is easier to get wrong. A second Google account is out of scope.

## Decision: Gmail search narrows; local rules decide

- **Decision**: The list query excludes spam, trash, sent, drafts, and chats, and starts at the earlier of the previous successful check date and today minus 30 days. It ORs the parent's senders, domains, and labels. Before any insert, `mail.py` keeps a message only when all of these hold: it is in the inbox or archived; it is not spam, trash, sent, or drafts; From is not the connected mailbox; a sender rule matches the address exactly, or a domain rule matches an address that ends with `@` plus that exact domain, or a label name matches; the date rule in the data model passes. Messages that fail are dropped in memory. Their sender, subject, and body are not written.
- **Rationale**: The parent asked the check to look far enough to find school mail and to keep nothing else. Gmail's `from:school.org` also matches subdomains, but the spec copies only addresses that end with `@school.org`. `alice@mail.school.org` does not end with `@school.org`. The local check is the one tests assert.
- **Alternatives considered**: Trusting the Gmail query alone would copy subdomain mail and would be hard to test without Google. Downloading the whole mailbox and filtering afterward keeps non-school bodies in the process longer than this feature needs.

## Decision: Remember the Gmail id after delete

- **Decision**: `gmail_imports.gmail_id` is the identity of a copied message. A later check inserts nothing when that id already exists. Deleting the communication sets the link to null and leaves the id row, so the message is not copied again. A check never updates title, body, child, sender, or link on a row that already exists. Hand-entered communications have no Gmail id and are not rewritten.
- **Rationale**: The spec requires one copy, sticky edits, and sticky deletes, including after the parent disconnects and connects again.
- **Alternatives considered**: Matching on subject and date collapses two different messages with the same subject. Deleting the id row on delete would bring the message back on the next check.

## Decision: One transaction, then the check date

- **Decision**: The Gmail client returns the full candidate list or raises. On raise, the database is unchanged and `last_success_on` stays put. On success, inserts and the new check date commit together. No children, no rules, or no token: the page explains why, and Gmail is not called.
- **Rationale**: A failed check must not leave a partial copy or skip mail that arrived during the failure. The parent starts each check with a POST. Startup and page views do not check.
- **Alternatives considered**: Saving each message as it arrives would keep a partial list when the network drops. A background timer would check while the parent did not ask.

## Decision: Plain text in the standard library

- **Decision**: Use the `text/plain` part when it exists. Otherwise strip HTML with `html.parser` and drop script and style. Keep the first 5,000 characters of that text. If it was longer, add a line that the message was shortened. If any part has a filename or an attachment disposition, add a line that the message has attachments. Do not call the attachments endpoint and do not write files. A blank subject is stored as `(no subject)`. A missing sent date uses today's date on this computer.
- **Rationale**: The spec wants readable text, a hard length, and a note instead of the files. Another parser dependency is unused.
- **Alternatives considered**: Saving HTML would show formatting code in the body. Downloading attachments would store school files the spec leaves in Gmail.

## Decision: Child scope from the display name

- **Decision**: If the two children share a display name, ignoring case, file the message as both. Otherwise consider only names of at least 3 characters. A name matches when it appears in the subject or body as a whole phrase, case insensitive, and not as part of a longer word. Exactly one match selects that child. Zero or two matches file the message once with a null child id.
- **Rationale**: This is the spec's rule, including short names and shared names. Null child id is already how a shared communication is stored.
- **Alternatives considered**: Matching any word of a two-word name would file "Mary" mail to "Mary Jane". A review queue would add a screen this feature does not require, because the parent can edit the child afterward and the edit sticks.

## Decision: Open original through a local route

- **Decision**: Copied messages show "Open in Gmail". That route calls `messages.get` with a minimal format. If the message is still there, the browser is redirected to `https://mail.google.com/mail/u/0/#all/{gmail_id}`. If the get fails or the message is gone, the dashboard shows that the original could not be opened and leaves the communication in place. The link field is filled with that Gmail URL only when the row is created. Later checks do not change it. The route keys off `gmail_id`, so an edited link still has a working Open action.
- **Rationale**: The parent needs the full message and its files, and those files stay in Gmail. A minimal get does not change unread state. The parent's later visit in Gmail's own site is the parent opening the message, not the check writing back.
- **Alternatives considered**: Only storing a URL would leave a dead link with no sentence from the dashboard when the message is gone. Copying attachments locally contradicts the spec.

## Decision: Tests use a fake mailbox

- **Decision**: `create_app` accepts a mailbox object and a token-file path. Production uses `gmail.py` and `data/gmail_token.json`. Tests pass fictional messages and a temporary token path. The suite covers matching, child scope, duplicates, deletes, edits, spam and trash, archived mail, truncation, the attachment note, a failed check, and the absence of any mutate call on the fake.
- **Rationale**: The spec requires those checks with no live mailbox and no real student names. The existing upcoming-window tests stay as they are.
- **Alternatives considered**: Recording a live Gmail session would put school mail in the test suite and would fail offline.

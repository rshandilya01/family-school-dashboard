# Tasks: Gmail School Mail

**Input**: Design documents from `/specs/002-gmail-school-mail/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required by spec FR-018. Matching, child scope, and duplicate suppression must be verified with fictional messages and no live mailbox. The constitution also requires automated coverage of child filtering.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested on its own.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (for example US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- Single project at the repository root with `app/` and `tests/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Name the Gmail client settings without committing a secret

- [x] T001 Add blank `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` to `.env.example` beside the existing `DATABASE_PATH` and `PORT` entries

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema and app seam that every mail story uses

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Add mail tables and columns in `app/db.py`, including an `init_db` migration for an existing database: nullable `communications.sender_name` and `communications.sender_email`; `school_mail_rules` with `kind` of `sender`, `domain`, or `label`, `value` trimmed, non-blank, and at most 200 characters, sender and domain stored lowercase, and the same kind and value rejected twice; `gmail_imports` with `gmail_id` text primary key, nullable `communication_id`, and `created_at`; `gmail_checkpoint` as one row whose `id` is always `1` and whose `last_success_on` is a nullable calendar date
- [x] T003 [P] Extend `create_app` in `app/main.py` to accept an optional mailbox and a token path defaulting to `data/gmail_token.json`, and do not check mail during startup

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Bring school mail onto the dashboard (Priority: P1) 🎯 MVP

**Goal**: A check copies matching inbox mail into communications, files it to one child or both, and does not store anything else

**Independent Test**: With fictional messages and no live mailbox, one check copies a matching message for one child and a matching message that names neither child, skips a non-matching message, and a second check adds no duplicate. The fake mailbox records no send, delete, archive, relabel, or read-state change.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T004 [US1] Fictional import test in `tests/test_gmail.py` for a sender match, a non-matching message whose sender, subject, and body are absent from the database, child scope, a second check with zero new copies, a blank subject stored as `(no subject)`, a body longer than 5,000 characters, an attachment note with no file written, source `Gmail` on the home list, and no new event, assignment, or grade

### Implementation for User Story 1

- [x] T005 [US1] Implement body text, child scope, and the import transaction in `app/mail.py`: readable text at most 5,000 characters, then a line that the message was shortened when the source was longer, plus a line that the message has attachments when a part has a filename or an attachment disposition; attachment bytes are not stored; a missing sent date uses today on this computer; shared display names, compared after trim and without regard to case, file the message as both; otherwise only names of at least 3 characters can match, as a whole phrase and not inside a longer word; exactly one match sets `child_id` and zero or two matches set `child_id` null; insert the communication and `gmail_imports` row together; skip a `gmail_id` that already exists; do not update an existing communication; set `last_success_on` to today only in that same successful commit; with no successful check yet, copy a date that is today or within the previous 30 days and not after today
- [x] T006 [US1] Add `POST /gmail/check` and the mail page in `app/main.py`, `app/templates/gmail.html`, and a header link in `app/templates/base.html`
- [x] T007 [US1] Show the sender name and address on copied rows in `app/templates/communications.html`, and add `GET /communications/{id}/original` in `app/main.py` that redirects to `https://mail.google.com/mail/u/0/#all/{gmail_id}` when the message exists and otherwise shows "The original could not be opened." without removing the communication

**Checkpoint**: User Story 1 is testable on its own with a fictional mailbox and one inserted sender rule

---

## Phase 4: User Story 2 - Choose what counts as school mail (Priority: P1)

**Goal**: The parent adds and removes sender, domain, and label rules, and a check copies only mail those rules allow

**Independent Test**: With fictional messages, no rules copies nothing. A sender, a domain, and a label each copy only the newly matching message. An archived match is copied. Spam, trash, and mail the parent sent are not. Removing a rule leaves an already copied communication in place.

### Tests for User Story 2

- [x] T008 [US2] Rule and folder tests in `tests/test_gmail.py`: no rules leaves the database unchanged and the page says "Name a sender, domain, or label."; `teacher@school.org` matches domain `school.org` and `teacher@mail.school.org` does not; a label matches without regard to case; a message in spam or trash is not copied; an archived matching message is copied; a message the parent sent, or whose From is the connected mailbox, is not copied; deleting a rule does not delete the communication

### Implementation for User Story 2

- [x] T009 [P] [US2] Add and remove school-mail rules in `app/db.py`: `kind` is `sender`, `domain`, or `label`; `value` is trimmed, non-blank, and at most 200 characters; a sender contains one `@` with text on both sides; a domain is stored without a leading `@`, without spaces, and without `@`; sender and domain are stored lowercase; the same kind and value is rejected; removing a rule does not delete communications
- [x] T010 [P] [US2] Extend the copy filter in `app/mail.py` so a message is kept only when it is in the inbox or archived, is not spam, trash, sent, or drafts, From is not the connected mailbox, and a sender, exact `@domain`, or label rule matches
- [x] T011 [US2] Add the rule form, `POST /gmail/rules`, and `POST /gmail/rules/{id}/delete` in `app/main.py` and `app/templates/gmail.html`, and redisplay the page with a message that names a blank or invalid value without inserting it

**Checkpoint**: User Stories 1 and 2 both work on a fictional mailbox

---

## Phase 5: User Story 3 - Connect and disconnect Gmail (Priority: P2)

**Goal**: The parent allows one mailbox on this computer and can remove that permission without losing copied mail

**Independent Test**: Connect, copy one fictional matching message, disconnect, confirm the communication remains, confirm a check copies nothing, connect again, and confirm that message is not duplicated

### Tests for User Story 3

- [x] T012 [US3] Connection tests in `tests/test_gmail.py`: a token file shows the mailbox address and "Gmail connected" with no dashboard login; disconnect deletes the token file, leaves the communication, and a check says "Gmail is not connected."; reconnecting does not insert a second copy; the authorize URL uses `http://127.0.0.1` and scope `https://www.googleapis.com/auth/gmail.readonly`; the test opens no network connection

### Implementation for User Story 3

- [x] T013 [US3] Implement the read-only client in `app/gmail.py`: desktop OAuth with PKCE, redirect `http://127.0.0.1:{port}/gmail/callback`, refresh token and mailbox address in `data/gmail_token.json`, and only the token endpoint, `users.getProfile`, `users.messages.list`, and `users.messages.get`. The list query excludes spam, trash, sent, drafts, and chats. Do not call send, modify, trash, batch modify, label create, or the attachments endpoint
- [x] T014 [US3] Add `GET /gmail/connect`, `GET /gmail/callback`, and `POST /gmail/disconnect` in `app/main.py`, and show "Gmail is not connected" or the connected address in `app/templates/gmail.html`

**Checkpoint**: Disconnect removes only the permission. Copied mail and import rows remain

---

## Phase 6: User Story 4 - Keep the parent's corrections (Priority: P2)

**Goal**: A later check does not undo an edit or bring back a deleted communication

**Independent Test**: Change a copied message to the other child and edit the title, run the check, and confirm both changes remain. Confirm delete, run the check, and confirm it stays gone. Cancel delete and confirm the row remains

### Tests for User Story 4

- [x] T015 [US4] Edit and delete tests in `tests/test_gmail.py` using the existing confirm-delete flow: an edited child and title survive a later check, a confirmed delete stays gone, a canceled delete leaves the communication, and the fake mailbox is unchanged

### Implementation for User Story 4

- [x] T016 [US4] When a Gmail communication is confirmed deleted, keep the `gmail_imports` row in `app/db.py` and set `communication_id` null. `app/mail.py` must not change title, body, child, sender, or link for a `gmail_id` that already exists

**Checkpoint**: Corrections stick across a later check

---

## Phase 7: User Story 5 - A failed check leaves the dashboard alone (Priority: P3)

**Goal**: A mailbox error saves nothing and does not move the success date

**Independent Test**: With communications already listed, a failed read leaves the list unchanged and shows a plain reason. The next successful check copies an eligible message that was never copied. A household with no children copies nothing.

### Tests for User Story 5

- [x] T017 [US5] Failure tests in `tests/test_gmail.py`: a raising mailbox leaves communications and `last_success_on` unchanged and the page explains the failure; the next success copies the eligible message once; no children copies nothing and the page says "Add a child first."; opening the app does not run a check

### Implementation for User Story 5

- [x] T018 [US5] In `app/mail.py` and `app/main.py`, treat a mailbox exception as a failed check with no commit and no change to `last_success_on`. Before calling the mailbox, no children returns "Add a child first." and no token returns "Gmail is not connected."

**Checkpoint**: All five stories work with a fictional mailbox

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Document the optional live mailbox and confirm the automated path

- [x] T019 [P] Note in `README.md` that Gmail is an optional read-only check, with the run steps from `specs/002-gmail-school-mail/quickstart.md`
- [x] T020 Run `uv run pytest` from `specs/002-gmail-school-mail/quickstart.md` and confirm `data/` and `.env` remain ignored by git

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories
- **User Stories (Phase 3+)**: Depend on Foundational. Implement in priority order P1 → P2 → P3
- **Polish (Phase 8)**: Depends on the user stories whose behavior the quickstart runs

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational. No dependency on later stories
- **User Story 2 (P1)**: After User Story 1, because it extends the filter in `app/mail.py` and the form in `app/templates/gmail.html`
- **User Story 3 (P2)**: After User Story 2 for `app/main.py` and `app/templates/gmail.html`. `app/gmail.py` itself needs only the foundational token path
- **User Story 4 (P2)**: After User Story 1, because it changes how `gmail_imports` behaves on delete
- **User Story 5 (P3)**: After User Story 1, because it covers a failed import and the checkpoint row

### Within Each User Story

- Tests are written and fail before that story's implementation
- `app/mail.py` and `app/db.py` before the routes that call them
- `app/gmail.py` before the connect routes

### Parallel Opportunities

- T002 and T003 touch different files and can run together
- T006 and T007 both edit `app/main.py`, so T007 follows T006
- T009 and T010 can run together after T008
- T013 can be written while User Story 2 is in progress, and wired in T014 afterward
- Later story edits to `app/main.py`, `app/mail.py`, and `app/templates/gmail.html` stay sequential

---

## Parallel Example: User Story 2

```bash
# After T008 is written and failing, different files can proceed together:
Task: "Add and remove school-mail rules in app/db.py"
Task: "Extend the copy filter in app/mail.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2
2. Complete Phase 3 and run the fictional import test
3. Stop and confirm a non-matching message is not stored and a second check adds no copy

### Incremental Delivery

1. Setup and Foundational are the shared schema and app seam
2. User Story 1 copies mail with a fictional mailbox
3. User Story 2 lets the parent name the school rules
4. User Story 3 connects a real mailbox and disconnects without deleting copies
5. User Story 4 keeps edits and deletes
6. User Story 5 keeps a failed check from writing a partial list
7. Polish runs the full pytest suite from the quickstart

### Parallel Team Strategy

After Foundational:

- One person finishes User Story 1, then User Story 2, because they share `app/mail.py`
- Another person can draft `app/gmail.py` (T013) during User Story 2, then connect it in User Story 3

## Notes

- [P] tasks use different files
- Tests for a story are written before that story's routes
- The check is read-only toward Gmail. Canvas and TalkingPoints stay uncalled
- Do not commit `.env`, `data/school.db`, or `data/gmail_token.json`

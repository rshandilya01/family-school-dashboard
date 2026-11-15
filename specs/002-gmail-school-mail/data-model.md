# Data Model: Gmail School Mail

Dates are ISO calendar dates (`YYYY-MM-DD`) on the computer where the app runs. This feature adds columns and tables to the model in `specs/001-family-dashboard/data-model.md`. Children, events, assignments, and grades are unchanged.

## Communication (added fields)

| Field | Required | Rules |
|-------|----------|--------|
| sender_name | no | Display name from the message. Blank for hand entry |
| sender_email | no | Address from the message. Blank for hand entry |

Existing fields still apply. A copied message sets `source` to `Gmail`, `title` to the subject or `(no subject)`, `body` to the readable text plus the shortening and attachment notes, `link` to the Gmail URL at insert time, and `occurred_on` to the sent date or to today when the sent date is missing. A later check does not update these fields.

## School mail rule

| Field | Required | Rules |
|-------|----------|--------|
| id | yes | Integer identity |
| kind | yes | `sender`, `domain`, or `label` |
| value | yes | Trimmed, non-blank, at most 200 characters. Stored lowercase for `sender` and `domain` |
| created_at | yes | Set when the row is inserted |

A `sender` value must contain one `@`, with text on both sides. A `domain` value is the part after `@` only; a leading `@` is removed before save. A `domain` value must not contain `@` or spaces. The same kind and value cannot be stored twice. Removing a rule does not delete communications already copied.

## Gmail import

| Field | Required | Rules |
|-------|----------|--------|
| gmail_id | yes | Text identity of one Gmail message. Primary key |
| communication_id | no | The communication created from that message. Null after the parent deletes it |
| created_at | yes | Set when the row is inserted |

One Gmail message maps to at most one communication. If `gmail_id` is already present, a check does not insert again and does not revive a null `communication_id`. Deleting the communication keeps this row and sets `communication_id` null. Hand-entered communications have no import row.

## Check checkpoint

One row.

| Field | Required | Rules |
|-------|----------|--------|
| id | yes | Always `1` |
| last_success_on | no | Calendar date of the last check that finished. Null until the first success |

A failed check, a check with no token, a check with no children, and a check with no rules leave this value unchanged.

## Mailbox connection

Not a database table. `data/gmail_token.json` holds the refresh token and the mailbox address when Gmail is connected. The file is absent when it is not. Disconnect deletes the file and does not delete communications, rules, import rows, or the checkpoint.

## What a check copies

A candidate is copied only when every rule below is true. Otherwise nothing about that message is written.

1. Folder is inbox, or archived (not inbox, and not spam, trash, sent, or drafts).
2. From address is not the connected mailbox address.
3. A saved rule matches:
   - `sender`: the From address equals the value, ignoring case.
   - `domain`: the From address ends with `@` plus the value. `teacher@school.org` matches `school.org`. `teacher@mail.school.org` does not.
   - `label`: a label name on the message equals the value, ignoring case.
4. The message has no `gmail_imports` row.
5. Date, using the sent date, or today when it is missing:
   - No successful check yet: the date is today or within the previous 30 days, and it is not after today. A date 31 days before today is out.
   - After a success: the date is after `last_success_on`, or the date is today or within the previous 30 days and not after today.

The readable body is at most 5,000 characters. When the source text is longer, the stored body ends with a line that the message was shortened. When the message has an attachment, the stored body says so. Attachment bytes are not stored.

## Child scope

Shared display names, compared after trim and without regard to case, file the message as both (`child_id` null).

Otherwise a child name is eligible when it is at least 3 characters. It matches when the subject or body contains that full name as its own phrase, without regard to case, and not inside a longer word. `Ann` does not match `Anniversary`. A two-word name matches that phrase, not one word of it.

Exactly one matching child sets `child_id`. Zero or two matches set `child_id` null. Names that are not one of the two children are ignored.

## State changes

- Connect: write the token file. Do not copy mail.
- Disconnect: delete the token file. Leave communications and `gmail_imports`.
- Add or remove rule: change `school_mail_rules` only.
- Check success: insert any new communications and import rows, then set `last_success_on` to today, in one commit.
- Check failure: no insert, no checkpoint change.
- Edit communication: the parent's fields stay. The import row stays pointed at that communication.
- Confirm delete: the communication row goes away. The import row remains with a null communication id.
- Cancel delete: no change.

## Relationships

- A school mail rule stands alone.
- A Gmail import belongs to at most one communication.
- A copied communication belongs to one child or to both, the same filter as any other communication.
- Events, assignments, and grades are not created by a check.

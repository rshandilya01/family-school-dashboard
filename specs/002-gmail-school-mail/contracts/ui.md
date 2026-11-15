# UI Contract: Gmail School Mail

Server-rendered HTML, same as `specs/001-family-dashboard/contracts/ui.md`. Writes use POST, then redirect. A check that cannot run redisplays the mail page with a plain message and does not change stored communications.

The child filter on communications and home is unchanged.

## Pages

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/gmail` | Whether Gmail is connected, the mailbox address when it is, the school rules, and the check form |
| GET | `/gmail/connect` | Send the browser to Google to allow read-only access. Redirect target is this app on `127.0.0.1` |
| GET | `/gmail/callback` | Store the permission and return to `/gmail`. On failure, `/gmail` explains it |
| POST | `/gmail/disconnect` | Delete the permission on this computer and return to `/gmail` |
| POST | `/gmail/rules` | Add one school rule |
| POST | `/gmail/rules/{id}/delete` | Remove that rule. Communications already copied stay |
| POST | `/gmail/check` | Copy matching school mail, or explain why nothing was copied |
| GET | `/communications/{id}/original` | Open that copied message in Gmail, or say the original could not be opened |

`/gmail` is linked from the shared page header. Home, events, assignments, grades, and children gain no new forms.

## Form fields

- Rule: `kind` (`sender`, `domain`, or `label`), `value`
- Check and disconnect: no fields. The button is the action.

## Visible labels

- Connected mailbox: the address, and the words Gmail connected
- Not connected: Gmail is not connected
- Rule kinds: Sender, Domain, Label
- Copied source: Gmail
- Sender line on a copied communication: the sender name and address when present
- Open action: Open in Gmail
- Attachment note in the body: This message has attachments.
- Shortened note in the body: This message was shortened.

Hand-entered communications stay labeled Manual and do not show Open in Gmail.

## Messages

- No permission: "Gmail is not connected."
- No children: "Add a child first."
- No rules: "Name a sender, domain, or label."
- Gmail could not be read: a plain sentence naming the failure. The communications list is unchanged.
- A rule value is blank or is not a sender or domain as required: the mail page names what is wrong and does not insert the rule.
- Original missing or unreadable: "The original could not be opened." The communication remains.

## Read-only boundary

The check and the open action do not send, reply, delete, archive, label, or change read state. Opening a message that still exists redirects the browser to Gmail. The dashboard does not save attachment files.

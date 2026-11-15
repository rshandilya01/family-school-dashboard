# Feature Specification: Gmail School Mail

**Feature Branch**: `002-gmail-school-mail`

**Created**: 2026-11-15

**Status**: Draft

**Input**: User description: "I want to connect dashboard with gmail emails for school communication"

## Clarifications

### Session 2026-11-15

- Q: When the dashboard checks Gmail, what should happen to messages that do not match the parent's school rules? → A: Look through the mailbox far enough to find matches, save only the matching school messages, and keep nothing else.
- Q: Which messages in Gmail should a check be allowed to consider for school mail? → A: Messages in the inbox and messages the parent has archived. Skip spam and trash.
- Q: From a copied school message, should the parent be able to open the original in Gmail? → A: Each copied message includes a way to open the original in Gmail.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bring school mail onto the dashboard (Priority: P1)

The parent has already allowed Gmail on this computer and named at least one school sender, school domain, or Gmail label. They ask the dashboard to check mail. Matching messages in the inbox or in archived mail become communications. Spam and trash are skipped. Each copied message includes a way to open the original in Gmail. A message that names one child is filed to that child. A message that names both, or neither, is filed once as both. Hand-entered communications stay as they are.

**Why this priority**: The dashboard exists so the parent can see school messages without hunting through a mailbox. Copying those messages in is the whole point of this feature.

**Independent Test**: Using fictional messages and no live mailbox, run one check against a set that includes a matching school message for one child, a matching message that names neither child, and a message from someone else. Confirm only the two school messages appear, with the right child scope, that a second check does not add a second copy of either, that each copied message includes a way to open the original, and that the fictional mailbox records no send, delete, archive, relabel, or read-state change.

**Acceptance Scenarios**:

1. **Given** Gmail is allowed, one school sender is saved, and fictional messages include one matching message from the last 30 days and one non-matching message from the last 30 days, **When** the parent checks mail, **Then** only the matching message appears as a communication labeled Gmail, and the other message does not.
2. **Given** a matching message whose subject or body names exactly one child as a whole name, **When** the parent checks mail, **Then** that communication appears for that child and on Both, and is hidden when the other child is selected.
3. **Given** a matching message that names both children, or neither child, **When** the parent checks mail, **Then** one communication is stored and it appears for either child and on Both, labeled as both.
4. **Given** a matching message was already copied, **When** the parent checks mail again, **Then** the communications list does not gain a second copy of that message.
5. **Given** a check finishes, **When** the parent looks at the mailbox that was read, **Then** the same messages are still there, with the same read or unread state, and nothing was sent, deleted, archived, or relabeled.
6. **Given** a matching message with a blank subject, a readable text longer than 5,000 characters, and an attached file, **When** the parent checks mail, **Then** the title is "(no subject)", the body is the first 5,000 characters of readable text, the communication says the message was shortened and that a file was attached, and the file is not saved on this computer.
7. **Given** an imported communication is one of the eight newest, **When** the parent opens the home view on a child scope that includes it, **Then** it appears there, and the check has not created an event, an assignment, or a grade.
8. **Given** a copied school message with an attached file, **When** the parent uses its way to open the original, **Then** that message opens in Gmail and the file remains in Gmail.
9. **Given** a copied school message whose original can no longer be opened, **When** the parent tries to open it, **Then** the copied communication remains and the dashboard says the original could not be opened.

---

### User Story 2 - Choose what counts as school mail (Priority: P1)

The parent decides which mail is school mail. They add or remove a sender address, a school domain (the part after @), or a Gmail label. Until at least one of those is saved, a check copies nothing. Mail the parent sent is never copied. Changing the rules does not remove communications already copied. The next check uses the new rules.

**Why this priority**: A full inbox is not school communication. The parent has to be able to keep the dashboard limited to school mail before the first copy is trustworthy.

**Independent Test**: With fictional messages, save no rules and confirm a check copies nothing. Add one sender, one domain, and one label across three checks and confirm each check copies only the newly matching message. Remove a rule and confirm the next check does not copy a message that only matched the removed rule, and that an already copied communication stays. Confirm an archived matching message is copied, and a matching message in spam or trash is not.

**Acceptance Scenarios**:

1. **Given** Gmail is allowed and no school sender, domain, or label is saved, **When** the parent checks mail, **Then** nothing is copied and the dashboard tells the parent to name a sender, domain, or label.
2. **Given** a sender address is saved, **When** the parent checks mail, **Then** a received message from that address is copied and a received message from any other address is not, unless it matches another saved rule.
3. **Given** a school domain is saved, **When** the parent checks mail, **Then** a received message whose sender address ends with @ that domain is copied.
4. **Given** a Gmail label is saved, **When** the parent checks mail, **Then** a received message with that label is copied, and a message without that label is not copied unless it matches a sender or domain.
5. **Given** a message the parent sent matches a rule, **When** the parent checks mail, **Then** that sent message is not copied.
6. **Given** a communication was already copied and the parent then removes the rule that matched it, **When** the parent checks mail, **Then** that communication remains.
7. **Given** a message that does not match any school rule, **When** the parent checks mail, **Then** that message is not copied, and its sender, subject, and body are not kept.
8. **Given** one matching school message in the inbox and another matching school message the parent has archived, **When** the parent checks mail, **Then** both are copied.
9. **Given** a matching school message in spam and a matching school message in trash, **When** the parent checks mail, **Then** neither is copied.

---

### User Story 3 - Connect and disconnect Gmail (Priority: P2)

The parent allows the dashboard to read one Gmail mailbox from this computer, sees that it is connected, and can disconnect. Disconnecting leaves every copied communication in place, removes the permission from this computer, and later checks copy nothing until the parent connects again. The dashboard still has no login of its own. The permission stays on this computer only, and the fictional sample never includes a mailbox permission or real student mail.

**Why this priority**: Import is useful only after the parent can grant access and take it away. The copied school records matter more than the live link, so disconnecting must not throw them away.

**Independent Test**: Connect, confirm a check can copy a fictional matching message, disconnect, confirm the copied communication is still listed, confirm a check copies nothing, then connect again and confirm the same message is not duplicated.

**Acceptance Scenarios**:

1. **Given** Gmail is not connected, **When** the parent connects one mailbox on this computer, **Then** the dashboard shows that Gmail is connected, still does not ask for a separate dashboard login, still opens only on this computer, and does not ask the parent to share usage data.
2. **Given** Gmail is connected and a school message was copied, **When** the parent disconnects, **Then** the copied communication remains, the dashboard shows that Gmail is not connected, and the permission is gone from this computer.
3. **Given** Gmail is not connected, **When** the parent checks mail, **Then** nothing new is copied and the dashboard says Gmail is not connected.
4. **Given** the parent disconnected and later connects the same mailbox again, **When** the parent checks mail, **Then** messages already copied are not copied again.

---

### User Story 4 - Keep the parent's corrections (Priority: P2)

The parent can correct an imported communication the same way as a hand-entered one: change the child, the title, or the body, or delete it after confirming. A later check does not undo that correction, does not bring back a deleted item, and does not change the original Gmail message.

**Why this priority**: Name matching will sometimes file a message as both, or the parent will want a clearer title. Those corrections have to stick or the parent will stop trusting the list.

**Independent Test**: Copy a fictional message filed to one child, change it to the other child and edit the title, run the check again, and confirm the edited title and the new child remain. Delete another imported communication, confirm the deletion, run the check again, and confirm it stays gone.

**Acceptance Scenarios**:

1. **Given** an imported communication, **When** the parent changes its child, title, or body and then checks mail, **Then** the list shows the correction and Gmail is unchanged.
2. **Given** an imported communication, **When** the parent confirms deletion and then checks mail, **Then** the communication stays deleted and is not copied again.
3. **Given** the parent starts deleting an imported communication and then cancels, **When** the list reloads, **Then** the communication is still there.

---

### User Story 5 - A failed check leaves the dashboard alone (Priority: P3)

If Gmail cannot be read, the parent sees a plain explanation. Communications already on the dashboard stay. Nothing new is saved. The next successful check can still pick up school messages it has not copied, including ones that arrived while checks were failing.

**Why this priority**: A bad connection must not wipe or half-write the school list. Recovering on the next good check matters once the happy path works.

**Independent Test**: With communications already listed, run a check that cannot read the mailbox, confirm the list is unchanged and a reason is shown, then run a successful check that includes one new matching message and one older matching message that was never copied, and confirm both appear once.

**Acceptance Scenarios**:

1. **Given** communications already exist and Gmail cannot be read, **When** the parent checks mail, **Then** the list is unchanged and the dashboard explains the failure in plain language.
2. **Given** a check failed and a matching school message that the dashboard has not copied is still eligible, **When** the next check succeeds, **Then** that message is copied once.
3. **Given** the household has no children, **When** the parent checks mail, **Then** nothing is copied and the dashboard tells the parent to add a child first.
4. **Given** the dashboard is closed, **When** time passes, **Then** no mail check runs.

---

### Edge Cases

- A check runs only when the parent asks, and only while the dashboard is open. Closing the dashboard does not check mail.
- The first successful check copies matching received messages dated today or within the previous 30 days. A message dated 31 days before that first check is not copied. After that, a check copies a matching received message that was never copied and was not deleted by the parent when its date is after the previous successful check, or when its date is still today or within the previous 30 days. A failed check does not move the previous successful check forward. Adding a school rule later in that 30-day window copies a matching message the earlier check skipped.
- A message with a blank subject is titled "(no subject)".
- If the sent date is missing, the communication uses the date the dashboard copied it.
- The saved body is ordinary readable text. Formatting code is not shown as the body. If the readable text is longer than 5,000 characters, the dashboard keeps the first 5,000 and says the message was shortened.
- If a message has attachments, the communication says so. The files are not saved on this computer. The parent uses the way to open the original in Gmail to see those files.
- If the original can no longer be opened, the copied communication stays and the dashboard says the original could not be opened.
- A child's name matches only as a whole word or full phrase, ignoring case. "Ann" does not match "Anniversary". A two-word display name matches that phrase, not one of the words alone.
- If both children share the same display name, or the only name that would match is shorter than 3 characters, the communication is filed as both.
- Names that are not one of the two children are ignored.
- Two matching messages with the same subject and different sent times are both copied.
- An imported communication uses the same child filter as every other list: one child, or Both. On home it can appear among the eight newest communications. It does not create an event, an assignment, or a grade.
- The parent can still add a communication by hand. Hand-entered items stay labeled Manual unless the parent changes that label. A check never rewrites them.
- Fictional sample data does not connect to a real mailbox and does not contain real student mail.
- A check may look through the mailbox far enough to tell which messages match. A message that does not match is not copied, and its sender, subject, and body are not kept.
- A matching message in the inbox or in archived mail can be copied. A matching message in spam or trash is not copied. A school message already copied stays on the dashboard if the parent later archives it, marks it as spam, or moves it to trash in Gmail.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The parent MUST be able to connect one Gmail mailbox on this computer and see that it is connected. The dashboard MUST NOT add a login for the dashboard itself.
- **FR-002**: The parent MUST be able to disconnect Gmail. Disconnecting MUST leave already copied communications in place, MUST remove the mailbox permission from this computer, and MUST show that Gmail is not connected.
- **FR-003**: The mailbox permission MUST stay on this computer and MUST be removed when the parent disconnects. It MUST NOT appear in the fictional sample.
- **FR-004**: The dashboard MUST stay on this computer. It MUST NOT become reachable from another computer, and it MUST NOT send usage data.
- **FR-005**: A mail check MUST be read-only toward Gmail. It MUST NOT send, reply, delete, archive, label, or change the read or unread state of any message.
- **FR-006**: The parent MUST be able to add and remove school rules. A rule is a sender address, a school domain, or a Gmail label. With none saved, a check MUST copy nothing and MUST tell the parent to add one.
- **FR-007**: A check MUST copy a message only when it was received, not sent by the parent, it is in the inbox or archived, it is not in spam or trash, and it matches a saved sender address, a saved domain, or a saved label. The check MAY look through the mailbox far enough to tell what matches. It MUST NOT keep a non-matching message, including that message's sender, subject, or body. A message already copied MUST stay on the dashboard if it is later archived, marked as spam, or moved to trash in Gmail.
- **FR-008**: The dashboard MUST copy a received message that matches a school rule, is in the inbox or archived, and is not in spam or trash, when that message has never been copied, the parent has not deleted it, and either its date is after the previous successful check or its date is today or within the previous 30 days. When no check has succeeded yet, only the 30-day rule applies. Every other message MUST NOT be copied. A failed check MUST NOT move the previous successful check forward.
- **FR-009**: Each Gmail message MUST be stored as at most one communication. A later check MUST NOT create a second copy.
- **FR-010**: If the parent edits an imported communication, a later check MUST keep the edit. If the parent confirms deletion, a later check MUST NOT restore it. Neither action MUST change the Gmail message. Canceling a delete MUST leave the communication in place.
- **FR-011**: An imported communication MUST show the sender name and address, a title taken from the subject or "(no subject)" when the subject is blank, the sent date or the copy date when the sent date is missing, a readable body, the source label Gmail, a child scope of one child or both, and a way to open the original message in Gmail. If that original can no longer be opened, the communication MUST remain and the dashboard MUST say so.
- **FR-012**: Child scope MUST be that child when the subject or body contains exactly one household child's display name as a whole word or full phrase. It MUST be both when the message names both children, names neither, the two children share a display name, or the only candidate name is shorter than 3 characters. Selecting the other child MUST hide a one-child imported communication. Selecting either child or Both MUST show a shared one.
- **FR-013**: The body MUST be ordinary readable text. Formatting code MUST NOT be shown as the body. Past 5,000 characters, the dashboard MUST keep the first 5,000 and say the message was shortened. If the message has attachments, the communication MUST say so and MUST NOT save the files.
- **FR-014**: Imported communications MUST follow the existing child filter on every screen, and MUST be eligible for the eight newest communications on the home view. A check MUST NOT create events, assignments, or grades, and MUST NOT change hand-entered communications.
- **FR-015**: If the household has no children, a check MUST copy nothing and MUST tell the parent to add a child first.
- **FR-016**: If Gmail cannot be read, the dashboard MUST explain why in plain language, MUST save no new communications, and MUST leave existing communications unchanged.
- **FR-017**: A check MUST run only when the parent asks, and only while the dashboard is open.
- **FR-018**: Matching, child scope, and duplicate suppression MUST be verifiable with fictional messages, with no live mailbox and no real student names.
- **FR-019**: This feature MUST NOT connect to Canvas or TalkingPoints, and MUST NOT send notifications or produce an automated summary of a message.

### Key Entities

- **Mailbox connection**: Whether the parent currently allows this computer to read one Gmail mailbox. Removing it does not remove copied communications.
- **School mail rule**: A sender address, a school domain, or a Gmail label the parent chose. A received message in the inbox or in archived mail is eligible when it matches any saved rule. Spam and trash are not eligible.
- **Imported communication**: A communication created from one received Gmail message. The dashboard remembers which message it came from so the same message is not copied twice. It shows the sender, uses the source label Gmail, belongs to one child or to both, and includes a way to open the original in Gmail. Parent edits and confirmed deletions stick.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With Gmail allowed and one school rule saved, one check shows each matching school message from the last 30 days on the communications list. Non-matching messages from that same period are absent, and none of their sender, subject, or body text is kept.
- **SC-002**: A second check adds zero extra copies of messages already listed.
- **SC-003**: Switching from Both to one child, and back, hides the other child's imported mail and still shows shared imported mail on the next view.
- **SC-004**: After disconnect, every previously copied communication is still listed, and a check copies nothing until the parent connects again.
- **SC-005**: After a check, Gmail still contains the same messages, with the same read or unread state as before the check.
- **SC-006**: When Gmail cannot be read, the communications list is unchanged and the parent can read a plain explanation of the failure.
- **SC-007**: A reviewer can confirm matching, child scope, and no duplicates using only fictional messages, with no real student mail and no live mailbox.
- **SC-008**: From a copied message, the parent can open the original in Gmail in one action. Attached files are not stored on this computer.

## Assumptions

- This feature is the later mail connector allowed by the project constitution. It reads the parent's Gmail and does not write back. Canvas and TalkingPoints stay out of scope.
- The dashboard remains the local app for one parent on one computer. Connecting Gmail does not add a dashboard account, a public address, or usage reporting.
- One Gmail mailbox is enough. A second mailbox is out of scope.
- School mail means received messages in the inbox or in archived mail that match a sender, domain, or label the parent named. Spam and trash are skipped. A check may look through the mailbox far enough to find those messages, and it keeps nothing else. Thirty days is the first window so the dashboard does not copy years of mail.
- The parent starts each check. There is no checking while the dashboard is closed.
- Uncertain child scope is filed as both so the parent still sees the message under either child. The parent can correct it. Corrections are not written back to Gmail.
- Only the two children in this household are recognized. Classmates named in a message do not create profiles.
- Dates use the calendar on the computer where the dashboard runs, consistent with the existing dashboard.
- Attachments stay in Gmail. The copied communication notes that files were attached and includes a way to open the original message.
- This feature files communications only. The parent continues to record field trips, assignments, and grades by hand.
- A check needs a network connection to Gmail only while that check runs. Existing records remain readable when the network is down.
- Fictional messages are a stand-in for Gmail so a reviewer can test this feature without real children or a live mailbox.

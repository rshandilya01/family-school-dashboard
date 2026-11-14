# Feature Specification: Family School Dashboard

**Feature Branch**: `001-family-dashboard`

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "A local dashboard for one parent of twin daughters. Show communications, important dates, milestones, field trips, assignments, and grades for each child or both. Fill the first version by hand and with fictional sample data. Live Canvas, email, and TalkingPoints connectors are later specs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See what is coming up (Priority: P1)

The parent opens the app and sees the household's next two weeks: assignments that are due, field trips, milestones, and other important dates, soonest first. A short list of the latest communications sits under that. The parent can switch the whole view to one child or back to both.

**Why this priority**: The daily job is knowing what is due and what was just sent home. Without this view the other screens are a filing cabinet.

**Independent Test**: With fictional sample records loaded, open the home view, confirm a yesterday item is absent, confirm an in-window item is present and ordered by date, then switch from both children to one child and see the lists change.

**Acceptance Scenarios**:

1. **Given** sample records for two children, **When** the parent opens the home view on Both, **Then** upcoming items from either child and shared items dated today through the next 13 days appear, soonest first, and the eight newest communications appear newest first.
2. **Given** the home view is on Both, **When** the parent chooses one child, **Then** every list on the home view shows that child's items plus shared communications and shared events, and hides the other child's private items.
3. **Given** an assignment or event dated yesterday and another dated inside the window, **When** the parent views home, **Then** yesterday's item is absent and the in-window item is present.

---

### User Story 2 - Keep communications (Priority: P1)

The parent records a notice or message, corrects it, or removes it. Each communication belongs to one child or to both, has a date, a title, a body, a source label, and an optional link.

**Why this priority**: Teacher messages are the reason the dashboard exists, and the home view's recent list depends on them.

**Independent Test**: Add a communication for one child, see it on that child and on Both, confirm the other child does not see it, edit the title, then delete it after confirming.

**Acceptance Scenarios**:

1. **Given** two children, **When** the parent saves a communication for one child, **Then** it appears for that child and on Both, labeled with that child, and does not appear when the other child is selected.
2. **Given** a communication marked for both children, **When** the parent views either child or Both, **Then** the same communication appears, labeled as both.
3. **Given** a saved communication, **When** the parent edits it or confirms deletion, **Then** the list shows the edit or no longer shows the item.
4. **Given** a required field is blank, **When** the parent tries to save, **Then** the communication is not saved and the form shows what is missing.

---

### User Story 3 - Keep dates, milestones, and field trips (Priority: P2)

The parent records a field trip, a milestone, or another important date, then edits or deletes it. A field trip can include a destination and a note for a permission slip or items to bring.

**Why this priority**: Trips and dates are what the upcoming list is for, after the parent can already see and file messages.

**Independent Test**: Add a shared field trip inside the window, see it on home for both children, add a milestone for one child, and confirm the other child does not see that milestone.

**Acceptance Scenarios**:

1. **Given** a field trip saved for both children with a destination and a note, **When** the parent views events or the home upcoming list, **Then** the destination and note are visible.
2. **Given** a milestone saved for one child, **When** the other child is selected, **Then** that milestone is hidden.
3. **Given** an event dated yesterday, **When** the parent views home, **Then** it is absent from upcoming and still listed on the events screen.

---

### User Story 4 - Keep assignments (Priority: P2)

The parent records an assignment for one child, with a subject, a title, a due date, and a status of Not started or Done. New assignments start as Not started. The parent can edit or delete an assignment.

**Why this priority**: Due dates drive the upcoming list, and each assignment belongs to one child.

**Independent Test**: Add an assignment due inside the window for one child, see it on that child's home view and not the other child's, mark it Done, and confirm the status change.

**Acceptance Scenarios**:

1. **Given** an assignment due inside the window, **When** the parent views that child's home, **Then** the assignment appears in upcoming.
2. **Given** an assignment for one child, **When** the other child is selected, **Then** the assignment is hidden.
3. **Given** the parent marks an assignment Done, **When** the assignments list reloads, **Then** the status is Done.

---

### User Story 5 - Keep grades (Priority: P3)

The parent records a grade for one child: subject, the score or letter as typed, term, and the date it was recorded. The grades screen shows each saved grade and, for each subject, the latest grade in the current filter.

**Why this priority**: Grades matter, and they do not drive the daily upcoming list.

**Independent Test**: Add two grades for the same subject on different dates and confirm the latest one is identified as the current grade for that subject, while both remain in the list.

**Acceptance Scenarios**:

1. **Given** grades for one child, **When** the parent selects the other child, **Then** those grades are hidden.
2. **Given** two grades in the same subject, **When** the parent views grades, **Then** both are listed and the one with the later recorded date is the latest for that subject.
3. **Given** a grade, **When** the parent edits or confirms deletion, **Then** the list matches the change.

---

### User Story 6 - Name the children and load sample data (Priority: P3)

The parent names the two children. Until two children exist, the parent can add a child. A sample-data action fills a household that has no children yet with two fictional students and a small set of fake records. Sample data is never loaded by itself when the app opens, and it refuses to run once any child exists.

**Why this priority**: Real names should be easy to set, and a reviewer needs fictional data without typing every screen first.

**Independent Test**: On an empty household, run the sample-data action once, confirm two fictional children and the sample records exist, run it again and confirm it does not add a second copy, then rename one child and see the new name on every list.

**Acceptance Scenarios**:

1. **Given** no children, **When** the parent adds a child with a non-blank name, **Then** that child appears in the switcher.
2. **Given** two children already exist, **When** the parent tries to add a third, **Then** the third is not created.
3. **Given** a child, **When** the parent renames them to a non-blank name, **Then** lists show the new name.
4. **Given** no children, **When** the parent loads sample data, **Then** two fictional children exist, plus one shared field trip inside the window, one assignment due inside the window, one grade, one teacher message, and one item dated yesterday.
5. **Given** sample data is already loaded, **When** the parent loads sample data again, **Then** no duplicate children or records are added.

### Edge Cases

- A household with no records shows an empty upcoming list and an empty communications list, with a way to add a child or load sample data.
- A blank child name, title, subject, or required date is rejected and nothing is saved.
- Two children may share the same display name.
- Deleting an item requires confirmation. Canceling leaves the item in place.
- An item dated on the 14th day after today is outside the window. An item dated today, or on any of the next 13 days, is inside it.
- A grade is the text the parent typed. The app does not average scores or convert letters.
- Closing the app and opening it again shows the same children and records.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide one parent on one computer with no login.
- **FR-002**: The system MUST support at most two child profiles. The parent MUST be able to add a child until two exist, and MUST be able to rename a child. A blank name MUST be rejected.
- **FR-003**: Every screen MUST let the parent choose one child or Both. Both shows each child's items labeled with that child, plus shared items labeled as both.
- **FR-004**: Communications and events MUST belong to one child or to both children. Assignments and grades MUST belong to exactly one child.
- **FR-005**: The home view MUST list upcoming assignments and events whose date is today or within the next 13 days, soonest first, and MUST hide earlier and later items. It MUST also list the eight newest communications, newest first, regardless of that window.
- **FR-006**: Selecting one child MUST include that child's items and shared communications and events, and MUST exclude the other child's private items, on every screen.
- **FR-007**: The parent MUST be able to add, edit, and delete communications, events, assignments, and grades. Delete MUST require confirmation.
- **FR-008**: A communication MUST have a child scope (one child or both), a date, a title, a body, and a source label. A link is optional. The source label MUST default to Manual.
- **FR-009**: An event MUST have a kind of field trip, milestone, or other date, a child scope, a title, and a date. Destination and a note (permission slip or items to bring) are optional and MUST be shown when present.
- **FR-010**: An assignment MUST have one child, a subject, a title, a due date, and a status of Not started or Done. A new assignment MUST start as Not started.
- **FR-011**: A grade MUST have one child, a subject, the score or letter as entered, a term, and a recorded date. The grades view MUST show every grade in the current filter and MUST identify the latest grade per subject by recorded date.
- **FR-012**: Saving with a missing required field MUST leave stored data unchanged and MUST tell the parent what is missing.
- **FR-013**: Children and records MUST still be present after the app is closed and opened again.
- **FR-014**: A sample-data action MUST load fictional children and the records in User Story 6 only when the household has no children, and MUST NOT run automatically on startup.
- **FR-015**: This feature MUST NOT connect to Canvas, email, or TalkingPoints, and MUST NOT send notifications or summaries.
- **FR-016**: Child filtering and the upcoming-date window MUST be verifiable by an automated check that does not require a person to click through the app.

### Key Entities

- **Child**: A named profile. At most two. Every private item points at one child.
- **Communication**: A notice or message. Scope is one child or both. Has a date, title, body, source label, and optional link.
- **Event**: A field trip, milestone, or other date. Scope is one child or both. Has a title, date, optional destination, and optional note.
- **Assignment**: Work due for exactly one child. Has a subject, title, due date, and status.
- **Grade**: A recorded result for exactly one child. Has a subject, entered score or letter, term, and recorded date.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The parent can switch from Both to one child, and back, and every visible list matches that choice on the next view.
- **SC-002**: The parent can add a communication, a field trip, an assignment, and a grade without leaving the app, and all four are still present after the app is closed and opened again.
- **SC-003**: An item dated yesterday is absent from the upcoming list, an item dated inside the window is present, and upcoming items are ordered with the soonest date first.
- **SC-004**: On an empty household, one sample-data action produces two fictional children and the sample records, and a second action does not duplicate them.
- **SC-005**: A reviewer can complete the home-view check in User Story 1 using only fictional sample data, with no real student names required.

## Assumptions

- "Both" means the two children in this household, not a general multi-student directory.
- The upcoming window is 14 dates: today and the next 13 days. The date 14 days after today is outside the window.
- Recent communications on the home view are the eight newest, not limited to the upcoming window.
- Dates are calendar dates on the computer where the app runs.
- The parent is the only user. There is no second account and no sharing link.
- Sample students are fictional. Real names are typed by the parent later.
- Live school-system connectors, accounts, notifications, and AI summaries are later features. The source label exists so those features can mark where a record came from.
- A grade stores the parent's text (for example "A-" or "92") and is not computed.
- Deleting a child is out of scope. Records stay attached to the child they were saved with.

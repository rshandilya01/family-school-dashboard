# Data Model: Family School Dashboard

Dates are ISO calendar dates (`YYYY-MM-DD`). Timestamps are ISO datetimes used only for bookkeeping.

## Child

| Field | Required | Rules |
|-------|----------|--------|
| id | yes | Integer identity |
| name | yes | Trimmed, non-blank, at most 80 characters |
| created_at | yes | Set when the row is inserted |

At most two rows. Adding a third is rejected. Names may duplicate. Children are not deleted in this feature.

## Communication

| Field | Required | Rules |
|-------|----------|--------|
| id | yes | Integer identity |
| child_id | no | Null means both children. Otherwise a real child id |
| title | yes | Trimmed, non-blank, at most 200 characters |
| body | yes | Trimmed, non-blank |
| source | yes | Defaults to `Manual`. Shown as the source label |
| link | no | If present, a non-blank URL string the parent typed |
| occurred_on | yes | Calendar date |
| created_at | yes | Set when the row is inserted |

## Event

| Field | Required | Rules |
|-------|----------|--------|
| id | yes | Integer identity |
| child_id | no | Null means both children |
| kind | yes | `field_trip`, `milestone`, or `other` |
| title | yes | Trimmed, non-blank, at most 200 characters |
| destination | no | Shown when present. Expected for field trips, optional for every kind |
| notes | no | Permission slip or items to bring, shown when present |
| event_on | yes | Calendar date. Home uses this for the upcoming window |
| created_at | yes | Set when the row is inserted |

## Assignment

| Field | Required | Rules |
|-------|----------|--------|
| id | yes | Integer identity |
| child_id | yes | Exactly one child |
| subject | yes | Trimmed, non-blank, at most 80 characters |
| title | yes | Trimmed, non-blank, at most 200 characters |
| due_on | yes | Calendar date. Home uses this for the upcoming window |
| status | yes | `not_started` or `done`. New rows start as `not_started` |
| created_at | yes | Set when the row is inserted |

Status transition: the parent may set either value on create or edit. No other states.

## Grade

| Field | Required | Rules |
|-------|----------|--------|
| id | yes | Integer identity |
| child_id | yes | Exactly one child |
| subject | yes | Trimmed, non-blank, at most 80 characters |
| score_text | yes | The score or letter as typed. Not parsed |
| term | yes | Trimmed, non-blank, at most 40 characters |
| recorded_on | yes | Calendar date. Latest grade for a child and subject is the greatest date, then greatest id |
| created_at | yes | Set when the row is inserted |

## Filter rules

- `child=all`: every row.
- `child={id}`: rows with that child id, plus communications and events whose child id is null.
- Unknown child id: treat as an empty selection and show no private rows. Shared rows still appear, and the page says the child was not found.

## Relationships

- A child has many communications, events, assignments, and grades.
- Shared communications and events have no child.
- Deleting a child is not supported, so child ids on existing rows stay valid.

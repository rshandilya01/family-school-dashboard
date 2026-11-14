# UI Contract: Family School Dashboard

The app is server-rendered HTML. Writes use POST forms and redirect back to the list on success (POST, redirect, GET). A failed validation re-displays the form and does not change stored rows.

The child filter is the `child` query parameter: `all` (default) or a child id. List and home links keep the current filter.

## Pages

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Home. Upcoming assignments and events, then eight newest communications |
| GET | `/communications` | Communication list |
| GET | `/communications/new` | Blank communication form |
| POST | `/communications` | Create |
| GET | `/communications/{id}/edit` | Edit form |
| POST | `/communications/{id}` | Update |
| GET | `/communications/{id}/delete` | Confirm delete |
| POST | `/communications/{id}/delete` | Delete |
| GET | `/events` | Event list |
| GET | `/events/new` | Blank event form |
| POST | `/events` | Create |
| GET | `/events/{id}/edit` | Edit form |
| POST | `/events/{id}` | Update |
| GET | `/events/{id}/delete` | Confirm delete |
| POST | `/events/{id}/delete` | Delete |
| GET | `/assignments` | Assignment list |
| GET | `/assignments/new` | Blank assignment form |
| POST | `/assignments` | Create |
| GET | `/assignments/{id}/edit` | Edit form |
| POST | `/assignments/{id}` | Update |
| GET | `/assignments/{id}/delete` | Confirm delete |
| POST | `/assignments/{id}/delete` | Delete |
| GET | `/grades` | Grade list, latest per child and subject marked |
| GET | `/grades/new` | Blank grade form |
| POST | `/grades` | Create |
| GET | `/grades/{id}/edit` | Edit form |
| POST | `/grades/{id}` | Update |
| GET | `/grades/{id}/delete` | Confirm delete |
| POST | `/grades/{id}/delete` | Delete |
| GET | `/children` | Names, add form when fewer than two, sample-data form |
| POST | `/children` | Add a child |
| POST | `/children/{id}` | Rename a child |
| POST | `/sample-data` | Load fictional sample data when no children exist |

## Form fields

- Communication: `child_id` (`both` or a child id), `occurred_on`, `title`, `body`, `source`, `link`
- Event: `child_id` (`both` or a child id), `kind` (`field_trip`, `milestone`, `other`), `event_on`, `title`, `destination`, `notes`
- Assignment: `child_id` (required child id), `subject`, `title`, `due_on`, `status` (`not_started` or `done`)
- Grade: `child_id`, `subject`, `score_text`, `term`, `recorded_on`
- Child: `name`

## Visible labels

- Kinds: Field trip, Milestone, Other date
- Status: Not started, Done
- Shared scope: Both
- Default source: Manual
- Latest grade: the word Current next to the latest row for that child and subject

## Errors

Missing required fields return the form with a message naming the field. The stored row is unchanged. Adding a third child returns the children page with a message and does not insert. Sample data on a non-empty household returns the children page with a message and does not insert.

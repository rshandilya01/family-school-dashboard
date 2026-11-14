import re
from datetime import date, timedelta


def _child_id(client, name):
    client.post("/children", data={"name": name})
    html = client.get("/children").text
    match = re.search(rf'data-child-name="{name}" data-child-id="(\d+)"', html)
    assert match, html
    return match.group(1)


def test_upcoming_window_hides_yesterday_and_orders_soonest_first(client):
    child_id = _child_id(client, "Lila")
    today = date.today()

    def event(title, day):
        response = client.post(
            "/events",
            data={
                "child_id": child_id,
                "kind": "other",
                "event_on": day.isoformat(),
                "title": title,
                "destination": "",
                "notes": "",
            },
        )
        assert response.status_code == 200

    event("Yesterday Event", today - timedelta(days=1))
    event("Today Event", today)
    event("Edge Event", today + timedelta(days=13))
    event("Later Event", today + timedelta(days=14))
    assignment = client.post(
        "/assignments",
        data={
            "child_id": child_id,
            "subject": "Math",
            "title": "Due Soon",
            "due_on": (today + timedelta(days=1)).isoformat(),
            "status": "not_started",
        },
    )
    assert assignment.status_code == 200

    home = client.get("/").text
    assert "Yesterday Event" not in home
    assert "Later Event" not in home
    assert home.index("Today Event") < home.index("Due Soon") < home.index("Edge Event")

    events = client.get("/events").text
    assert "Yesterday Event" in events

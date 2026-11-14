import re
from datetime import date, timedelta


def _ids(client):
    client.post("/children", data={"name": "Lila"})
    client.post("/children", data={"name": "Nora"})
    html = client.get("/children").text
    found = dict(re.findall(r'data-child-name="([^"]+)" data-child-id="(\d+)"', html))
    return found["Lila"], found["Nora"]


def test_child_filter_hides_the_other_child_and_keeps_shared_items(client):
    lila, nora = _ids(client)
    today = date.today().isoformat()
    soon = (date.today() + timedelta(days=2)).isoformat()

    assert client.post(
        "/communications",
        data={
            "child_id": lila,
            "occurred_on": today,
            "title": "Lila bottle",
            "body": "Send a water bottle.",
            "source": "Manual",
            "link": "",
        },
    ).status_code == 200
    assert client.post(
        "/communications",
        data={
            "child_id": nora,
            "occurred_on": today,
            "title": "Nora slip",
            "body": "Sign the slip.",
            "source": "Manual",
            "link": "",
        },
    ).status_code == 200
    assert client.post(
        "/communications",
        data={
            "child_id": "both",
            "occurred_on": today,
            "title": "Both notice",
            "body": "Early dismissal Friday.",
            "source": "Manual",
            "link": "",
        },
    ).status_code == 200
    assert client.post(
        "/events",
        data={
            "child_id": "both",
            "kind": "field_trip",
            "event_on": soon,
            "title": "Museum trip",
            "destination": "Science museum",
            "notes": "Permission slip",
        },
    ).status_code == 200
    assert client.post(
        "/events",
        data={
            "child_id": lila,
            "kind": "milestone",
            "event_on": soon,
            "title": "Lila concert",
            "destination": "",
            "notes": "",
        },
    ).status_code == 200
    assert client.post(
        "/assignments",
        data={
            "child_id": lila,
            "subject": "Math",
            "title": "Lila worksheet",
            "due_on": soon,
            "status": "not_started",
        },
    ).status_code == 200
    assert client.post(
        "/grades",
        data={
            "child_id": nora,
            "subject": "Reading",
            "score_text": "A-",
            "term": "Fall",
            "recorded_on": today,
        },
    ).status_code == 200

    lila_home = client.get(f"/?child={lila}").text
    assert "Lila bottle" in lila_home
    assert "Both notice" in lila_home
    assert "Museum trip" in lila_home
    assert "Science museum" in lila_home
    assert "Lila worksheet" in lila_home
    assert "Nora slip" not in lila_home
    assert "A-" not in lila_home

    nora_comms = client.get(f"/communications?child={nora}").text
    assert "Nora slip" in nora_comms
    assert "Both notice" in nora_comms
    assert "Lila bottle" not in nora_comms

    nora_events = client.get(f"/events?child={nora}").text
    assert "Museum trip" in nora_events
    assert "Permission slip" in nora_events
    assert "Lila concert" not in nora_events

    blank = client.post(
        "/communications",
        data={
            "child_id": lila,
            "occurred_on": today,
            "title": "   ",
            "body": "Missing title",
            "source": "Manual",
            "link": "",
        },
    )
    assert blank.status_code == 400
    assert "Title is required." in blank.text
    assert "Missing title" not in client.get("/communications").text


def test_assignment_status_and_grade_latest_respect_child(client):
    lila, nora = _ids(client)
    today = date.today()
    earlier = (today - timedelta(days=10)).isoformat()
    later = today.isoformat()

    client.post(
        "/grades",
        data={
            "child_id": lila,
            "subject": "Math",
            "score_text": "80",
            "term": "Fall",
            "recorded_on": earlier,
        },
    )
    client.post(
        "/grades",
        data={
            "child_id": lila,
            "subject": "Math",
            "score_text": "95",
            "term": "Fall",
            "recorded_on": later,
        },
    )
    client.post(
        "/grades",
        data={
            "child_id": nora,
            "subject": "Math",
            "score_text": "70",
            "term": "Fall",
            "recorded_on": later,
        },
    )
    client.post(
        "/assignments",
        data={
            "child_id": lila,
            "subject": "Math",
            "title": "Status check",
            "due_on": later,
            "status": "done",
        },
    )

    lila_grades = client.get(f"/grades?child={lila}").text
    assert "95" in lila_grades
    assert "80" in lila_grades
    assert "70" not in lila_grades
    assert lila_grades.count("Current") == 1

    nora_grades = client.get(f"/grades?child={nora}").text
    assert "70" in nora_grades
    assert "95" not in nora_grades

    assignments = client.get(f"/assignments?child={lila}").text
    assert "Done" in assignments
    assert "Status check" in assignments

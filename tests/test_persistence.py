from datetime import date, timedelta

from fastapi.testclient import TestClient

from app.main import create_app


def test_records_remain_after_a_new_process_opens_the_same_file(db_path):
    today = date.today().isoformat()
    soon = (date.today() + timedelta(days=4)).isoformat()

    with TestClient(create_app(db_path)) as first:
        first.post("/children", data={"name": "Lila"})
        first.post("/children", data={"name": "Nora"})
        children = first.get("/children").text
        lila = children.split('data-child-name="Lila" data-child-id="', 1)[1].split('"', 1)[0]
        first.post(
            "/communications",
            data={
                "child_id": lila,
                "occurred_on": today,
                "title": "Saved note",
                "body": "Still here after restart.",
                "source": "Manual",
                "link": "",
            },
        )
        first.post(
            "/events",
            data={
                "child_id": "both",
                "kind": "field_trip",
                "event_on": soon,
                "title": "Saved trip",
                "destination": "Zoo",
                "notes": "Bring lunch",
            },
        )
        first.post(
            "/assignments",
            data={
                "child_id": lila,
                "subject": "Science",
                "title": "Saved assignment",
                "due_on": soon,
                "status": "not_started",
            },
        )
        first.post(
            "/grades",
            data={
                "child_id": lila,
                "subject": "Science",
                "score_text": "88",
                "term": "Fall",
                "recorded_on": today,
            },
        )

    with TestClient(create_app(db_path)) as second:
        home = second.get("/").text
        assert "Saved note" in home
        assert "Saved trip" in home
        assert "Saved assignment" in home
        assert "88" in second.get("/grades").text

def test_two_child_cap_rename_and_sample_data_once(client):
    assert "Name is required." in client.post("/children", data={"name": "  "}).text
    client.post("/children", data={"name": "Lila"})
    client.post("/children", data={"name": "Nora"})
    third = client.post("/children", data={"name": "Extra"})
    assert "This household already has two children." in third.text
    assert "Extra" not in client.get("/children").text

    html = client.get("/children").text
    assert 'data-child-name="Lila"' in html
    child_id = html.split('data-child-name="Lila" data-child-id="', 1)[1].split('"', 1)[0]
    renamed = client.post(f"/children/{child_id}", data={"name": "Lila Jane"})
    assert "Lila Jane" in renamed.text
    assert "Lila Jane" in client.get("/").text

    skipped = client.post("/sample-data")
    assert "Sample data was not loaded because children already exist." in skipped.text


def test_sample_data_loads_once_on_an_empty_household(client):
    loaded = client.post("/sample-data")
    assert loaded.status_code == 200
    assert "Lila" in loaded.text
    assert "Nora" in loaded.text
    home = client.get("/").text
    assert "Science museum trip" in home
    assert "Worksheet 4" in home
    assert "Picture day" not in home
    assert "Please send a water bottle." in client.get("/communications").text
    grades = client.get("/grades").text
    assert "A-" in grades

    again = client.post("/sample-data")
    assert "Sample data was not loaded because children already exist." in again.text
    assert again.text.count('data-child-name="Lila"') == 1

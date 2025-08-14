# tests/test_availability.py

def test_availability_crud(client):
    # Create employee
    emp = {
        "first_name": "Cal",
        "last_name": "Slots",
        "gender": True,
        "birth_date": "1990-05-05"
    }
    emp_id = client.post("/employees/", json=emp).json()["id"]

    # GET availability (empty)
    r = client.get(f"/employees/{emp_id}/availability/")
    assert r.status_code == 200
    assert r.json() == []

    # POST availability (create two slots)
    slots = [
        {"day_of_week": 1, "time_from": "09:00:00", "time_to": "12:00:00", "location_id": 3},
        {"day_of_week": 3, "time_from": "13:00:00", "time_to": "17:00:00", "location_id": 3},
    ]
    r = client.post(f"/employees/{emp_id}/availability/", json=slots)
    assert r.status_code == 200
    created = r.json()
    assert len(created) == 2
    slot_ids = [s["id"] for s in created]

    # GET availability (should have two)
    r = client.get(f"/employees/{emp_id}/availability/")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2

    # DELETE one slot
    r = client.delete(f"/employees/{emp_id}/availability/{slot_ids[0]}")
    assert r.status_code == 204

    # GET availability (now one left)
    r = client.get(f"/employees/{emp_id}/availability/")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    assert body[0]["id"] == slot_ids[1]

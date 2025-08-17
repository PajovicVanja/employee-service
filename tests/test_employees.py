# tests/test_employees.py
import pytest

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_create_read_update_delete_employee(client):
    # CREATE
    payload = {
        "first_name": "John",
        "last_name": "Doe",
        "gender": True,
        "birth_date": "1990-01-01"
    }
    r = client.post("/employees/", json=payload)
    assert r.status_code == 201
    emp = r.json()
    assert emp["first_name"] == "John"
    emp_id = emp["id"]

    # READ list
    r = client.get("/employees/")
    assert r.status_code == 200
    assert any(e["id"] == emp_id for e in r.json())

    # READ detail
    r = client.get(f"/employees/{emp_id}")
    assert r.status_code == 200 and r.json()["id"] == emp_id

    # UPDATE
    upd = {
        "first_name": "Jane",
        "last_name": "Doe",
        "gender": False,
        "birth_date": "1992-02-02",
        "idp_id": None,
        "id_picture": None,
        "active": True
    }
    r = client.put(f"/employees/{emp_id}", json=upd)
    assert r.status_code == 200
    assert r.json()["first_name"] == "Jane"

    # DELETE (soft)
    r = client.delete(f"/employees/{emp_id}")
    assert r.status_code == 204

    # ensure it no longer appears in GET /employees
    r = client.get("/employees/")
    assert r.status_code == 200
    assert all(e["id"] != emp_id for e in r.json())

# stub out the inter-service call
@pytest.fixture(autouse=True)
def fake_reservation(monkeypatch):
    async def fake_get(self, employee_id):
        return [{"id": 1, "employee_id": employee_id, "date": "2025-01-01", "time_from": "09:00:00", "time_to": "10:00:00"}]
    from app.services.reservation_client import ReservationServiceClient
    monkeypatch.setattr(ReservationServiceClient, "get_reservations_for_employee", fake_get)

def test_get_reservations(client):
    # create an employee
    payload = {
        "first_name": "Tom",
        "last_name": "Thumb",
        "gender": True,
        "birth_date": "1991-01-01"
    }
    emp_id = client.post("/employees/", json=payload).json()["id"]

    r = client.get(f"/employees/{emp_id}/reservations")
    assert r.status_code == 200
    data = r.json()
    assert data and data[0]["employee_id"] == emp_id

# tests/test_skills.py

def test_skills_replace_and_get(client):
    # Create employee
    emp = {
        "first_name": "Sam",
        "last_name": "Skills",
        "gender": True,
        "birth_date": "1994-04-04"
    }
    emp_id = client.post("/employees/", json=emp).json()["id"]

    # GET skills (empty)
    r = client.get(f"/employees/{emp_id}/skills/")
    assert r.status_code == 200
    assert r.json() == []

    # PUT replace skills
    r = client.put(f"/employees/{emp_id}/skills/", json=[1, 3, 5])
    assert r.status_code == 200
    skills = sorted([s["service_id"] for s in r.json()])
    assert skills == [1, 3, 5]

    # GET confirm
    r = client.get(f"/employees/{emp_id}/skills/")
    assert r.status_code == 200
    skills = sorted([s["service_id"] for s in r.json()])
    assert skills == [1, 3, 5]

    # Replace again
    r = client.put(f"/employees/{emp_id}/skills/", json=[2])
    assert r.status_code == 200
    skills = [s["service_id"] for s in r.json()]
    assert skills == [2]

# tests/test_graphql.py

def test_graphql_employees_query(client):
    # create one employee via REST
    token = client.post("/token", data={"username":"alice","password":"secret1"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        "/employees/",
        json={
            "first_name": "GQL",
            "last_name": "Tester",
            "gender": True,
            "birth_date": "1990-01-01"
        },
        headers=headers
    )

    query = {
        "query": """
            {
                employees {
                    id
                    firstName
                    lastName
                }
            }
        """
    }
    r = client.post("/graphql", json=query)
    assert r.status_code == 200
    data = r.json()
    assert "data" in data and "employees" in data["data"]
    # confirm at least one returned employee has firstName == "GQL"
    assert any(e["firstName"] == "GQL" for e in data["data"]["employees"])

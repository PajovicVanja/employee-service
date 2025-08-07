# tests/test_auth.py
def test_token_success(client):
    r = client.post("/token", data={"username": "alice", "password": "secret1"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and body["token_type"] == "bearer"

def test_token_failure(client):
    r = client.post("/token", data={"username": "alice", "password": "wrong"})
    assert r.status_code == 401

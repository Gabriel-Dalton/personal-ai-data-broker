import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_header(client):
    from app.auth import hash_password
    from app.models import User

    db = TestSession()
    user = User(username="testuser", hashed_password=hash_password("testpass"))
    db.add(user)
    db.commit()
    db.close()

    resp = client.post("/auth/login", json={"username": "testuser", "password": "testpass"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_login_success(client):
    from app.auth import hash_password
    from app.models import User

    db = TestSession()
    user = User(username="loginuser", hashed_password=hash_password("pass123"))
    db.add(user)
    db.commit()
    db.close()

    resp = client.post("/auth/login", json={"username": "loginuser", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_failure(client):
    resp = client.post("/auth/login", json={"username": "nobody", "password": "wrong"})
    assert resp.status_code == 401


def test_data_crud(client, auth_header):
    resp = client.post("/api/data", json={
        "category": "contacts",
        "label": "Work email",
        "content": "test@example.com",
        "is_sensitive": False,
    }, headers=auth_header)
    assert resp.status_code == 201
    entry_id = resp.json()["id"]

    resp = client.get("/api/data", headers=auth_header)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.patch(f"/api/data/{entry_id}", json={"label": "Personal email"}, headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["label"] == "Personal email"

    resp = client.delete(f"/api/data/{entry_id}", headers=auth_header)
    assert resp.status_code == 204


def test_policy_crud(client, auth_header):
    resp = client.post("/api/policies", json={
        "name": "Test Policy",
        "allowed_categories": "contacts",
        "allow_sensitive": False,
    }, headers=auth_header)
    assert resp.status_code == 201
    policy_id = resp.json()["id"]

    resp = client.get("/api/policies", headers=auth_header)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    resp = client.delete(f"/api/policies/{policy_id}", headers=auth_header)
    assert resp.status_code == 204


def test_api_key_lifecycle(client, auth_header):
    resp = client.post("/api/policies", json={
        "name": "Key Test Policy",
        "allowed_categories": "*",
    }, headers=auth_header)
    policy_id = resp.json()["id"]

    resp = client.post("/api/keys", json={
        "policy_id": policy_id,
        "label": "Test Key",
    }, headers=auth_header)
    assert resp.status_code == 201
    key_data = resp.json()
    assert key_data["key"].startswith("pdb_")
    key_id = key_data["id"]

    resp = client.get("/api/keys", headers=auth_header)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    resp = client.post(f"/api/keys/{key_id}/toggle", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_broker_query(client, auth_header):
    client.post("/api/data", json={
        "category": "contacts",
        "label": "Email",
        "content": "hello@world.com",
    }, headers=auth_header)
    client.post("/api/data", json={
        "category": "health",
        "label": "Allergy",
        "content": "Peanuts",
        "is_sensitive": True,
    }, headers=auth_header)

    resp = client.post("/api/policies", json={
        "name": "Contacts Only",
        "allowed_categories": "contacts",
        "allow_sensitive": False,
    }, headers=auth_header)
    policy_id = resp.json()["id"]

    resp = client.post("/api/keys", json={
        "policy_id": policy_id,
        "label": "Broker Test Key",
    }, headers=auth_header)
    api_key = resp.json()["key"]

    resp = client.post("/broker/query", json={
        "categories": ["contacts"],
    }, headers={"Authorization": f"Bearer {api_key}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["allowed"] is True
    assert data["filtered_count"] == 1
    assert data["data"][0]["content"] == "hello@world.com"

    resp = client.post("/broker/query", json={
        "categories": ["health"],
    }, headers={"Authorization": f"Bearer {api_key}"})
    assert resp.status_code == 403


def test_broker_no_key(client):
    resp = client.post("/broker/query", json={})
    assert resp.status_code == 401


def test_audit_log(client, auth_header):
    resp = client.get("/api/audit", headers=auth_header)
    assert resp.status_code == 200


def test_landing_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Personal AI" in resp.text


def test_dashboard_page(client):
    resp = client.get("/dashboard")
    assert resp.status_code == 200

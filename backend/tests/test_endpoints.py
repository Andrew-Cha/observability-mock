import pytest
import sqlite3

from fastapi.testclient import TestClient

from backend.api.database import create_database_tables, get_db_cursor
from backend.api.main import app

client = TestClient(app)


@pytest.fixture
def db_cursor():
    # As FastAPI creates a unique thread for each call.
    connection = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = connection.cursor()
    create_database_tables(cursor)

    def override_get_db_cursor():
        try:
            yield cursor
        finally:
            pass

    app.dependency_overrides[get_db_cursor] = override_get_db_cursor

    yield cursor

    cursor.close()
    connection.close()

    app.dependency_overrides.pop(get_db_cursor, None)


def test_get_cats_empty(db_cursor):
    response = client.get("/cats/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_cat(db_cursor):
    response = client.post(
        "/cats/", json={"name": "Whiskers", "breed": "Tabby", "age": 2}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Whiskers"


def test_get_cats_after_creation(db_cursor):
    client.post("/cats/", json={"name": "Whiskers", "breed": "Tabby", "age": 2})
    response = client.get("/cats/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Whiskers"


def test_update_cat(db_cursor):
    response = client.post(
        "/cats/", json={"name": "Whiskers", "breed": "Tabby", "age": 2}
    )
    cat_id = response.json()["id"]

    response = client.patch(f"/cats/{cat_id}/", json={"name": "Fluffy"})
    assert response.status_code == 200
    assert response.json()["name"] == "Fluffy"


def test_get_owners_empty(db_cursor):
    response = client.get("/owners/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_owner_with_existing_cat(db_cursor):
    response = client.post(
        "/cats/", json={"name": "Whiskers", "breed": "Tabby", "age": 2}
    )
    cat_id = response.json()["id"]

    response = client.post(
        "/owners/",
        json={"name": "John Doe", "address": "123 Cat Street", "cat_id": cat_id},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "John Doe"


def test_create_owner_with_nonexistent_cat(db_cursor):
    response = client.post(
        "/owners/",
        json={"name": "John Doe", "address": "123 Cat Street", "cat_id": 999},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Cat with id 999 does not exist"


def test_update_owner(db_cursor):
    response = client.post(
        "/cats/", json={"name": "Whiskers", "breed": "Tabby", "age": 2}
    )
    cat_id = response.json()["id"]

    response = client.post(
        "/owners/",
        json={"name": "John Doe", "address": "123 Cat Street", "cat_id": cat_id},
    )
    owner_id = response.json()["id"]

    response = client.patch(f"/owners/{owner_id}/", json={"name": "Jane Doe"})
    assert response.status_code == 200
    assert response.json()["name"] == "Jane Doe"

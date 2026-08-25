import pytest

from app import app, db


@pytest.fixture()
def client(tmp_path):
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'test.db'}",
        SECRET_KEY="test-secret",
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.drop_all()


def csrf(client):
    response = client.get("/employees")
    assert response.status_code == 200
    with client.session_transaction() as session:
        return session["_csrf_token"]


def test_post_requires_csrf(client):
    response = client.post(
        "/add",
        data={
            "name": "A",
            "email": "a@example.com",
            "department": "IT",
            "job_title": "Engineer",
        },
    )
    assert response.status_code == 400


def test_add_employee_with_valid_csrf(client):
    token = csrf(client)
    response = client.post(
        "/add",
        data={
            "_csrf_token": token,
            "name": "A",
            "email": "a@example.com",
            "department": "IT",
            "job_title": "Engineer",
        },
    )
    assert response.status_code == 302

import pytest

from app import db as _db
from app.routes import create_app
from tests.utils import (
    create_client,
    create_opened_parking,
)


@pytest.fixture
def app():
    _app = create_app()
    _app.config["TESTING"] = True
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"

    with _app.app_context():
        _db.create_all()

        yield _app
        _db.session.close()
        _db.drop_all()


@pytest.fixture
def client(app):
    client = app.test_client()
    yield client


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db


@pytest.fixture
def user(db):
    return create_client(db)


@pytest.fixture
def open_parking(db):
    return create_opened_parking(db)

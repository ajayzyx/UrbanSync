import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings


@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(settings.test_database_url)
    from app import db

    db.init_db(engine, drop=True)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def session_factory(test_engine):
    return sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest.fixture(scope="module")
def db_session(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture(scope="module")
def client(session_factory):
    from app.db import get_session
    from app.main import app

    def override():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_session] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def demo_dir(tmp_path_factory):
    from app.synthetic import generate_ward

    d = tmp_path_factory.mktemp("demo")
    generate_ward(d)
    return d


@pytest.fixture(scope="module")
def seeded(db_session, demo_dir):
    from app.seed import seed_demo

    return seed_demo(db_session, data_dir=demo_dir)

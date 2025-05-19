import pytest
from app.services.memory_service import fetch_recent_messages

# Placeholder for db_session fixture. You should implement this to provide a test DB session.
@pytest.fixture
def db_session():
    # TODO: Implement a real test DB session or mock
    pass

def test_fetch_recent_messages_empty(db_session):
    messages = fetch_recent_messages("nonexistent_convo", db_session)
    assert messages == [] 
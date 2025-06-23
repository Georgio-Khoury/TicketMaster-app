import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_get_db():
    return MagicMock()

@pytest.fixture
def mock_user():
    return 1

@patch("app.Router.event_router.get_events_service")
def test_get_event_names(mock_get_events_service):
    mock_get_events_service.return_value = [{
        "id": "1",
        "name": "Event 1", 
        "description": None,
        "start_date": None,
        "venue_name": None,
        "city": None,
        "country": None,
        "url": None,
        "created_at": None
    }]
    
    response = client.get("/events/")
    assert response.status_code == 200
    assert response.json() == [{
        "id": "1",
        "name": "Event 1",
        "description": None,
        "start_date": None,
        "venue_name": None,
        "city": None,
        "country": None,
        "url": None,
        "created_at": None
    }]

@patch("app.Router.event_router.save_event_service")
def test_save_event(mock_save_event_service):
    from app.core.auth import get_current_user
    from app.core.database import get_db
    
    # Mock the dependencies
    def mock_get_current_user():
        return 1
    
    def mock_get_db():
        return MagicMock()
    
    # Override dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db] = mock_get_db
    
    # Return a response that matches FavoriteSchema
    mock_save_event_service.return_value = {
        "id": 1,
        "user_id": 1,
        "event_id": "123",
        "created_at": "2023-01-01T00:00:00"
    }
    
    try:
        response = client.post("/events/123/save")
        assert response.status_code == 200
        assert response.json() == {
            "id": 1,
            "user_id": 1,
            "event_id": "123",
            "created_at": "2023-01-01T00:00:00"
        }
    finally:
        # Clean up dependency overrides
        app.dependency_overrides.clear()

@patch("app.Router.event_router.get_favorites_service") 
def test_get_favorite_events(mock_get_favorites_service):
    from app.core.auth import get_current_user
    from app.core.database import get_db
    
    # Mock the dependencies
    def mock_get_current_user():
        return 1
    
    def mock_get_db():
        return MagicMock()
    
    # Override dependencies
    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[get_db] = mock_get_db
    
    # Return a response that matches List[FavoriteSchema]
    mock_get_favorites_service.return_value = [{
        "id": 1,
        "user_id": 1,
        "event_id": "123",
        "created_at": "2023-01-01T00:00:00"
    }]
    
    try:
        response = client.get("/events/favorites")
        assert response.status_code == 200
        assert response.json() == [{
            "id": 1,
            "user_id": 1,
            "event_id": "123",
            "created_at": "2023-01-01T00:00:00"
        }]
    finally:
        # Clean up dependency overrides
        app.dependency_overrides.clear()
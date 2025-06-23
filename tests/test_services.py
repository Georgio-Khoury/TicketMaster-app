import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.Services.event_service import (
    get_events_service,
    save_event_service,
    get_favorites_service
)

# Fixtures
@pytest.fixture
def db():
    return MagicMock(spec=Session)

@pytest.fixture
def user_id():
    return 1

@pytest.fixture
def sample_event():
    return {"id": "event123", "name": "Sample Event"}

@pytest.fixture
def sample_favorite():
    return {"event_id": "event123", "user_id": 1}

# Test get_events_service
@patch("app.Services.event_service.get_events")
def test_get_events_service_success(mock_get_events, db):
    mock_get_events.return_value = ["event1", "event2"]
    result = get_events_service(db)
    assert result == ["event1", "event2"]

@patch("app.Services.event_service.get_events")
def test_get_events_service_failure(mock_get_events, db):
    mock_get_events.side_effect = Exception("DB error")
    with pytest.raises(HTTPException) as exc:
        get_events_service(db)
    assert exc.value.status_code == 500

# Test save_event_service
@patch("app.Services.event_service.save_event_repository")
@patch("app.Services.event_service.favorite_exists")
@patch("app.Services.event_service.event_exists")
def test_save_event_success(mock_event_exists, mock_favorite_exists, mock_save_repo, db, user_id):
    mock_event_exists.return_value = True
    mock_favorite_exists.return_value = False
    mock_save_repo.return_value = {"event_id": "123", "user_id": user_id}

    result = save_event_service("123", db, user_id)
    assert result == {"event_id": "123", "user_id": user_id}

@patch("app.Services.event_service.event_exists")
def test_save_event_not_found(mock_event_exists, db, user_id):
    mock_event_exists.return_value = False
    with pytest.raises(HTTPException) as exc:
        save_event_service("cf", db, user_id)
    assert exc.value.status_code == 404

@patch("app.Services.event_service.favorite_exists")
@patch("app.Services.event_service.event_exists")
def test_save_event_already_saved(mock_event_exists, mock_favorite_exists, db, user_id):
    mock_event_exists.return_value = True
    mock_favorite_exists.return_value = True
    with pytest.raises(HTTPException) as exc:
        save_event_service("123", db, user_id)
    assert exc.value.status_code == 400

# Test get_favorites_service
@patch("app.Services.event_service.get_favorites_repository")
@patch("app.Services.event_service.UserRepository.user_exists")
def test_get_favorites_success(mock_user_exists, mock_get_favorites, db, user_id):
    mock_user_exists.return_value = True
    mock_get_favorites.return_value = ["fav1", "fav2"]
    result = get_favorites_service(db, user_id)
    assert result == ["fav1", "fav2"]

@patch("app.Services.event_service.UserRepository.user_exists")
def test_get_favorites_user_not_found(mock_user_exists, db, user_id):
    mock_user_exists.return_value = False
    with pytest.raises(HTTPException) as exc:
        get_favorites_service(db, user_id)
    assert exc.value.status_code == 404

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.Models.event import EventSchema
from fastapi import HTTPException
from app.Services.event_service import (
    get_events_service,
    save_event_service,
    get_favorites_service
)
from app.Models.event import PaginatedEventsResponse, EventFilters

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

@pytest.fixture
def sample_filters():
    return EventFilters()

# Test get_events_service
@patch("app.Services.event_service.get_events")
@patch("app.Services.event_service.get_total_count")
@patch("app.Services.event_service.apply_sorting")
@patch("app.Services.event_service.apply_pagination")
def test_get_events_service_success(mock_pagination, mock_sorting, mock_count, mock_get_events, db, sample_filters):
    # Create real EventSchema objects
    event1 = EventSchema(
        id="event1",
        name="Event 1",
        description="Description 1",
        start_date="2023-01-01T00:00:00",
        venue_name="Venue 1",
        city="City 1",
        country="Country 1",
        url="http://example.com/1"
    )
    
    event2 = EventSchema(
        id="event2",
        name="Event 2",
        description="Description 2",
        start_date="2023-01-02T00:00:00",
        venue_name="Venue 2",
        city="City 2",
        country="Country 2",
        url="http://example.com/2"
    )
    
    # Setup mocks
    mock_get_events.return_value = MagicMock()
    mock_count.return_value = 2
    mock_sorting.return_value = MagicMock()
    mock_pagination.return_value = [event1, event2]
    
    # Call service
    result = get_events_service(
        db,
        page=1,
        per_page=10,
        filters=sample_filters,
        sort_by="start_date",
        sort_order="asc"
    )
    
    # Verify result
    assert isinstance(result, PaginatedEventsResponse)
    assert len(result.events) == 2
    assert result.events[0].id == "event1"
    assert result.events[1].id == "event2"
    assert result.total == 2
    assert result.page == 1
    assert result.per_page == 10
    assert result.total_pages == 1
    assert result.has_next is False
    assert result.has_prev is False

@patch("app.Services.event_service.get_events")
def test_get_events_service_failure(mock_get_events, db, sample_filters):
    mock_get_events.side_effect = Exception("DB error")
    with pytest.raises(HTTPException) as exc:
        get_events_service(db, 1, 10, sample_filters)
    assert exc.value.status_code == 500
    assert "Error fetching events" in str(exc.value.detail)

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
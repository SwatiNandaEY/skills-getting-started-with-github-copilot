"""Tests for the FastAPI application"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


def test_root_redirect(client):
    """Test that root URL redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]


def test_get_activities(client):
    """Test fetching all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    
    # Check that we have activities
    assert len(data) > 0
    
    # Check that expected activities exist
    assert "Basketball Team" in data
    assert "Soccer Club" in data
    assert "Drama Club" in data
    
    # Verify activity structure
    activity = data["Basketball Team"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert isinstance(activity["participants"], list)


def test_signup_for_activity(client):
    """Test successfully signing up for an activity"""
    response = client.post(
        "/activities/Basketball%20Team/signup",
        params={"email": "test@mergington.edu"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "Signed up" in data["message"]
    
    # Verify participant was added
    activities = client.get("/activities").json()
    assert "test@mergington.edu" in activities["Basketball Team"]["participants"]


def test_signup_duplicate_prevents_double_registration(client):
    """Test that duplicate registration is prevented"""
    email = "duplicate@mergington.edu"
    
    # First signup should succeed
    response1 = client.post(
        "/activities/Soccer%20Club/signup",
        params={"email": email}
    )
    assert response1.status_code == 200
    
    # Second signup with same email should fail
    response2 = client.post(
        "/activities/Soccer%20Club/signup",
        params={"email": email}
    )
    assert response2.status_code == 400
    assert "already signed up" in response2.json()["detail"]


def test_signup_nonexistent_activity(client):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/NonExistent%20Activity/signup",
        params={"email": "test@mergington.edu"}
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_from_activity(client):
    """Test unregistering from an activity"""
    email = "unreg@mergington.edu"
    
    # First signup
    client.post(
        "/activities/Drama%20Club/signup",
        params={"email": email}
    )
    
    # Verify participant was added
    activities = client.get("/activities").json()
    assert email in activities["Drama Club"]["participants"]
    
    # Now unregister
    response = client.delete(
        "/activities/Drama%20Club/unregister",
        params={"email": email}
    )
    assert response.status_code == 200
    assert "Unregistered" in response.json()["message"]
    
    # Verify participant was removed
    activities = client.get("/activities").json()
    assert email not in activities["Drama Club"]["participants"]


def test_unregister_nonexistent_activity(client):
    """Test unregistering from an activity that doesn't exist"""
    response = client.delete(
        "/activities/FakeActivity/unregister",
        params={"email": "test@mergington.edu"}
    )
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_not_registered_student(client):
    """Test unregistering a student who isn't registered"""
    response = client.delete(
        "/activities/Art%20Studio/unregister",
        params={"email": "notregistered@mergington.edu"}
    )
    assert response.status_code == 404
    assert "not registered" in response.json()["detail"]


def test_activity_has_correct_structure(client):
    """Test that activity objects have all required fields"""
    activities = client.get("/activities").json()
    
    for activity_name, activity_data in activities.items():
        assert isinstance(activity_data, dict)
        assert "description" in activity_data
        assert "schedule" in activity_data
        assert "max_participants" in activity_data
        assert "participants" in activity_data
        assert isinstance(activity_data["participants"], list)


def test_multiple_signups_different_activities(client):
    """Test signing up for multiple different activities"""
    email = "multi@mergington.edu"
    
    # Signup for multiple activities
    response1 = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": email}
    )
    assert response1.status_code == 200
    
    response2 = client.post(
        "/activities/Robotics%20Club/signup",
        params={"email": email}
    )
    assert response2.status_code == 200
    
    # Verify both signups worked
    activities = client.get("/activities").json()
    assert email in activities["Chess Club"]["participants"]
    assert email in activities["Robotics Club"]["participants"]

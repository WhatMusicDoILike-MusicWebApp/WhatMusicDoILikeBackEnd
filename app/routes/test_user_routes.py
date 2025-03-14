import pytest
from flask import Flask
from app import create_app, db  
from app.models import User  

@pytest.fixture
def client():
    app = create_app("testing")  
    print(app.config)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' 
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.session.remove()
            db.drop_all()

def test_new_user_success(client):
    """Test user creation with valid data"""
    response = client.post('/users', json={
        "userId": "123",
        "name": "Test User",
        "email": "test@example.com",
        "spotifyId": "spotify123",
        "youtubeId": "youtube123",
        "appleMusicId": "apple123"
    })
    
    assert response.status_code == 201
    assert response.json["message"] == "User created successfully!"

    # Verify user is in the database
    user = User.query.filter_by(userId="123").first()
    assert user is not None
    assert user.name == "Test User"

def test_new_user_missing_fields(client):
    """Test user creation failure when required fields are missing"""
    response = client.post('/users', json={})  
    assert response.status_code == 400
    assert response.json["error"] == "Missing required fields"

def test_new_user_duplicate(client):
    """Test handling of duplicate user creation"""
    client.post('/users', json={
        "userId": "123",
        "name": "Test User",
        "email": "test@example.com"
    })

    response = client.post('/users', json={
        "userId": "123",
        "name": "Duplicate User",
        "email": "duplicate@example.com"
    })
    
    assert response.status_code == 500  

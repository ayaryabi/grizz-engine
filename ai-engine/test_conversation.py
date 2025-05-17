import requests
import json
import sys
from app.db.database import SessionLocal
from app.db.models import User

def test_create_user_if_needed(email="test@example.com", username="testuser"):
    """Create a test user if needed"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Creating test user with email: {email}")
            user = User(email=email, username=username)
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"User created with ID: {user.id}")
        else:
            print(f"Using existing user with ID: {user.id}")
        
        return user.id
    finally:
        db.close()

def test_get_today_conversation(user_id, timezone="America/Los_Angeles"):
    """Test the /api/conversations/today endpoint"""
    url = f"http://localhost:8001/api/conversations/today?user_id={user_id}&timezone={timezone}"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Got today's conversation:")
            print(f"ID: {data['id']}")
            print(f"Title: {data['title']}")
            print(f"Created at: {data['created_at']}")
            return data['id']
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return None

if __name__ == "__main__":
    # Create a test user if needed
    user_id = test_create_user_if_needed()
    
    # Test getting today's conversation
    timezone = "America/Los_Angeles"
    if len(sys.argv) > 1:
        timezone = sys.argv[1]
    
    print(f"Testing with timezone: {timezone}")
    conversation_id = test_get_today_conversation(user_id, timezone) 
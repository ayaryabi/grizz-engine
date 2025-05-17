from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.models import User, Conversation, Message
import sys

def get_user_by_email(email: str):
    """
    Retrieve a user from the database by email
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            print(f"✅ User found!")
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Created at: {user.created_at}")
            
            # Get conversations for this user
            conversations = db.query(Conversation).filter(Conversation.user_id == user.id).all()
            print(f"\nConversations: {len(conversations)}")
            
            if conversations:
                for i, conv in enumerate(conversations):
                    print(f"\nConversation #{i+1}")
                    print(f"ID: {conv.id}")
                    print(f"Title: {conv.title}")
                    print(f"Created at: {conv.created_at}")
                    
                    # Get messages for this conversation
                    messages = db.query(Message).filter(Message.conversation_id == conv.id).all()
                    print(f"Messages: {len(messages)}")
            
            return user
        else:
            print(f"❌ No user found with email: {email}")
            return None
            
    finally:
        db.close()

if __name__ == "__main__":
    email = "arian.erp161@gmail.com"
    if len(sys.argv) > 1:
        email = sys.argv[1]
    
    print(f"Looking for user with email: {email}")
    user = get_user_by_email(email)
    
    if not user:
        print("\nWould you like to create this test user? (y/n)")
        response = input().strip().lower()
        if response == 'y':
            db = SessionLocal()
            try:
                new_user = User(
                    username="testuser",
                    email=email
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
                print(f"✅ Test user created with ID: {new_user.id}")
            except Exception as e:
                print(f"❌ Error creating user: {str(e)}")
                db.rollback()
            finally:
                db.close() 
from sqlalchemy import inspect, text
from app.db.database import engine
from app.db.models import User, Conversation, Message

def check_database_tables():
    """Check if all required database tables exist"""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    
    print(f"Available tables: {table_names}")
    
    # Check each table
    required_tables = ['users', 'conversations', 'messages']
    for table in required_tables:
        if table in table_names:
            print(f"✅ Table '{table}' exists")
            # Show columns
            columns = inspector.get_columns(table)
            print(f"   Columns: {', '.join(col['name'] for col in columns)}")
        else:
            print(f"❌ Table '{table}' does not exist")
    
    # Check if tables have data
    with engine.connect() as conn:
        for table in required_tables:
            if table in table_names:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   Records in '{table}': {count}")

if __name__ == "__main__":
    check_database_tables() 
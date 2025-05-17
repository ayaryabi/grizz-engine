import sys
import traceback
import logging
import socket
import re
from sqlalchemy import text
from app.db.database import engine
from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_connection():
    settings = get_settings()
    
    # Mask password for logging
    safe_url = settings.DATABASE_URL
    if '@' in safe_url:
        safe_url = re.sub(r'\/\/([^:]+):([^@]+)@', r'//\1:****@', safe_url)
    
    print(f"Testing connection to database: {safe_url}")
    
    # Extract hostname and port using regex
    hostname = None
    port = 5432  # Default PostgreSQL port
    
    if settings.DATABASE_URL.startswith("postgresql:"):
        # Extract hostname
        hostname_match = re.search(r'@([^:]+)(?::(\d+))?/', settings.DATABASE_URL)
        if hostname_match:
            hostname = hostname_match.group(1)
            if hostname_match.group(2):
                port = int(hostname_match.group(2))
        
        # Print connection details
        username_match = re.search(r'\/\/([^:]+):', settings.DATABASE_URL)
        username = username_match.group(1) if username_match else "unknown"
        
        db_name_match = re.search(r'\/([^?]+)(?:\?|$)', settings.DATABASE_URL)
        db_name = db_name_match.group(1) if db_name_match else "postgres"
        
        print(f"- Host: {hostname}")
        print(f"- Port: {port}")
        print(f"- Username: {username}")
        print(f"- Database: {db_name}")
        
        # Try a simple socket connection first
        if hostname:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                print(f"Attempting to connect to {hostname}:{port}...")
                result = sock.connect_ex((hostname, port))
                if result == 0:
                    print(f"Socket connection succeeded. Port is open.")
                else:
                    print(f"Socket connection failed. Error code: {result}")
            except Exception as e:
                print(f"Socket test failed: {str(e)}")
            finally:
                sock.close()
    
    try:
        # Try to execute a simple query
        print("Attempting SQLAlchemy connection...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Connection successful!")
            return True
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1) 
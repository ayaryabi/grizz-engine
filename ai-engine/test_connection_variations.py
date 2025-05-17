import sys
import psycopg2
import urllib.parse

# Your Supabase credentials
host = "aws-0-eu-central-1.pooler.supabase.com"
port = "6543"
user = "postgres.epubdombwmocadlxuskr"
password = "pIl2k6mk6UhKnU9J"  # Replace with your actual password
dbname = "postgres"

# Test variations of connection parameters
connection_variations = [
    # Direct parameters
    {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "dbname": dbname,
        "sslmode": "require"
    },
    
    # Connection URI with URL-encoded password
    f"postgresql://{user}:{urllib.parse.quote_plus(password)}@{host}:{port}/{dbname}?sslmode=require",
    
    # Connection URI without encoding
    f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode=require",
    
    # Pooler format from Supabase dashboard
    f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
]

# Try each variation
for i, connection_info in enumerate(connection_variations):
    print(f"\nTrying variation #{i+1}:")
    try:
        if isinstance(connection_info, dict):
            print(f"Using parameters: host={host}, port={port}, user={user}, password=****")
            conn = psycopg2.connect(**connection_info)
        else:
            # Mask password for logging
            safe_url = connection_info.replace(password, "****")
            print(f"Using connection string: {safe_url}")
            conn = psycopg2.connect(connection_info)
            
        print("✅ CONNECTION SUCCESSFUL!")
        
        # Test a simple query
        with conn.cursor() as cur:
            cur.execute("SELECT current_timestamp")
            result = cur.fetchone()
            print(f"Current timestamp from database: {result[0]}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ CONNECTION FAILED: {str(e)}")

print("\nTest completed.") 
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

# Get database connection parameters from environment variables
DB_URL = os.environ.get("DATABASE_URL")

# Strip postgresql:// prefix for asyncpg
if DB_URL.startswith("postgresql://"):
    # Extract connection parts
    parts = DB_URL[len("postgresql://"):]
    user_pass, host_port_db = parts.split("@", 1)
    user, password = user_pass.split(":", 1)
    host_port, dbname = host_port_db.split("/", 1)
    
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host = host_port
        port = "5432"
else:
    print("Could not parse DATABASE_URL. Should start with postgresql://")
    exit(1)

print(f"Connecting to {host}:{port} as {user} (database: {dbname})")

async def run_test():
    # Direct connection with asyncpg with statement cache disabled
    connection = await asyncpg.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=dbname,
        ssl="require",
        statement_cache_size=0,
    )
    
    try:
        # Test with a simple query
        print("Running simple query...")
        result = await connection.fetchval("SELECT 1")
        print(f"Result: {result}")
        
        # Run a second query to test statement caching is disabled
        print("Running second query...")
        result = await connection.fetchval("SELECT 2")
        print(f"Result: {result}")
        
        # Test with a parameterized query
        print("Running parameterized query...")
        result = await connection.fetchval("SELECT $1 + $2", 3, 4)
        print(f"Result: {result}")
        
        print("All tests passed!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        await connection.close()

if __name__ == "__main__":
    success = asyncio.run(run_test())
    exit(0 if success else 1) 
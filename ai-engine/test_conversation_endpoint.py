import requests
import pytz
from datetime import datetime

# Configuration - change these as needed
BASE_URL = "http://localhost:8000"  # Default FastAPI port
USER_ID = "6b9b58d8-b648-48d9-b431-70af03d7502b"  # The user ID you provided
TIMEZONE = "America/Los_Angeles"  # Example timezone

def test_get_conversation():
    """Test the GET endpoint with query parameters"""
    print("\n===== Testing GET /api/conversations/today =====")
    
    url = f"{BASE_URL}/api/conversations/today"
    params = {
        "user_id": USER_ID,
        "timezone": TIMEZONE
    }
    
    print(f"Making GET request to: {url}")
    print(f"With parameters: {params}")
    
    try:
        response = requests.get(url, params=params)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS! Response:")
            print(response.json())
        else:
            print("ERROR! Response:")
            try:
                print(response.json())
            except:
                print(response.text)
    except Exception as e:
        print(f"Request failed: {str(e)}")

def print_debug_info():
    """Print debugging information about the current time and timezone"""
    print("\n===== Debug Information =====")
    now_utc = datetime.now(pytz.UTC)
    print(f"Current UTC time: {now_utc}")
    
    try:
        local_tz = pytz.timezone(TIMEZONE)
        now_local = now_utc.astimezone(local_tz)
        print(f"Current {TIMEZONE} time: {now_local}")
        print(f"Local date only: {now_local.date()}")
        
        # This is what the endpoint would use
        today_start = datetime.combine(now_local.date(), datetime.min.time())
        today_start = local_tz.localize(today_start)
        today_start_utc = today_start.astimezone(pytz.UTC)
        print(f"Local midnight in UTC (for DB query): {today_start_utc}")
    except Exception as e:
        print(f"Timezone conversion error: {str(e)}")

if __name__ == "__main__":
    print("Starting conversation endpoint test...")
    test_get_conversation()
    print_debug_info()
    print("\nTest completed.") 
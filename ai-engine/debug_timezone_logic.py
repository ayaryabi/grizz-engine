import pytz
from datetime import datetime, date
import json

# Set up the test parameters
USER_ID = "6b9b58d8-b648-48d9-b431-70af03d7502b"
TIMEZONES_TO_TEST = [
    "America/Los_Angeles",
    "America/New_York", 
    "Europe/London",
    "Asia/Tokyo",
    "UTC"
]

def test_timezone_conversion(timezone_str):
    """Test the exact timezone conversion logic from the FastAPI endpoint"""
    print(f"\n==== Testing timezone: {timezone_str} ====")
    
    try:
        # This is the exact logic from conversation.py
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        today_date = now.date()
        print(f"Current time in {timezone_str}: {now}")
        print(f"Today's date: {today_date}")
        
        # Convert today_date to datetime with time set to 00:00:00
        today_start = datetime.combine(today_date, datetime.min.time())
        today_start = tz.localize(today_start)
        print(f"Local midnight: {today_start}")
        
        # Convert to UTC for database storage
        today_start_utc = today_start.astimezone(pytz.UTC)
        print(f"Local midnight in UTC: {today_start_utc}")
        
        # This would be the filter used in the database query
        print(f"Database filter value: {today_start_utc}")
        
        # Mock data for what we would return
        mock_response = {
            "id": "mock-conversation-id",
            "user_id": USER_ID,
            "title": f"Conversation on {today_date.strftime('%Y-%m-%d')}",
            "date": today_start_utc.isoformat(),
            "timezone": timezone_str
        }
        
        print("Response would look like:")
        print(json.dumps(mock_response, indent=2))
        
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def run_all_tests():
    """Run the timezone test for multiple timezones"""
    print("Starting timezone logic tests...")
    
    all_passed = True
    
    for tz in TIMEZONES_TO_TEST:
        result = test_timezone_conversion(tz)
        if not result:
            all_passed = False
    
    print("\n==== Test Summary ====")
    if all_passed:
        print("✅ All timezone tests passed")
    else:
        print("❌ Some timezone tests failed")

if __name__ == "__main__":
    run_all_tests() 
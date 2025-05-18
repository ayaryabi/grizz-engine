import requests
import json

# Configuration - change these as needed
BASE_URL = "http://localhost:8001"  # Check if backend is running on 8001 instead of 8000
NEXT_URL = "http://localhost:3000/api/chat/today"  # Next.js API route
USER_ID = "6b9b58d8-b648-48d9-b431-70af03d7502b"
TIMEZONE = "America/Los_Angeles"

def test_direct_api():
    """Test the FastAPI backend directly"""
    print("\n===== Testing Direct FastAPI Backend =====")
    
    # First try GET (as per backend code)
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
            print(json.dumps(response.json(), indent=2))
        else:
            print("ERROR! Response:")
            try:
                print(response.json())
            except:
                print(response.text)
    except Exception as e:
        print(f"Request failed: {str(e)}")
    
    # Now try POST (as per frontend code)
    print("\n----- Testing POST method -----")
    
    url = f"{BASE_URL}/api/conversations/today"
    data = {
        "user_id": USER_ID,
        "timezone": TIMEZONE
    }
    
    print(f"Making POST request to: {url}")
    print(f"With JSON body: {data}")
    
    try:
        response = requests.post(url, json=data)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS! Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("ERROR! Response:")
            try:
                print(response.json())
            except:
                print(response.text)
    except Exception as e:
        print(f"Request failed: {str(e)}")

def test_next_api():
    """Test the Next.js API route that the frontend is using"""
    print("\n===== Testing Next.js API Route =====")
    
    url = NEXT_URL
    data = {
        "timezone": TIMEZONE
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer fake-token-for-testing"  # This would be the actual auth token
    }
    
    print(f"Making POST request to: {url}")
    print(f"With JSON body: {data}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS! Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print("ERROR! Response:")
            try:
                print(response.json())
            except:
                print(response.text)
    except Exception as e:
        print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    print("Starting conversation endpoint tests...")
    test_direct_api()
    print("\n\nNOTE: The Next.js API test will likely fail unless you have valid auth.")
    print("This is just to show the format of the request the frontend is making.")
    # test_next_api()  # Uncomment if you want to test the Next.js API route
    print("\nTests completed.") 
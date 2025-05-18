#!/usr/bin/env python3
import os
import sys
import subprocess
import time

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def run_script(script_name):
    """Run a Python script and return True if successful"""
    print_header(f"RUNNING: {script_name}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=False,
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def main():
    """Run all test scripts"""
    print_header("CONVERSATION ENDPOINT TESTING")
    print("This will run all test scripts to diagnose the conversation endpoint.")
    
    # Current directory is where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the test scripts in order
    test_scripts = [
        "debug_timezone_logic.py",  # Test timezone logic first (pure Python, no HTTP)
        "test_conversation_endpoint.py",  # Test GET endpoint at port 8000
        "test_conversation_post.py"  # Test both GET and POST at port 8001
    ]
    
    # Run each test script
    for script in test_scripts:
        script_path = os.path.join(script_dir, script)
        success = run_script(script_path)
        
        # Add a small delay between script runs
        time.sleep(1)
    
    print_header("TESTING COMPLETE")
    print("Review the output above to diagnose any issues with the conversation endpoint.")
    print("Key things to check:")
    print("1. Is the FastAPI server running on port 8000 or 8001?")
    print("2. Are the timezone calculations correct?")
    print("3. Is the endpoint accepting GET requests as expected?")
    print("4. Is there a mismatch between frontend request format and backend expectations?")
    print("\nCheck which specific test succeeded or failed to narrow down the issue.")

if __name__ == "__main__":
    main() 
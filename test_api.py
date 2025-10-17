"""
Simple test script to verify the API endpoint works correctly.
Sends a sample payload to the running FastAPI server.
"""
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = "https://tds-project1-tawny.vercel.app/api-endpoint"
SECRET_KEY = os.getenv("SECRET_KEY", "Phlo9ywRxhjayA4qY0b139Z0aZJ5co7O") # Default for testing

# Sample payload
# NOTE: Get your personal webhook URL from https://webhook.site/
# Just visit the site and copy the unique URL shown
# WEBHOOK_URL = "https://webhook.site/f1c17b1c-a336-4c22-b788-311ff42762fa"
WEBHOOK_URL = "https://tds-project1.free.beeceptor.com"

payload = {
    "email": "test@example.com",
    "secret": SECRET_KEY,
    "task": "sample-task",
    "round": 1,
    "nonce": "test-nonce-123",
    "brief": "Create a simple landing page with a header, hero section, and call-to-action button. Use modern design with a gradient background.",
    "evaluation_url": WEBHOOK_URL,
    "attachments": []
}

def test_api():
    """
    Test the API endpoint by sending a POST request.
    """
    print("Testing AutoApp API endpoint...")
    print(f"Sending POST to: {API_URL}")
    print(f"Payload: {payload}")
    print("-" * 50)
    
    try:
        response = httpx.post(API_URL, json=payload, timeout=10.0)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print("-" * 50)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "ok":
                print("✓ Test PASSED! Request accepted.")
                print("\nBackground processing started...")
                print("Check your console/logs to see progress.")
                print(f"Check {WEBHOOK_URL} to see the evaluation submission.")
                print("\nExpected to see:")
                print("- A new GitHub repository created")
                print("- Files pushed to the repo")
                print("- Evaluation posted to webhook.site")
            else:
                print(f"✗ Test FAILED: {result.get('reason')}")
        else:
            print(f"✗ Test FAILED with status {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        print("\nMake sure:")
        print("1. The FastAPI server is running (uvicorn app:app --reload)")
        print("2. Your .env file has SECRET_KEY set")
        print("3. All dependencies are installed")


if __name__ == "__main__":
    test_api()

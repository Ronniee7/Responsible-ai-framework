import requests
import json

def test_gemini_endpoint():
    # Target URL matching your Django routing
    url = "http://127.0.0.1:8000/api/chat/"
    
    # Payload matching the exact expectations of your LLMFactory/GeminiProvider
    payload = {
        "provider": "gemini",
        "message": "Verify connection. Test message to Gemini provider."
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    print(f"Sending request to {url}...")
    
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=4))
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure your Django server is running via 'python manage.py runserver'.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_gemini_endpoint()
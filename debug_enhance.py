#!/usr/bin/env python3
"""Debug email enhancement endpoint"""

import requests
import json

BASE_URL = "http://localhost:8000/api"

enhance_request = {
    "subject": "Quick question about API",
    "body": "Hi, I wanted to ask about your API integration."
}

print("Testing enhancement endpoint...")
response = requests.post(f"{BASE_URL}/activate/email/enhance", json=enhance_request)
print(f"Status: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")

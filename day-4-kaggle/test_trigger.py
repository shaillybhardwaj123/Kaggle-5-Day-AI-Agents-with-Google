import json
import base64
import requests

url = "http://127.0.0.1:8080/apps/expense_agent/trigger/pubsub"

# Test payload
payload = {
    "amount": 150.0,
    "submitter": "alice@company.com",
    "category": "software",
    "description": "IDE License",
    "date": "2026-06-06"
}

# Encode to base64
encoded_data = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')

# Pub/Sub push notification envelope
pubsub_message = {
    "message": {
        "data": encoded_data,
        "messageId": "test-msg-12345"
    },
    "subscription": "projects/my-gcp-project/subscriptions/expense-trigger-sub"
}

headers = {
    "Content-Type": "application/json"
}

print(f"Sending Pub/Sub trigger payload to {url}...")
try:
    response = requests.post(url, json=pubsub_message, headers=headers)
    print("Response Status Code:", response.status_code)
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print("Failed to send request. Is the server running on port 8080?")
    print("Error:", e)

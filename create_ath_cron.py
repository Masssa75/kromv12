import requests
import json

# Create cron job for ATH processing
api_key = "r3DUAv++Rji6jI+ExSYoyA6FZKuaXmXj2WaGUEKX2+g="
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Create job that runs every 5 minutes
job_data = {
    "job": {
        "title": "KROM ATH Historical Calculator",
        "url": "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ath-historical",
        "requestMethod": 1,  # POST
        "enabled": True,
        "schedule": {
            "timezone": "UTC",
            "minutes": [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],  # Every 5 minutes
            "hours": [-1],
            "mdays": [-1],
            "months": [-1],
            "wdays": [-1]
        },
        "requestTimeout": 60,
        "body": json.dumps({"limit": 50})  # Process 50 tokens at a time
    }
}

response = requests.put("https://api.cron-job.org/jobs", headers=headers, json=job_data)
print(f"Status code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    job_id = response.json()["jobId"]
    print(f"\nCron job created successfully!")
    print(f"Job ID: {job_id}")
    print(f"Will process 50 tokens every 5 minutes")
    print(f"At this rate, all 5,654 tokens will be processed in ~9.4 hours")
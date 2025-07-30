import requests
import json

# Update cron job to add Authorization header
api_key = "r3DUAv++Rji6jI+ExSYoyA6FZKuaXmXj2WaGUEKX2+g="
job_id = 6404310

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Get current job details
get_response = requests.get(f"https://api.cron-job.org/jobs/{job_id}", headers=headers)
job_data = get_response.json()

# Add authorization header
job_data["job"]["header"] = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4"
}

# Update the job
update_response = requests.patch(f"https://api.cron-job.org/jobs/{job_id}", headers=headers, json=job_data)
print(f"Update status: {update_response.status_code}")
print(f"Response: {update_response.text}")

if update_response.status_code == 200:
    print("\nCron job updated successfully with Authorization header!")
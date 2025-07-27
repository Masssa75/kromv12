#!/usr/bin/env python3
import requests
import json

# Make request
response = requests.post('http://localhost:5001/api/chat', json={
    'message': 'Create a simple bar chart showing the top 10 groups by average ROI',
    'session_id': 'debug_json'
})

data = response.json()
resp_text = data.get('response', '')

print("RESPONSE LENGTH:", len(resp_text))
print("\nLOOKING FOR JSON BLOCKS...")

# Find JSON blocks
import re
json_pattern = r'```json\s*(\{[\s\S]*?\})\s*```'
matches = re.findall(json_pattern, resp_text)

print(f"Found {len(matches)} JSON blocks\n")

for i, match in enumerate(matches):
    print(f"JSON BLOCK {i+1}:")
    print(match[:200])
    print("...")
    try:
        parsed = json.loads(match)
        print("✅ Valid JSON!")
        print(f"Keys: {list(parsed.keys())}")
        if 'tool' in parsed:
            print(f"Tool: {parsed['tool']}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON Error: {e}")
    print("-" * 40)
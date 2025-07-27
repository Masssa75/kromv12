#!/usr/bin/env python3
import requests

# Clear any existing session
print("Clearing session and testing fresh...")

# Start with a completely fresh session
response = requests.post('http://localhost:5001/api/chat', json={
    'message': 'Create a simple bar chart showing the top 5 groups by call count. Use execute_analysis and set result = {"labels": group_names, "values": counts}',
    'session_id': 'fresh_session_test'
})

data = response.json()
print('\nResponse summary:')
print('- Tools used:', data.get('tools_used', []))
print('- Has visualization:', 'visualization' in data)
print('- Response mentions error:', 'error' in data.get('response', '').lower())

if 'visualization' in data:
    print('\n✅ SUCCESS! Visualization created')
    viz = data['visualization']
    print(f'- Type: {viz.get("type")}')
    print(f'- Title: {viz.get("title")}')
    print(f'- Data: {viz.get("data")}')
else:
    print('\n❌ No visualization')
    if 'error' in data.get('response', '').lower():
        print('Response preview:', data.get('response', '')[:300])
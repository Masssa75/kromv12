#!/usr/bin/env python3
import requests
import json

# Test visualization
response = requests.post('http://localhost:5001/api/chat', json={
    'message': 'Create a simple bar chart showing the top 10 groups by average ROI',
    'session_id': 'test_viz_now'
})

data = response.json()
print('Tools used:', data.get('tools_used', []))
print('Has visualization:', 'visualization' in data)

if 'visualization' in data:
    print('✅ SUCCESS! Visualization is working!')
    print('Type:', data['visualization'].get('type'))
    print('Title:', data['visualization'].get('title'))
    viz_data = data['visualization'].get('data', {})
    if 'labels' in viz_data:
        print(f'Number of items: {len(viz_data["labels"])}')
else:
    print('❌ No visualization data')
    # Show error if present
    if 'response' in data and 'error' in data['response'].lower():
        print('Error mentioned in response')
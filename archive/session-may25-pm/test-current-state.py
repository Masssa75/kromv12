#!/usr/bin/env python3
import requests
import json

# Test the exact same request
response = requests.post('http://localhost:5001/api/chat', json={
    'message': 'Pick an interesting analysis and run it. Execute code to analyze the data in a unique way and create a visualization. Surprise me with something insightful!',
    'session_id': 'debug_viz_test'
})

data = response.json()
print('Tools used:', data.get('tools_used', []))
print('Has visualization:', 'visualization' in data)

# If there's an error in the response
if 'matplotlib' in data.get('response', ''):
    print('\n❌ AI is trying to use matplotlib instead of returning data')
    print('This means the AI doesn\'t understand the visualization format')

# Try a more specific request
print('\n' + '='*60)
print('Testing with specific instructions...')

response2 = requests.post('http://localhost:5001/api/chat', json={
    'message': 'Create a bar chart showing top 10 groups by average ROI. Use execute_analysis tool and return result = {"labels": [...], "values": [...]}',
    'session_id': 'specific_test'
})

data2 = response2.json()
print('Tools used:', data2.get('tools_used', []))
print('Has visualization:', 'visualization' in data2)

if 'visualization' in data2:
    print('✅ SUCCESS with specific instructions!')
    viz = data2['visualization']
    print(f'Type: {viz.get("type")}')
    print(f'Data keys: {list(viz.get("data", {}).keys())}')
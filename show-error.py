#!/usr/bin/env python3
import requests
import json

# First, clear the session to start fresh
response = requests.post('http://localhost:5001/api/chat', json={
    'message': 'hi',
    'session_id': 'fresh_test'
})

# Now try the visualization
response = requests.post('http://localhost:5001/api/chat', json={
    'message': 'Create a simple bar chart showing the top 10 groups by average ROI',
    'session_id': 'fresh_test'
})

data = response.json()

# Extract the actual error from the tool results
if 'tools_used' in data and data['tools_used']:
    print("Tools were used:", data['tools_used'])
    
    # Look for error details in the response
    response_text = data.get('response', '')
    if 'Tool execution errors occurred:' in response_text:
        print("\n❌ TOOL EXECUTION ERROR FOUND:")
        # Extract the error message
        error_start = response_text.find('Tool execution errors occurred:')
        error_section = response_text[error_start:error_start+500]
        print(error_section)
    elif 'visualization' in data:
        print("\n✅ SUCCESS! Visualization data found")
        print("Type:", data['visualization'].get('type'))
        print("Title:", data['visualization'].get('title'))
    else:
        print("\n❓ No error but also no visualization")
        print("Response preview:", response_text[:200])
else:
    print("No tools were used")
    print("Response:", data.get('response', '')[:200])
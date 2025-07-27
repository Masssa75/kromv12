#!/usr/bin/env python3
import requests
import json

# Test what the AI is actually sending
response = requests.post('http://localhost:5001/api/chat', json={
    'message': 'Show me average ROI by network. Use execute_analysis with this exact code: conn = get_db_connection(); df = pd.read_sql("SELECT network, AVG(roi) as avg_roi FROM calls GROUP BY network", conn); result = {"labels": df["network"].tolist(), "values": df["avg_roi"].tolist()}',
    'session_id': 'test_specific_code'
})

data = response.json()
print('Tools used:', data.get('tools_used', []))
print('Has visualization:', 'visualization' in data)

if 'visualization' in data:
    print('✅ SUCCESS!')
    print('Title:', data['visualization'].get('title'))
else:
    print('\nResponse preview:')
    print(data.get('response', '')[:500])

# Let's also check what happens with the simplified code
print('\n' + '='*60)
print('Testing with minimal code...')

response2 = requests.post('http://localhost:5001/api/chat', json={
    'message': 'Create a bar chart. Use execute_analysis with code: result = {"labels": ["ETH", "SOL", "BSC"], "values": [10, 20, 15]}',
    'session_id': 'test_minimal'
})

data2 = response2.json()
print('Tools used:', data2.get('tools_used', []))
print('Has visualization:', 'visualization' in data2)
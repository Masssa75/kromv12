#!/usr/bin/env python3
import requests
import json

# Test the exact code the AI is trying to run
code = """conn = get_db_connection()

# Get ROI distribution by group
query = \"\"\"
SELECT 
    group_name,
    AVG(roi) as avg_roi,
    COUNT(*) as call_count
FROM calls 
WHERE roi > 0
GROUP BY group_name
HAVING call_count >= 50
ORDER BY avg_roi DESC
LIMIT 10
\"\"\"

df = pd.read_sql(query, conn)

result = {
    'labels': df['group_name'].tolist(),
    'values': df['avg_roi'].tolist()
}"""

# Make the request
response = requests.post('http://localhost:5001/api/chat', json={
    'message': f'Please run this exact code using execute_analysis: {code}',
    'session_id': 'test_exact'
})

data = response.json()
print('Tools used:', data.get('tools_used', []))
print('Has visualization:', 'visualization' in data)

# Also test a simple direct message
response2 = requests.post('http://localhost:5001/api/chat', json={
    'message': 'Use execute_analysis to create a bar chart with result = {"labels": ["A", "B", "C"], "values": [1, 2, 3]}',
    'session_id': 'test_simple'
})

data2 = response2.json()
print('\nSimple test:')
print('Tools used:', data2.get('tools_used', []))
print('Has visualization:', 'visualization' in data2)

if 'visualization' in data2:
    print('SUCCESS! Visualization data:', data2['visualization'])
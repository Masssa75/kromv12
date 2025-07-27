#!/usr/bin/env python3
import requests
import json

# Test with the exact same message you're using
response = requests.post('http://localhost:5001/api/chat', json={
    'message': 'Pick an interesting analysis and run it. Execute code to analyze the data in a unique way and create a visualization. Surprise me with something insightful!',
    'session_id': 'user_session'  # Using a consistent session ID
})

data = response.json()
print('='*60)
print('RESPONSE ANALYSIS:')
print('='*60)
print('Tools used:', data.get('tools_used', []))
print('Has visualization:', 'visualization' in data)

# Check if the response mentions errors
response_text = data.get('response', '')
if 'error' in response_text.lower() or 'apologize' in response_text.lower():
    print('\n❌ AI is reporting errors in response')
    print('First 300 chars of response:')
    print(response_text[:300])
else:
    print('\n✅ No errors mentioned in response')

if 'visualization' in data:
    print('\n✅ VISUALIZATION DATA FOUND:')
    viz = data['visualization']
    print(f'Type: {viz.get("type")}')
    print(f'Title: {viz.get("title")}')
    if 'data' in viz:
        viz_data = viz['data']
        if isinstance(viz_data, dict) and 'labels' in viz_data:
            print(f'Number of items: {len(viz_data["labels"])}')
            print(f'First 3 labels: {viz_data["labels"][:3]}')

# Check if this is a frontend display issue
print('\n' + '='*60)
print('NEXT STEPS:')
print('If visualization data exists but not showing in UI:')
print('1. Check browser console for JavaScript errors')
print('2. Refresh the page (Cmd+R)')
print('3. Clear browser cache')
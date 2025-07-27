#!/usr/bin/env python3
import requests
import json
import re

# Get the exact response with the error
response = requests.post('http://localhost:5001/api/chat', json={
    'message': 'Show me average ROI by network',
    'session_id': 'debug_ai_code'
})

data = response.json()
response_text = data.get('response', '')

# Extract the JSON block to see what code the AI is trying to run
json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', response_text)

if json_match:
    try:
        tool_call = json.loads(json_match.group(1))
        if 'params' in tool_call and 'code' in tool_call['params']:
            print("AI's code:")
            print("-" * 60)
            print(tool_call['params']['code'])
            print("-" * 60)
            
            # Check for import statements
            if 'import' in tool_call['params']['code']:
                print("\n❌ FOUND IMPORT STATEMENTS!")
                imports = [line for line in tool_call['params']['code'].split('\n') if 'import' in line]
                for imp in imports:
                    print(f"  - {imp}")
            else:
                print("\n✅ No import statements found")
    except:
        print("Could not parse JSON")
else:
    print("No JSON block found in response")
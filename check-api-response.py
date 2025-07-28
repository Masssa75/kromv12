import json
import urllib.request

# Check what the API returns
url = "https://lively-torrone-8199e0.netlify.app/api/analyzed?page=1&sortBy=created_at&sortOrder=desc&limit=5"

try:
    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode())
    
    print(f"API returned {len(data)} entries\n")
    
    for i, entry in enumerate(data):
        if isinstance(entry, dict):
            ticker = entry.get('ticker', 'N/A')
            krom_id = entry.get('krom_id', 'N/A')
        else:
            print(f"Entry {i} is not a dict: {type(entry)}")
            continue
        
        print(f"{ticker} (ID: {krom_id}):")
        print(f"- Has raw_data field: {'raw_data' in entry}")
        
        if 'raw_data' in entry and entry['raw_data']:
            raw_data = entry['raw_data']
            print(f"- raw_data type: {type(raw_data)}")
            print(f"- Has trade: {'trade' in raw_data if isinstance(raw_data, dict) else 'N/A'}")
            
            if isinstance(raw_data, dict) and 'trade' in raw_data and raw_data['trade']:
                print(f"- Buy price: ${raw_data['trade'].get('buyPrice', 'N/A')}")
        print()
        
except Exception as e:
    print(f"Error: {e}")
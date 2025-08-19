#!/usr/bin/env python3
"""
Test what web-browsing models actually see on JavaScript-heavy sites
"""
import requests
import json
import time

OPEN_ROUTER_API_KEY = "OPENROUTER_API_KEY_REMOVED"

def test_model_vision(model_id, model_name):
    """Ask model to describe exactly what they see on the website"""
    
    prompt = """Visit https://tharwa.finance/ and tell me EXACTLY what you see.

Please answer these specific questions:
1. Can you see a team section with names of team members? If yes, list the names.
2. Can you see a roadmap? If yes, what are the main milestones?
3. Can you see tokenomics information? If yes, what's the token distribution?
4. What specific product names or features are mentioned?
5. Are there any social media links (Twitter, Telegram, etc.)? List them.
6. Can you see any charts, graphs, or interactive elements?

Be very specific about what you can actually SEE vs what you're inferring."""
    
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {OPEN_ROUTER_API_KEY}',
            },
            json={
                'model': model_id,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0,
                'max_tokens': 1500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(content)
            return content
        else:
            print(f"Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def compare_with_parsed_content():
    """Show what we found with BeautifulSoup parsing"""
    
    print("\n" + "="*60)
    print("What BeautifulSoup (HTML Parser) Found:")
    print("="*60)
    print("""
From our earlier parsing:
1. Team section: NOT FOUND
2. Roadmap: NOT FOUND  
3. Tokenomics: NOT FOUND
4. Products mentioned: Limited content found
5. Social links: Only 2 found
6. Interactive elements: Cannot detect (JavaScript required)

Total static content: ~6,900 characters
Total page size: 99,087 characters
Missing: ~93% of the page content (loaded by JavaScript)
""")

def main():
    print("\n" + "="*80)
    print("TESTING: What Can AI Models Actually See on JavaScript Sites?")
    print("="*80)
    print("\nTarget: https://tharwa.finance/ (React/Next.js site)")
    
    # Test models that claim web browsing
    models_to_test = [
        ("moonshotai/kimi-k2", "Kimi K2"),
        ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash"),
        ("google/gemini-pro-1.5", "Gemini Pro 1.5"),
    ]
    
    results = []
    
    for model_id, model_name in models_to_test:
        result = test_model_vision(model_id, model_name)
        results.append({
            'model': model_name,
            'response': result
        })
        time.sleep(3)
    
    # Compare findings
    compare_with_parsed_content()
    
    print("\n" + "="*80)
    print("ANALYSIS:")
    print("="*80)
    
    for r in results:
        if r['response']:
            # Check what they found
            response_lower = r['response'].lower()
            
            print(f"\n{r['model']}:")
            print("-" * 40)
            
            # Check key indicators
            can_see_js = False
            
            if "cannot" in response_lower or "can't" in response_lower or "unable" in response_lower:
                print("❌ Likely CANNOT see JavaScript content")
            else:
                # Check for specific content mentions
                if "team" in response_lower and ("name" in response_lower or "member" in response_lower):
                    print("✓ Claims to see team information")
                    can_see_js = True
                else:
                    print("✗ No team information mentioned")
                
                if "roadmap" in response_lower and ("q1" in response_lower or "q2" in response_lower or "phase" in response_lower):
                    print("✓ Claims to see roadmap details")
                    can_see_js = True
                else:
                    print("✗ No roadmap details mentioned")
                
                if "tokenomics" in response_lower or "distribution" in response_lower:
                    print("✓ Claims to see tokenomics")
                    can_see_js = True
                else:
                    print("✗ No tokenomics mentioned")
            
            if not can_see_js:
                print("\n⚠️ CONCLUSION: Probably seeing same static HTML as our parser!")
    
    print("\n" + "="*80)
    print("FINAL VERDICT:")
    print("="*80)
    print("""
If the models cannot provide specific details about:
- Team member names
- Roadmap milestones  
- Token distribution percentages
- Interactive elements

Then they are likely only seeing the static HTML (same as BeautifulSoup),
NOT the JavaScript-rendered content!
""")

if __name__ == "__main__":
    main()
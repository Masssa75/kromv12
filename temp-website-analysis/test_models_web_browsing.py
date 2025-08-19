#!/usr/bin/env python3
"""
Test various AI models on OpenRouter for website analysis capabilities
"""
import requests
import json
import time

OPEN_ROUTER_API_KEY = "OPENROUTER_API_KEY_REMOVED"

# Models to test (Chinese and others known for good web capabilities)
MODELS_TO_TEST = [
    # Chinese models
    ("moonshotai/kimi-k2", "Kimi K2 - Moonshot AI"),
    ("deepseek/deepseek-chat", "DeepSeek Chat"),
    ("deepseek/deepseek-r1", "DeepSeek R1"),  
    ("qwen/qwen-2.5-72b-instruct", "Qwen 2.5 72B"),
    ("01-ai/yi-large", "Yi Large - 01.AI"),
    
    # Known good web browsing models
    ("google/gemini-2.0-flash-thinking-exp:free", "Gemini 2.0 Flash Thinking"),
    ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash"),
    ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet"),
    ("openai/gpt-4o", "GPT-4o"),
    ("perplexity/llama-3.1-sonar-large-128k-online", "Perplexity Sonar (has web access)")
]

def test_web_analysis(model_id, model_name):
    """Test if a model can analyze a website"""
    
    prompt = """Visit and analyze this website: https://www.graphai.tech/

Please describe:
1. What you see on the homepage
2. The main product or service offered
3. Whether there's a team section with names

If you cannot access the website, just say "Cannot access website"."""
    
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
                'temperature': 0.1,
                'max_tokens': 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Check if model actually accessed the website
            can_browse = False
            if any(phrase in content.lower() for phrase in [
                "homepage", "i can see", "the website shows", "displays", 
                "features", "navigation", "hero section", "the site"
            ]):
                can_browse = True
            elif "cannot access" in content.lower() or "don't have" in content.lower():
                can_browse = False
            else:
                # Ambiguous - check for specific details
                can_browse = "graphai" in content.lower() or "graph" in content.lower()
            
            return {
                'success': True,
                'can_browse': can_browse,
                'response_preview': content[:200] + "..." if len(content) > 200 else content
            }
        else:
            return {
                'success': False,
                'error': f"API error {response.status_code}",
                'can_browse': False
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'can_browse': False
        }

def main():
    print("Testing AI Models for Web Browsing Capabilities")
    print("=" * 60)
    print()
    
    results = []
    
    for model_id, model_name in MODELS_TO_TEST:
        print(f"Testing: {model_name}")
        print(f"Model ID: {model_id}")
        
        result = test_web_analysis(model_id, model_name)
        
        if result['success']:
            if result['can_browse']:
                print("✅ CAN browse websites")
            else:
                print("❌ CANNOT browse websites")
            print(f"Response: {result['response_preview']}")
        else:
            print(f"⚠️ Error: {result['error']}")
        
        results.append({
            'model': model_name,
            'model_id': model_id,
            'can_browse': result['can_browse'],
            'success': result['success']
        })
        
        print("-" * 60)
        time.sleep(2)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY - Models with Web Browsing Capability:")
    print("=" * 60)
    
    can_browse = [r for r in results if r['can_browse']]
    cannot_browse = [r for r in results if r['success'] and not r['can_browse']]
    failed = [r for r in results if not r['success']]
    
    print("\n✅ CAN Browse Websites:")
    for r in can_browse:
        print(f"  - {r['model']} ({r['model_id']})")
    
    print("\n❌ CANNOT Browse Websites:")
    for r in cannot_browse:
        print(f"  - {r['model']} ({r['model_id']})")
    
    if failed:
        print("\n⚠️ Failed to Test:")
        for r in failed:
            print(f"  - {r['model']} ({r['model_id']})")

if __name__ == "__main__":
    main()
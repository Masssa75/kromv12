#!/usr/bin/env python3
"""
Comprehensive test of all top AI models on OpenRouter for website analysis capabilities
"""
import requests
import json
import time
from datetime import datetime

OPEN_ROUTER_API_KEY = "OPENROUTER_API_KEY_REMOVED"

# Comprehensive list of top models
MODELS_TO_TEST = [
    # OpenAI Models
    ("openai/gpt-4o", "GPT-4o", "OpenAI"),
    ("openai/gpt-4o-mini", "GPT-4o Mini", "OpenAI"),
    ("openai/gpt-4-turbo", "GPT-4 Turbo", "OpenAI"),
    ("openai/o1-preview", "O1 Preview", "OpenAI"),
    ("openai/o1-mini", "O1 Mini", "OpenAI"),
    
    # Anthropic Models
    ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet", "Anthropic"),
    ("anthropic/claude-3.5-haiku", "Claude 3.5 Haiku", "Anthropic"),
    ("anthropic/claude-3-opus", "Claude 3 Opus", "Anthropic"),
    
    # Google Models
    ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash", "Google"),
    ("google/gemini-2.0-flash-thinking-exp:free", "Gemini 2.0 Flash Thinking", "Google"),
    ("google/gemini-pro-1.5", "Gemini Pro 1.5", "Google"),
    ("google/gemini-flash-1.5", "Gemini Flash 1.5", "Google"),
    ("google/gemini-flash-1.5-8b", "Gemini Flash 1.5 8B", "Google"),
    
    # Chinese Models - Moonshot AI (Kimi)
    ("moonshotai/kimi-k2", "Kimi K2", "Moonshot AI 🇨🇳"),
    ("moonshotai/kimi-k1.5", "Kimi K1.5", "Moonshot AI 🇨🇳"),
    
    # Chinese Models - DeepSeek
    ("deepseek/deepseek-chat", "DeepSeek Chat", "DeepSeek 🇨🇳"),
    ("deepseek/deepseek-r1", "DeepSeek R1", "DeepSeek 🇨🇳"),
    ("deepseek/deepseek-v3", "DeepSeek V3", "DeepSeek 🇨🇳"),
    ("deepseek/deepseek-reasoner", "DeepSeek Reasoner", "DeepSeek 🇨🇳"),
    
    # Chinese Models - Qwen (Alibaba)
    ("qwen/qwen-2.5-72b-instruct", "Qwen 2.5 72B", "Alibaba 🇨🇳"),
    ("qwen/qwen-2.5-32b-instruct", "Qwen 2.5 32B", "Alibaba 🇨🇳"),
    ("qwen/qwen-2.5-14b-instruct", "Qwen 2.5 14B", "Alibaba 🇨🇳"),
    ("qwen/qwen-2.5-7b-instruct", "Qwen 2.5 7B", "Alibaba 🇨🇳"),
    ("qwen/qwen-2-vl-72b-instruct", "Qwen 2 VL 72B (Vision)", "Alibaba 🇨🇳"),
    
    # Chinese Models - Yi (01.AI)
    ("01-ai/yi-large", "Yi Large", "01.AI 🇨🇳"),
    ("01-ai/yi-large-turbo", "Yi Large Turbo", "01.AI 🇨🇳"),
    ("01-ai/yi-vision", "Yi Vision", "01.AI 🇨🇳"),
    
    # Chinese Models - GLM (Zhipu AI)
    ("zhipuai/glm-4-plus", "GLM-4 Plus", "Zhipu AI 🇨🇳"),
    ("zhipuai/glm-4-flash", "GLM-4 Flash", "Zhipu AI 🇨🇳"),
    
    # Chinese Models - MiniMax
    ("minimax/minimax-01", "MiniMax-01", "MiniMax 🇨🇳"),
    
    # Chinese Models - Stepfun
    ("stepfun/step-2-16k", "Step 2 16K", "Stepfun 🇨🇳"),
    
    # Meta Models
    ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B", "Meta"),
    ("meta-llama/llama-3.2-90b-vision-instruct", "Llama 3.2 90B Vision", "Meta"),
    ("meta-llama/llama-3.1-405b-instruct", "Llama 3.1 405B", "Meta"),
    
    # Mistral Models
    ("mistralai/mistral-large", "Mistral Large", "Mistral AI"),
    ("mistralai/mixtral-8x22b-instruct", "Mixtral 8x22B", "Mistral AI"),
    ("mistralai/codestral", "Codestral", "Mistral AI"),
    
    # xAI Models
    ("x-ai/grok-2", "Grok 2", "xAI"),
    ("x-ai/grok-2-vision", "Grok 2 Vision", "xAI"),
    
    # Perplexity Models (with web search)
    ("perplexity/llama-3.1-sonar-large-128k-online", "Perplexity Sonar Large", "Perplexity"),
    ("perplexity/llama-3.1-sonar-small-128k-online", "Perplexity Sonar Small", "Perplexity"),
    
    # Cohere Models
    ("cohere/command-r-plus", "Command R Plus", "Cohere"),
    ("cohere/command-r", "Command R", "Cohere"),
    
    # AI21 Models
    ("ai21/jamba-1.5-large", "Jamba 1.5 Large", "AI21"),
    
    # Nous Research
    ("nousresearch/hermes-3-llama-3.1-405b", "Hermes 3 405B", "Nous Research"),
]

def test_web_capability(model_id, model_name, provider):
    """Test if a model can analyze a website"""
    
    # Simple prompt to test web access
    prompt = """Can you visit and analyze this website: https://example.com

Just tell me:
1. Can you access websites? (Yes/No)
2. What do you see on the page? (or say "Cannot access")

Keep your response under 100 words."""
    
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
                'max_tokens': 200
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].lower()
            
            # Determine capability
            if any(phrase in content for phrase in [
                "i can see", "the page shows", "example domain", "this domain is for use",
                "purple", "more information", "iana", "displays"
            ]):
                capability = "✅ YES"
            elif any(phrase in content for phrase in [
                "cannot access", "can't access", "don't have", "do not have", 
                "unable to", "cannot browse", "can't browse", "no, i"
            ]):
                capability = "❌ NO"
            else:
                capability = "🤔 UNCLEAR"
            
            # Extract brief response
            brief = content[:80] + "..." if len(content) > 80 else content
            
            return {
                'success': True,
                'capability': capability,
                'response': brief,
                'cost': result.get('usage', {}).get('total_cost', 0)
            }
        elif response.status_code == 404:
            return {
                'success': False,
                'capability': "⚠️ NOT FOUND",
                'response': "Model not available",
                'cost': 0
            }
        else:
            return {
                'success': False,
                'capability': "⚠️ ERROR",
                'response': f"API {response.status_code}",
                'cost': 0
            }
            
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'capability': "⏱️ TIMEOUT",
            'response': "Request timed out",
            'cost': 0
        }
    except Exception as e:
        return {
            'success': False,
            'capability': "⚠️ ERROR",
            'response': str(e)[:50],
            'cost': 0
        }

def main():
    print("\n" + "="*100)
    print(" "*30 + "AI MODELS WEB BROWSING CAPABILITY TEST")
    print(" "*35 + f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*100)
    print()
    
    results = []
    total_cost = 0
    
    # Group models by provider
    providers = {}
    for model_id, model_name, provider in MODELS_TO_TEST:
        if provider not in providers:
            providers[provider] = []
        providers[provider].append((model_id, model_name))
    
    # Test models grouped by provider
    for provider in sorted(providers.keys()):
        print(f"\n{'='*60}")
        print(f"  {provider}")
        print(f"{'='*60}")
        
        for model_id, model_name in providers[provider]:
            print(f"\n{model_name:<30} ", end="", flush=True)
            
            result = test_web_capability(model_id, model_name, provider)
            print(f"{result['capability']:<15}")
            
            if result['capability'] not in ["⚠️ NOT FOUND", "⚠️ ERROR", "⏱️ TIMEOUT"]:
                print(f"  └─ {result['response']}")
            
            results.append({
                'provider': provider,
                'model': model_name,
                'model_id': model_id,
                'capability': result['capability'],
                'response': result['response']
            })
            
            total_cost += result.get('cost', 0)
            time.sleep(0.5)  # Rate limiting
    
    # Summary
    print("\n" + "="*100)
    print(" "*35 + "SUMMARY REPORT")
    print("="*100)
    
    # Can browse
    can_browse = [r for r in results if r['capability'] == "✅ YES"]
    cannot_browse = [r for r in results if r['capability'] == "❌ NO"]
    unclear = [r for r in results if r['capability'] == "🤔 UNCLEAR"]
    unavailable = [r for r in results if r['capability'] in ["⚠️ NOT FOUND", "⚠️ ERROR", "⏱️ TIMEOUT"]]
    
    print(f"\n✅ CAN Browse Websites ({len(can_browse)} models):")
    print("-" * 60)
    for r in can_browse:
        print(f"  • {r['model']:<30} ({r['provider']})")
        print(f"    └─ Model ID: {r['model_id']}")
    
    print(f"\n❌ CANNOT Browse Websites ({len(cannot_browse)} models):")
    print("-" * 60)
    for r in cannot_browse:
        print(f"  • {r['model']:<30} ({r['provider']})")
    
    if unclear:
        print(f"\n🤔 UNCLEAR Results ({len(unclear)} models):")
        print("-" * 60)
        for r in unclear:
            print(f"  • {r['model']:<30} ({r['provider']})")
    
    if unavailable:
        print(f"\n⚠️ UNAVAILABLE/ERROR ({len(unavailable)} models):")
        print("-" * 60)
        for r in unavailable:
            print(f"  • {r['model']:<30} ({r['provider']}) - {r['capability']}")
    
    # Statistics
    print("\n" + "="*100)
    print("STATISTICS:")
    print(f"  Total models tested: {len(results)}")
    print(f"  Can browse: {len(can_browse)} ({len(can_browse)*100//len(results)}%)")
    print(f"  Cannot browse: {len(cannot_browse)} ({len(cannot_browse)*100//len(results)}%)")
    print(f"  Unclear: {len(unclear)} ({len(unclear)*100//len(results)}%)")
    print(f"  Unavailable: {len(unavailable)} ({len(unavailable)*100//len(results)}%)")
    print(f"  Estimated cost: ${total_cost:.4f}")
    
    # Save results
    with open('model_web_capabilities.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\n📁 Results saved to model_web_capabilities.json")

if __name__ == "__main__":
    main()
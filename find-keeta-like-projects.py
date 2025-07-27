#!/usr/bin/env python3
"""Find KEETA-like legitimate projects in crypto calls"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from anthropic import Anthropic
import time
from datetime import datetime

load_dotenv()

# Initialize
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

supabase = create_client(url, key)
anthropic = Anthropic(api_key=anthropic_key)

print("Finding KEETA-like legitimate crypto projects...")
print("=" * 60)

# Analysis prompt focused on finding legitimate projects
ANALYSIS_PROMPT = """Analyze this crypto announcement for signs of a legitimate project (like KEETA with real funding).

Message: {message}

Identify if this has:
- Real company/product (not memecoin)
- Specific funding amounts or investors mentioned
- Named team members or founders
- External validation (news sites, LinkedIn, etc)
- Technical product description

Rate 1-10 (10=very legitimate, 1=pure hype)
Format: SCORE:[number]|REASON:[brief reason]

Example: SCORE:9|REASON:$15M Series A from Sequoia, TechCrunch coverage"""

def analyze_batch(calls):
    """Analyze a batch of calls"""
    results = []
    
    for i, call in enumerate(calls):
        raw_data = call.get('raw_data')
        if not raw_data:
            continue
            
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except:
                continue
        
        message = raw_data.get('text', '')
        if len(message) < 50:  # Skip very short messages
            continue
        
        try:
            # Send to AI
            response = anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                temperature=0,
                system="You are analyzing crypto announcements to find legitimate projects with real backing.",
                messages=[{"role": "user", "content": ANALYSIS_PROMPT.format(message=message[:600])}]
            )
            
            result_text = response.content[0].text.strip()
            
            # Parse response
            score = 0
            reason = ""
            if "SCORE:" in result_text and "|REASON:" in result_text:
                parts = result_text.split("|")
                score_part = parts[0].split(":")[-1].strip()
                try:
                    score = float(score_part)
                except:
                    score = 0
                
                if len(parts) > 1:
                    reason = parts[1].replace("REASON:", "").strip()
            
            if score >= 7:  # Potential legitimate project
                results.append({
                    'ticker': call.get('ticker', 'Unknown'),
                    'score': score,
                    'reason': reason,
                    'date': call.get('created_at', '')[:10],
                    'original_rating': f"C:{call.get('analysis_tier', '?')} X:{call.get('x_analysis_tier', '?')}",
                    'message_preview': message[:150] + '...',
                    'krom_id': call.get('krom_id', '')
                })
                
                # Print as we find them
                print(f"\n🎯 Found: {call.get('ticker')} (Score: {score})")
                print(f"   Reason: {reason}")
                print(f"   Original: {results[-1]['original_rating']}")
            
            # Rate limiting
            if i > 0 and i % 20 == 0:
                print(f"\n...Processed {i} calls so far...")
                time.sleep(1)
                
        except Exception as e:
            continue
    
    return results

# Main execution
try:
    # First, let's check recent calls (last week)
    print("\nAnalyzing recent calls (last 7 days)...")
    
    result = supabase.table('crypto_calls') \
        .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at, krom_id') \
        .gte('created_at', '2025-07-07') \
        .order('created_at', desc=True) \
        .limit(200) \
        .execute()
    
    print(f"Found {len(result.data)} recent calls to analyze")
    
    # Analyze
    start_time = time.time()
    legitimate_projects = analyze_batch(result.data)
    elapsed = time.time() - start_time
    
    # Results
    print(f"\n{'='*60}")
    print(f"ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Time: {elapsed:.1f} seconds")
    print(f"Calls analyzed: {len(result.data)}")
    print(f"Legitimate projects found: {len(legitimate_projects)}")
    
    # Sort by score
    legitimate_projects.sort(key=lambda x: x['score'], reverse=True)
    
    # Show top finds
    if legitimate_projects:
        print(f"\n{'='*60}")
        print("TOP LEGITIMATE PROJECTS (KEETA-LIKE)")
        print(f"{'='*60}")
        
        for proj in legitimate_projects[:10]:
            print(f"\n{proj['ticker']} - Score: {proj['score']}/10")
            print(f"Date: {proj['date']}")
            print(f"Reason: {proj['reason']}")
            print(f"Original ratings: {proj['original_rating']}")
            print(f"Message: {proj['message_preview']}")
    
    # Check if we missed any ALPHA calls
    missed_alphas = [p for p in legitimate_projects if 'ALPHA' not in p['original_rating'] and p['score'] >= 8]
    if missed_alphas:
        print(f"\n{'='*60}")
        print(f"POTENTIALLY MISSED GEMS (High score but not rated ALPHA)")
        print(f"{'='*60}")
        for proj in missed_alphas[:5]:
            print(f"\n{proj['ticker']} - Should investigate further")
            print(f"AI Score: {proj['score']} | Original: {proj['original_rating']}")
            print(f"Why legitimate: {proj['reason']}")
    
    # Save results
    output = {
        'analysis_date': datetime.now().isoformat(),
        'calls_analyzed': len(result.data),
        'legitimate_found': len(legitimate_projects),
        'projects': legitimate_projects,
        'missed_gems': missed_alphas
    }
    
    with open('keeta_like_projects.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults saved to keeta_like_projects.json")
    print(f"Estimated cost: ${len(result.data) * 0.00008:.2f}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
#!/usr/bin/env python3
"""
Test CREATOR parsing with comprehensive analyzer
"""
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import json

def test_creator():
    analyzer = ComprehensiveWebsiteAnalyzer()
    url = "https://creatordao.com"
    
    print(f"Testing {url}")
    print("="*60)
    
    # Parse the website
    parsed_data = analyzer.parse_website_with_playwright(url)
    
    print(f"\n1. Parse Success: {parsed_data['success']}")
    print(f"2. Content Length: {len(parsed_data['content'].get('text', ''))} chars")
    print(f"3. LinkedIn Profiles Found: {len(parsed_data.get('team_data', {}).get('linkedin_profiles', []))}")
    print(f"4. Team Sections Found: {len(parsed_data.get('team_data', {}).get('sections_found', []))}")
    print(f"5. Documents Found: {len(parsed_data.get('documents', []))}")
    
    # Show team sections if found
    team_sections = parsed_data.get('team_data', {}).get('sections_found', [])
    if team_sections:
        print("\n📋 Team Sections Content:")
        for i, section in enumerate(team_sections, 1):
            print(f"\n   Section {i}: {section[:300]}...")
    else:
        print("\n❌ No team sections captured")
    
    # Check if "Kong" or "founder" appears in the content
    content = parsed_data['content'].get('text', '')
    if 'Kong' in content:
        # Find context around Kong
        idx = content.find('Kong')
        context = content[max(0, idx-100):min(len(content), idx+300)]
        print(f"\n✅ 'Kong' found in content:")
        print(f"   Context: ...{context}...")
    else:
        print("\n❌ 'Kong' not found in parsed content")
    
    if 'founder' in content.lower():
        idx = content.lower().find('founder')
        context = content[max(0, idx-100):min(len(content), idx+200)]
        print(f"\n✅ 'founder' found in content:")
        print(f"   Context: ...{context}...")
    
    # Show what will be sent to AI
    print("\n📤 Content that will be analyzed by AI:")
    print(f"   First 500 chars: {content[:500]}...")
    
    # Save raw parsed data for inspection
    with open('creator_parsed_data.json', 'w') as f:
        # Convert to serializable format
        serializable = {
            'url': parsed_data.get('url'),
            'success': parsed_data.get('success'),
            'content_length': len(parsed_data.get('content', {}).get('text', '')),
            'content_preview': parsed_data.get('content', {}).get('text', '')[:1000],
            'linkedin_count': len(parsed_data.get('team_data', {}).get('linkedin_profiles', [])),
            'team_sections_count': len(parsed_data.get('team_data', {}).get('sections_found', [])),
            'team_sections': parsed_data.get('team_data', {}).get('sections_found', [])[:3],
            'documents': parsed_data.get('documents', [])
        }
        json.dump(serializable, f, indent=2)
    print("\n💾 Saved parsed data to creator_parsed_data.json")

if __name__ == "__main__":
    test_creator()
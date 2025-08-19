#!/usr/bin/env python3
"""
Smart document parser that:
1. Identifies all important documents (PDFs, whitepapers, docs)
2. Handles single-page sites with sections
3. Intelligently decides what to parse based on importance
"""
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import json
import time
from urllib.parse import urljoin, urlparse
from datetime import datetime

class SmartDocumentParser:
    def __init__(self, base_url):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.main_page_content = None
        self.documents = []
        self.sections = []
        
    def analyze_site_structure(self):
        """Analyze if site is single-page or multi-page and find all documents"""
        print(f"\n🔍 Analyzing site structure for {self.base_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Load main page
            page.goto(self.base_url, wait_until='networkidle')
            page.wait_for_timeout(3000)
            
            # Get full page content
            self.main_page_content = page.evaluate("() => document.body.innerText")
            
            # Check if it's a single-page site (most content in anchors)
            links = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    const anchors = links.filter(a => a.href.includes('#')).length;
                    const external = links.filter(a => !a.href.includes(window.location.hostname)).length;
                    const total = links.length;
                    
                    return {
                        total: total,
                        anchors: anchors,
                        external: external,
                        is_single_page: (anchors / total) > 0.3  // >30% anchors = likely single page
                    };
                }
            """)
            
            print(f"  • Site type: {'Single-page' if links['is_single_page'] else 'Multi-page'}")
            print(f"  • Total links: {links['total']} (Anchors: {links['anchors']}, External: {links['external']})")
            
            # Find all documents (PDFs, docs, whitepapers)
            documents = page.evaluate("""
                () => {
                    const docs = [];
                    const docKeywords = ['whitepaper', 'pdf', 'docs', 'documentation', 'litepaper', 'deck', 'presentation'];
                    
                    document.querySelectorAll('a[href]').forEach(a => {
                        const href = a.href.toLowerCase();
                        const text = (a.innerText || '').toLowerCase();
                        
                        // Check if it's a document
                        const isDoc = href.includes('.pdf') || 
                                     href.includes('docs.') || 
                                     href.includes('gitbook') ||
                                     href.includes('github.com') ||
                                     docKeywords.some(kw => href.includes(kw) || text.includes(kw));
                        
                        if (isDoc) {
                            docs.push({
                                url: a.href,
                                text: a.innerText || 'Document',
                                type: href.includes('.pdf') ? 'pdf' : 
                                      href.includes('github') ? 'github' :
                                      href.includes('gitbook') ? 'gitbook' : 'docs'
                            });
                        }
                    });
                    
                    return docs;
                }
            """)
            
            self.documents = documents
            
            # Find all sections on the page
            if links['is_single_page']:
                sections = page.evaluate("""
                    () => {
                        const sections = [];
                        // Look for section headers
                        document.querySelectorAll('section, [id], [class*="section"]').forEach(elem => {
                            const id = elem.id;
                            const heading = elem.querySelector('h1, h2, h3');
                            if (heading) {
                                sections.push({
                                    id: id || elem.className,
                                    title: heading.innerText,
                                    content_length: elem.innerText.length
                                });
                            }
                        });
                        return sections;
                    }
                """)
                self.sections = sections
            
            browser.close()
        
        print(f"\n📚 Documents found: {len(self.documents)}")
        for doc in self.documents:
            print(f"    • [{doc['type'].upper()}] {doc['text'][:50]}")
            print(f"      {doc['url'][:80]}")
        
        if self.sections:
            print(f"\n📑 Page sections found: {len(self.sections)}")
            for section in self.sections[:5]:
                print(f"    • {section['title']} ({section['content_length']} chars)")
        
        return {
            'is_single_page': links['is_single_page'],
            'documents': self.documents,
            'sections': self.sections
        }
    
    def extract_team_from_content(self, content):
        """Extract team information from content using patterns"""
        team_info = {
            'members': [],
            'has_linkedin': False,
            'has_photos': False
        }
        
        # Look for LinkedIn URLs in the content
        import re
        linkedin_pattern = r'linkedin\.com/in/([a-zA-Z0-9-]+)'
        linkedin_matches = re.findall(linkedin_pattern, content)
        
        if linkedin_matches:
            team_info['has_linkedin'] = True
            team_info['linkedin_profiles'] = [f"https://linkedin.com/in/{m}" for m in linkedin_matches]
        
        # Look for common name patterns near titles
        # This is a simple pattern - could be enhanced
        exec_titles = ['CEO', 'CTO', 'CFO', 'COO', 'Founder', 'Co-founder', 'Advisor', 'Head of', 'Director']
        for title in exec_titles:
            # Look for pattern: Name + Title or Title + Name
            pattern = rf'([A-Z][a-z]+ [A-Z][a-z]+)\s*[,-]?\s*{title}'
            matches = re.findall(pattern, content)
            for match in matches:
                team_info['members'].append({'name': match, 'role': title})
        
        return team_info
    
    def create_analysis_prompt(self, site_data):
        """Create a comprehensive prompt for AI analysis"""
        prompt = f"""Analyze this crypto project website based on the comprehensive data extracted:

WEBSITE: {self.base_url}

SITE STRUCTURE:
- Type: {'Single-page' if site_data['is_single_page'] else 'Multi-page'} website
- Documents found: {len(self.documents)}
- Sections identified: {len(self.sections)}

MAIN CONTENT ({len(self.main_page_content)} characters total):
{self.main_page_content[:3000]}

DOCUMENTS AVAILABLE:"""
        
        for doc in self.documents[:5]:
            prompt += f"\n- [{doc['type'].upper()}] {doc['text']}: {doc['url'][:60]}"
        
        if self.sections:
            prompt += "\n\nPAGE SECTIONS:"
            for section in self.sections[:8]:
                prompt += f"\n- {section['title']}"
        
        # Add team info if found
        team_info = self.extract_team_from_content(self.main_page_content)
        if team_info['members']:
            prompt += "\n\nTEAM MEMBERS DETECTED:"
            for member in team_info['members'][:10]:
                prompt += f"\n- {member['name']} ({member['role']})"
        
        if team_info['has_linkedin']:
            prompt += f"\n\nLinkedIn profiles found: {len(team_info.get('linkedin_profiles', []))}"
        
        prompt += """

ANALYSIS REQUIRED:
1. What specific team members can you identify with full names?
2. Are there external documents (whitepaper, docs) that should be reviewed?
3. Is this a single-page marketing site or a comprehensive project site?
4. What are the most important pieces of information present vs missing?
5. Overall legitimacy assessment

Provide your analysis as JSON:
{
  "team_members_found": ["list of specific names"],
  "documents_importance": "assessment of whether docs need to be fetched",
  "site_depth": "single-page marketing" or "comprehensive multi-page",
  "missing_critical_info": ["list what's missing"],
  "legitimacy_score": 1-10,
  "recommendation": "what additional parsing would be most valuable"
}

Return ONLY the JSON."""
        
        return prompt
    
    def analyze_with_ai(self, site_data):
        """Get AI analysis of what to parse next"""
        OPEN_ROUTER_API_KEY = "OPENROUTER_API_KEY_REMOVED"
        
        prompt = self.create_analysis_prompt(site_data)
        
        print("\n🤖 Getting AI recommendation on what to parse next...")
        
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPEN_ROUTER_API_KEY}',
                },
                json={
                    'model': 'anthropic/claude-3.5-sonnet',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.1,
                    'max_tokens': 1000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse JSON
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                else:
                    return {'error': 'Could not parse JSON response'}
            else:
                return {'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': str(e)}


def main():
    print("\n" + "="*80)
    print("SMART DOCUMENT PARSER - Intelligent Content Discovery")
    print("="*80)
    
    # Test with TRWA
    url = "https://tharwa.finance/"
    
    parser = SmartDocumentParser(url)
    
    # Analyze site structure
    site_data = parser.analyze_site_structure()
    
    # Get AI recommendation
    ai_analysis = parser.analyze_with_ai(site_data)
    
    print("\n🎯 AI Analysis & Recommendations:")
    print("-" * 40)
    
    if 'error' not in ai_analysis:
        print(f"Team members found: {', '.join(ai_analysis.get('team_members_found', []))}")
        print(f"Site depth: {ai_analysis.get('site_depth', 'Unknown')}")
        print(f"Legitimacy score: {ai_analysis.get('legitimacy_score', 'N/A')}/10")
        print(f"\nRecommendation: {ai_analysis.get('recommendation', 'No recommendation')}")
        
        if ai_analysis.get('missing_critical_info'):
            print(f"\nMissing critical info:")
            for item in ai_analysis['missing_critical_info']:
                print(f"  • {item}")
    else:
        print(f"Error in analysis: {ai_analysis['error']}")
    
    # Save results
    output = {
        'website': url,
        'site_structure': site_data,
        'ai_analysis': ai_analysis,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('smart_parse_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n📁 Results saved to smart_parse_results.json")
    
    # Decision point
    print("\n" + "="*80)
    print("NEXT STEPS BASED ON ANALYSIS")
    print("="*80)
    
    if ai_analysis.get('documents_importance') == 'high' or 'whitepaper' in str(ai_analysis.get('recommendation', '')).lower():
        print("📄 → Should fetch and parse external documents (whitepaper, docs)")
    
    if len(ai_analysis.get('team_members_found', [])) < 3:
        print("👥 → Need deeper team extraction from page sections")
    
    if 'single-page' in ai_analysis.get('site_depth', ''):
        print("📑 → Focus on section-by-section analysis of main page")
    else:
        print("🔗 → Should explore additional pages for more information")

if __name__ == "__main__":
    main()
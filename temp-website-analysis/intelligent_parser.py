#!/usr/bin/env python3
"""
Intelligent two-stage website parser:
1. First pass: Map the website structure and identify important pages
2. Second pass: Deep parse the most relevant pages (docs, whitepaper, team, etc.)
"""
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import json
import time
from urllib.parse import urljoin, urlparse
from datetime import datetime

class IntelligentWebsiteParser:
    def __init__(self, base_url):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.discovered_pages = {}
        self.important_pages = []
        
    def stage1_discover_structure(self):
        """First stage: Quick discovery of website structure and important pages"""
        print(f"\n🔍 STAGE 1: Discovering website structure for {self.base_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Load main page
            page.goto(self.base_url, wait_until='networkidle')
            page.wait_for_timeout(2000)
            
            # Get all links
            links = page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        links.push({
                            href: a.href,
                            text: a.innerText || a.textContent || '',
                            classes: a.className
                        });
                    });
                    return links;
                }
            """)
            
            # Categorize links by importance
            high_priority_keywords = [
                'whitepaper', 'docs', 'documentation', 'litepaper',
                'team', 'about', 'founders', 'leadership',
                'tokenomics', 'token', 'distribution',
                'roadmap', 'milestones', 'timeline',
                'audit', 'security', 'contract'
            ]
            
            medium_priority_keywords = [
                'blog', 'news', 'updates', 'medium',
                'partners', 'investors', 'advisors',
                'faq', 'help', 'support'
            ]
            
            for link in links:
                href = link['href']
                text = link['text'].lower()
                
                # Skip external links unless they're important docs
                if self.domain not in href and not any(kw in text for kw in ['whitepaper', 'docs', 'github']):
                    continue
                
                # Categorize by priority
                priority = 'low'
                for keyword in high_priority_keywords:
                    if keyword in text or keyword in href.lower():
                        priority = 'high'
                        break
                
                if priority == 'low':
                    for keyword in medium_priority_keywords:
                        if keyword in text or keyword in href.lower():
                            priority = 'medium'
                            break
                
                self.discovered_pages[href] = {
                    'text': link['text'],
                    'priority': priority,
                    'type': self._classify_page_type(href, text)
                }
            
            # Also check for PDF/document links
            pdf_links = page.evaluate("""
                () => {
                    const pdfs = [];
                    document.querySelectorAll('a[href*=".pdf"], a[href*="whitepaper"], a[href*="docs"]').forEach(a => {
                        pdfs.push({
                            href: a.href,
                            text: a.innerText || 'PDF Document'
                        });
                    });
                    return pdfs;
                }
            """)
            
            for pdf in pdf_links:
                self.discovered_pages[pdf['href']] = {
                    'text': pdf['text'],
                    'priority': 'high',
                    'type': 'document'
                }
            
            browser.close()
        
        # Select pages to deep parse
        self.important_pages = [
            url for url, info in self.discovered_pages.items() 
            if info['priority'] in ['high', 'medium']
        ]
        
        print(f"  ✅ Discovered {len(self.discovered_pages)} total pages")
        print(f"  📌 Identified {len(self.important_pages)} important pages to parse:")
        
        for url in self.important_pages[:10]:  # Show first 10
            info = self.discovered_pages[url]
            print(f"    • [{info['priority'].upper()}] {info['type']}: {info['text'][:50]}")
            print(f"      {url[:80]}")
        
        return self.discovered_pages
    
    def _classify_page_type(self, url, text):
        """Classify what type of page this is"""
        url_lower = url.lower()
        text_lower = text.lower()
        
        if 'whitepaper' in url_lower or 'whitepaper' in text_lower:
            return 'whitepaper'
        elif 'team' in url_lower or 'team' in text_lower or 'about' in text_lower:
            return 'team'
        elif 'docs' in url_lower or 'documentation' in text_lower:
            return 'documentation'
        elif 'tokenomics' in url_lower or 'token' in text_lower:
            return 'tokenomics'
        elif 'roadmap' in url_lower or 'roadmap' in text_lower:
            return 'roadmap'
        elif '.pdf' in url_lower:
            return 'pdf'
        elif 'github' in url_lower:
            return 'github'
        else:
            return 'page'
    
    def stage2_deep_parse(self, max_pages=5):
        """Second stage: Deep parse the most important pages"""
        print(f"\n📊 STAGE 2: Deep parsing {min(max_pages, len(self.important_pages))} important pages")
        
        parsed_content = {}
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            for i, url in enumerate(self.important_pages[:max_pages]):
                info = self.discovered_pages[url]
                print(f"\n  [{i+1}/{min(max_pages, len(self.important_pages))}] Parsing {info['type']}: {url[:80]}")
                
                try:
                    page = browser.new_page()
                    
                    # Handle PDFs differently
                    if url.endswith('.pdf'):
                        print("    📄 PDF detected - would need special handling")
                        parsed_content[url] = {
                            'type': 'pdf',
                            'content': 'PDF parsing requires additional libraries',
                            'url': url
                        }
                        continue
                    
                    # Load the page
                    page.goto(url, wait_until='networkidle', timeout=15000)
                    page.wait_for_timeout(2000)
                    
                    # Extract content based on page type
                    if info['type'] == 'team':
                        content = self._extract_team_content(page)
                    elif info['type'] == 'documentation':
                        content = self._extract_documentation_content(page)
                    elif info['type'] == 'tokenomics':
                        content = self._extract_tokenomics_content(page)
                    else:
                        content = self._extract_general_content(page)
                    
                    parsed_content[url] = {
                        'type': info['type'],
                        'priority': info['priority'],
                        'content': content,
                        'url': url
                    }
                    
                    page.close()
                    print(f"    ✅ Extracted {len(content.get('text', ''))} characters")
                    
                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    parsed_content[url] = {
                        'type': info['type'],
                        'error': str(e),
                        'url': url
                    }
            
            browser.close()
        
        return parsed_content
    
    def _extract_team_content(self, page):
        """Extract team-specific content"""
        content = {}
        
        # Get all text
        content['text'] = page.evaluate("() => document.body.innerText")
        
        # Look for team member cards
        team_members = page.evaluate("""
            () => {
                const members = [];
                // Try multiple selectors for team member cards
                const selectors = [
                    '[class*="team-member"]',
                    '[class*="member-card"]',
                    '[class*="team"] [class*="card"]',
                    '[class*="founder"]',
                    '[class*="advisor"]'
                ];
                
                selectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(card => {
                        const text = card.innerText || '';
                        if (text.length > 10) {
                            members.push(text);
                        }
                    });
                });
                
                return members;
            }
        """)
        
        content['team_members_raw'] = team_members
        
        # Look for LinkedIn links
        linkedin_links = page.evaluate("""
            () => {
                const links = [];
                document.querySelectorAll('a[href*="linkedin.com"]').forEach(a => {
                    links.push({
                        url: a.href,
                        text: a.innerText || a.closest('[class*="member"], [class*="team"]')?.innerText || ''
                    });
                });
                return links;
            }
        """)
        
        content['linkedin_profiles'] = linkedin_links
        
        return content
    
    def _extract_documentation_content(self, page):
        """Extract documentation content"""
        content = {}
        
        # Get main content area
        content['text'] = page.evaluate("""
            () => {
                // Try to find main documentation content
                const selectors = [
                    'main', 
                    'article',
                    '[class*="content"]',
                    '[class*="docs"]',
                    '.markdown-body'
                ];
                
                for (const selector of selectors) {
                    const elem = document.querySelector(selector);
                    if (elem && elem.innerText.length > 500) {
                        return elem.innerText;
                    }
                }
                
                return document.body.innerText;
            }
        """)
        
        # Get all headers for structure
        content['headers'] = page.evaluate("""
            () => {
                const headers = [];
                document.querySelectorAll('h1, h2, h3').forEach(h => {
                    headers.push({
                        level: h.tagName,
                        text: h.innerText
                    });
                });
                return headers;
            }
        """)
        
        return content
    
    def _extract_tokenomics_content(self, page):
        """Extract tokenomics information"""
        content = {}
        
        content['text'] = page.evaluate("() => document.body.innerText")
        
        # Look for specific tokenomics data
        content['token_data'] = page.evaluate("""
            () => {
                const data = {};
                const text = document.body.innerText.toLowerCase();
                
                // Try to find supply information
                const supplyMatch = text.match(/total supply[:\\s]+([\\d,\\.]+\\s*\\w+)/i);
                if (supplyMatch) data.total_supply = supplyMatch[1];
                
                // Look for percentages (distribution)
                const percentages = [];
                const percentMatches = text.matchAll(/(\\d+(?:\\.\\d+)?)[\\s]*%/g);
                for (const match of percentMatches) {
                    percentages.push(match[0]);
                }
                data.percentages = percentages.slice(0, 20); // First 20 percentages
                
                return data;
            }
        """)
        
        return content
    
    def _extract_general_content(self, page):
        """Extract general page content"""
        return {
            'text': page.evaluate("() => document.body.innerText"),
            'title': page.title(),
            'headers': page.evaluate("""
                () => {
                    const headers = [];
                    document.querySelectorAll('h1, h2, h3').forEach(h => {
                        headers.push(h.innerText);
                    });
                    return headers;
                }
            """)
        }
    
    def analyze_with_ai(self, parsed_content, model_id="anthropic/claude-3.5-sonnet"):
        """Send parsed content to AI for analysis"""
        OPEN_ROUTER_API_KEY = "OPENROUTER_API_KEY_REMOVED"
        
        # Prepare content summary for AI
        content_summary = f"Website: {self.base_url}\n\n"
        
        for url, data in parsed_content.items():
            content_summary += f"\n{'='*60}\n"
            content_summary += f"Page Type: {data['type'].upper()}\n"
            content_summary += f"URL: {url}\n"
            content_summary += f"Priority: {data.get('priority', 'unknown')}\n\n"
            
            if 'error' in data:
                content_summary += f"Error loading page: {data['error']}\n"
            else:
                content = data.get('content', {})
                text = content.get('text', '')[:2000]  # First 2000 chars
                content_summary += f"Content Preview:\n{text}\n"
                
                if data['type'] == 'team' and 'linkedin_profiles' in content:
                    content_summary += f"\nLinkedIn Profiles Found: {len(content['linkedin_profiles'])}\n"
                    for profile in content['linkedin_profiles'][:5]:
                        content_summary += f"  • {profile['url']}\n"
        
        prompt = f"""Analyze this crypto project based on the multiple pages parsed from their website:

{content_summary}

Provide a comprehensive analysis including:
1. Overall legitimacy score (1-10)
2. Team assessment based on all information found
3. Technical depth based on documentation
4. Red flags or concerns
5. Positive indicators

Format as JSON with score, tier, team_assessment, technical_assessment, red_flags, positive_indicators, and overall_reasoning."""
        
        # Call AI model
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {OPEN_ROUTER_API_KEY}',
                },
                json={
                    'model': model_id,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.1,
                    'max_tokens': 1500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code}"
                
        except Exception as e:
            return f"Error: {e}"


def main():
    print("\n" + "="*80)
    print("INTELLIGENT TWO-STAGE WEBSITE PARSER")
    print("="*80)
    
    # Test with TRWA
    url = "https://tharwa.finance/"
    
    parser = IntelligentWebsiteParser(url)
    
    # Stage 1: Discover structure
    discovered = parser.stage1_discover_structure()
    
    # Let user see what was found
    print(f"\n📋 Summary:")
    print(f"  • Total pages discovered: {len(discovered)}")
    print(f"  • High priority pages: {sum(1 for p in discovered.values() if p['priority'] == 'high')}")
    print(f"  • Medium priority pages: {sum(1 for p in discovered.values() if p['priority'] == 'medium')}")
    
    # Stage 2: Deep parse important pages
    parsed_content = parser.stage2_deep_parse(max_pages=5)
    
    # Stage 3: Analyze with AI
    print("\n🤖 Analyzing with AI...")
    analysis = parser.analyze_with_ai(parsed_content)
    print("\nAI Analysis:")
    print(analysis[:1000])  # First 1000 chars
    
    # Save results
    output = {
        'website': url,
        'discovered_pages': discovered,
        'parsed_pages': list(parsed_content.keys()),
        'page_count': {
            'total': len(discovered),
            'parsed': len(parsed_content)
        },
        'timestamp': datetime.now().isoformat()
    }
    
    with open('intelligent_parse_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\n📁 Results saved to intelligent_parse_results.json")

if __name__ == "__main__":
    main()
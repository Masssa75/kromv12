#!/usr/bin/env python3
"""
Comprehensive Website Analysis System
- Intelligent two-stage parsing
- Team extraction focus
- Document discovery
- Batch processing with database storage
"""
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import json
import sqlite3
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin
import re
import traceback

class ComprehensiveWebsiteAnalyzer:
    def __init__(self, db_path="website_analysis_new.db"):
        self.db_path = db_path
        self.api_key = "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"
        
    def parse_website_with_playwright(self, url):
        """Stage 1: Parse website with JavaScript rendering and extract all content"""
        print(f"\n🌐 Parsing {url} with Playwright...")
        
        result = {
            'url': url,
            'success': False,
            'content': {},
            'documents': [],
            'team_data': {},
            'navigation': {
                'all_links': [],
                'parsed_sections': [],
                'external_links': []
            },
            'error': None
        }
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Navigate to page
                page.goto(url, wait_until='networkidle', timeout=20000)
                page.wait_for_timeout(3000)
                
                # Extract main content
                result['content']['title'] = page.title()
                result['content']['text'] = page.evaluate("() => document.body.innerText")
                result['content']['html'] = page.content()
                
                # Extract all navigation links first
                all_links = page.evaluate("""
                    () => {
                        const links = [];
                        const seen = new Set();
                        
                        document.querySelectorAll('a[href]').forEach(link => {
                            const href = link.href;
                            const text = (link.innerText || '').trim();
                            
                            if (!seen.has(href) && text) {
                                seen.add(href);
                                
                                // Categorize the link
                                const isExternal = !href.includes(window.location.hostname);
                                const isAnchor = href.includes('#');
                                const isPDF = href.includes('.pdf');
                                const isDoc = href.includes('docs') || href.includes('documentation');
                                const isTeam = text.toLowerCase().includes('team') || text.toLowerCase().includes('about');
                                const isWhitepaper = text.toLowerCase().includes('whitepaper') || text.toLowerCase().includes('litepaper');
                                
                                links.push({
                                    url: href,
                                    text: text.substring(0, 50),
                                    type: isPDF ? 'pdf' : isDoc ? 'docs' : isTeam ? 'team' : isWhitepaper ? 'whitepaper' : isAnchor ? 'anchor' : isExternal ? 'external' : 'internal',
                                    external: isExternal,
                                    priority: (isWhitepaper || isDoc || isTeam) ? 'high' : isPDF ? 'medium' : 'low'
                                });
                            }
                        });
                        
                        return links;
                    }
                """)
                
                result['navigation']['all_links'] = all_links
                
                # Track which sections we actually parsed
                parsed_sections = []
                
                # Extract team information specifically
                team_data = page.evaluate("""
                    () => {
                        const team = {
                            members: [],
                            linkedin_profiles: [],
                            sections_found: []
                        };
                        
                        // Look for team sections
                        const teamSelectors = [
                            '[class*="team"]', '[id*="team"]',
                            '[class*="founder"]', '[class*="leadership"]',
                            '[class*="about"]', '[id*="about"]',
                            'section:has(h1:contains("team"))',
                            'section:has(h2:contains("team"))'
                        ];
                        
                        teamSelectors.forEach(selector => {
                            try {
                                const elements = document.querySelectorAll(selector);
                                elements.forEach(elem => {
                                    const text = elem.innerText || '';
                                    if (text.length > 50 && text.length < 5000) {
                                        team.sections_found.push(text);
                                    }
                                });
                            } catch(e) {}
                        });
                        
                        // Look for LinkedIn profiles
                        document.querySelectorAll('a[href*="linkedin.com/in/"]').forEach(link => {
                            const href = link.href;
                            const text = link.innerText || '';
                            const parent = link.closest('[class*="member"], [class*="team"], div');
                            const context = parent ? parent.innerText : '';
                            
                            team.linkedin_profiles.push({
                                url: href,
                                link_text: text,
                                context: context.substring(0, 200)
                            });
                        });
                        
                        return team;
                    }
                """)
                
                result['team_data'] = team_data
                
                # Mark team sections as parsed
                if team_data['sections_found']:
                    parsed_sections.append({'type': 'team', 'content': 'Team section with member information'})
                
                # Find all documents (PDFs, whitepapers, docs)
                documents = page.evaluate("""
                    () => {
                        const docs = [];
                        const seen = new Set();
                        
                        document.querySelectorAll('a[href]').forEach(link => {
                            const href = link.href;
                            const text = (link.innerText || '').trim();
                            
                            // Skip if already seen
                            if (seen.has(href)) return;
                            
                            const isDoc = 
                                href.includes('.pdf') ||
                                href.includes('whitepaper') ||
                                href.includes('litepaper') ||
                                href.includes('docs.') ||
                                href.includes('gitbook') ||
                                href.includes('github.com') ||
                                text.toLowerCase().includes('whitepaper') ||
                                text.toLowerCase().includes('documentation');
                            
                            if (isDoc) {
                                seen.add(href);
                                docs.push({
                                    url: href,
                                    text: text || 'Document',
                                    type: href.includes('.pdf') ? 'pdf' : 
                                          href.includes('github') ? 'github' :
                                          href.includes('gitbook') ? 'gitbook' : 
                                          'docs'
                                });
                            }
                        });
                        
                        return docs;
                    }
                """)
                
                result['documents'] = documents
                
                # Mark documents as identified for parsing
                for doc in documents:
                    parsed_sections.append({'type': 'document', 'content': f"{doc['type']}: {doc['text']}"})
                
                # Get all headings for structure
                headings = page.evaluate("""
                    () => {
                        const headings = [];
                        document.querySelectorAll('h1, h2, h3').forEach(h => {
                            headings.push({
                                level: h.tagName,
                                text: h.innerText
                            });
                        });
                        return headings;
                    }
                """)
                
                result['content']['headings'] = headings
                
                # Count images
                result['content']['image_count'] = page.evaluate("() => document.querySelectorAll('img').length")
                
                # Get social links
                social_links = page.evaluate("""
                    () => {
                        const social = [];
                        const platforms = ['twitter', 'telegram', 'discord', 'github', 'medium', 'linkedin', 'reddit', 'youtube'];
                        
                        document.querySelectorAll('a[href]').forEach(link => {
                            const href = link.href.toLowerCase();
                            for (const platform of platforms) {
                                if (href.includes(platform)) {
                                    social.push({
                                        platform: platform,
                                        url: link.href,
                                        text: link.innerText || ''
                                    });
                                    break;
                                }
                            }
                        });
                        
                        return social;
                    }
                """)
                
                result['content']['social_links'] = social_links
                
                # Mark main page as parsed
                parsed_sections.insert(0, {'type': 'main', 'content': f"Main page ({len(result['content'].get('text', ''))} chars)"})
                
                # Add social links as parsed
                if social_links:
                    parsed_sections.append({'type': 'social', 'content': f"{len(social_links)} social media links"})
                
                result['navigation']['parsed_sections'] = parsed_sections
                
                # Mark which links were actually parsed
                for link in all_links:
                    link_text = (link.get('text', '') or '').lower()
                    link_url = (link.get('url', '') or '').lower()
                    
                    # Main page content is always parsed
                    if link.get('type') == 'internal':
                        link['parsed'] = True
                    # Team sections were parsed
                    elif link.get('type') == 'team' or 'about' in link_text:
                        link['parsed'] = True
                    # Documentation links that were identified as documents
                    elif 'documentation' in link_text or 'docs' in link_text or 'gitbook' in link_url:
                        # Check if this was in our documents list
                        link['parsed'] = any(doc['url'] == link.get('url') for doc in documents)
                    # GitHub links were parsed
                    elif 'github' in link_text or 'github.com' in link_url:
                        link['parsed'] = any(doc['url'] == link.get('url') for doc in documents)
                    # Social links that were extracted
                    elif any(social in link_url for social in ['twitter.com', 'x.com', 'telegram', 'discord', 'linkedin.com', 'medium.com']):
                        link['parsed'] = any(social['url'] == link.get('url') for social in social_links)
                    else:
                        link['parsed'] = False
                
                # Separate external links
                result['navigation']['external_links'] = [link for link in all_links if link.get('external')]
                
                browser.close()
                result['success'] = True
                
                print(f"  ✅ Extracted {len(result['content'].get('text', ''))} chars")
                print(f"  📄 Found {len(result['documents'])} documents")
                print(f"  👥 Found {len(result['team_data'].get('linkedin_profiles', []))} LinkedIn profiles")
                print(f"  🔗 Found {len(all_links)} total links ({len([l for l in all_links if l.get('priority') == 'high'])} high priority)")
                
        except Exception as e:
            result['error'] = str(e)
            print(f"  ❌ Error: {e}")
            
        return result
    
    def extract_team_names_from_content(self, parsed_data):
        """Stage 2: Extract specific team member names from parsed content"""
        team_members = []
        content = parsed_data.get('content', {}).get('text', '')
        team_sections = parsed_data.get('team_data', {}).get('sections_found', [])
        
        # Combine all team-related content
        all_team_content = content + '\n'.join(team_sections)
        
        # Pattern for finding names near titles
        exec_patterns = [
            r'([A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+)\s*[,-]?\s*(?:CEO|Chief Executive)',
            r'([A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+)\s*[,-]?\s*(?:CTO|Chief Technology)',
            r'([A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+)\s*[,-]?\s*(?:CFO|Chief Financial)',
            r'([A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+)\s*[,-]?\s*(?:COO|Chief Operating)',
            r'([A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+)\s*[,-]?\s*(?:CMO|Chief Marketing)',
            r'([A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+)\s*[,-]?\s*(?:Founder|Co-founder)',
            r'([A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+)\s*[,-]?\s*(?:Head of|Director of)',
            r'([A-Z][a-z]+ (?:[A-Z]\. )?[A-Z][a-z]+)\s*[,-]?\s*(?:Advisor|Strategic)',
        ]
        
        found_names = set()
        for pattern in exec_patterns:
            matches = re.findall(pattern, all_team_content)
            for match in matches:
                if match and len(match) > 3:  # Filter out initials
                    found_names.add(match)
        
        # Match LinkedIn profiles to names if possible
        linkedin_profiles = parsed_data.get('team_data', {}).get('linkedin_profiles', [])
        for profile in linkedin_profiles:
            # Try to extract name from LinkedIn URL
            url = profile.get('url', '')
            match = re.search(r'linkedin\.com/in/([^/]+)', url)
            if match:
                linkedin_id = match.group(1)
                # Convert LinkedIn ID to potential name (e.g., john-doe -> John Doe)
                potential_name = linkedin_id.replace('-', ' ').title()
                
                # Check if this name appears in context
                context = profile.get('context', '')
                for name in found_names:
                    if name.lower() in context.lower():
                        team_members.append({
                            'name': name,
                            'linkedin': url,
                            'context': context[:100]
                        })
                        break
                else:
                    # Add based on LinkedIn alone if it looks like a name
                    if ' ' in potential_name and not any(c.isdigit() for c in potential_name):
                        team_members.append({
                            'name': potential_name,
                            'linkedin': url,
                            'context': context[:100]
                        })
        
        return team_members
    
    def analyze_with_models(self, parsed_data, models_to_test=None):
        """Stage 3: Analyze with multiple AI models"""
        if models_to_test is None:
            models_to_test = [
                ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet"),
                ("openai/gpt-4o", "GPT-4o"),
                ("google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash"),
                ("moonshotai/kimi-k2", "Kimi K2"),
            ]
        
        results = []
        
        for model_id, model_name in models_to_test:
            print(f"\n🤖 Analyzing with {model_name}...")
            
            prompt = self.create_analysis_prompt(parsed_data)
            
            try:
                response = requests.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self.api_key}',
                    },
                    json={
                        'model': model_id,
                        'messages': [{'role': 'user', 'content': prompt}],
                        'temperature': 0.1,
                        'max_tokens': 2000
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    
                    # Parse JSON from response
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        analysis = json.loads(json_match.group(0))
                        results.append({
                            'model': model_name,
                            'analysis': analysis
                        })
                        print(f"  ✅ Score: {analysis.get('score')}/10")
                        print(f"  👥 Team members found: {len(analysis.get('team_members', []))}")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            time.sleep(2)  # Rate limiting
        
        return results
    
    def create_analysis_prompt(self, parsed_data):
        """Create comprehensive prompt for AI analysis"""
        content = parsed_data.get('content', {})
        team_data = parsed_data.get('team_data', {})
        documents = parsed_data.get('documents', [])
        
        prompt = f"""Analyze this crypto project website based on fully rendered content (JavaScript executed):

WEBSITE: {parsed_data.get('url')}
TITLE: {content.get('title')}

MAIN CONTENT ({len(content.get('text', ''))} characters):
{content.get('text', '')[:3000]}

TEAM INFORMATION FOUND:
- LinkedIn profiles discovered: {len(team_data.get('linkedin_profiles', []))}
- Team sections found: {len(team_data.get('sections_found', []))}

LINKEDIN PROFILES:"""
        
        for profile in team_data.get('linkedin_profiles', [])[:10]:
            prompt += f"\n- {profile.get('url')}"
            if profile.get('context'):
                prompt += f" (Context: {profile.get('context', '')[:50]})"
        
        prompt += f"""

DOCUMENTS AVAILABLE ({len(documents)} total):"""
        for doc in documents[:10]:
            prompt += f"\n- [{doc.get('type', 'unknown').upper()}] {doc.get('text')}: {doc.get('url')[:60]}"
        
        prompt += f"""

SOCIAL LINKS:"""
        for social in content.get('social_links', [])[:10]:
            prompt += f"\n- {social.get('platform')}: {social.get('url')}"
        
        prompt += """

STAGE 1 ASSESSMENT - Quick Website Triage (1-3 scale per category)

This is a RAPID assessment based ONLY on what's visible on the website. We're looking for signals that justify deeper investigation.

EVALUATION CRITERIA (1-3 scale each):

1. TECHNICAL INFRASTRUCTURE (1-3):
   - 1: No technical information visible
   - 2: Basic technical mentions or architecture overview
   - 3: GitHub/GitLab links present OR major tech partnership mentioned (AWS, Google Cloud, etc.)

2. BUSINESS & UTILITY (1-3):
   - 1: Vague or unclear use case
   - 2: Clear use case and value proposition explained
   - 3: Clear use case PLUS notable backers/partners mentioned (e.g., "Backed by Coinbase", "Partnership with Microsoft")

3. DOCUMENTATION (1-3):
   - 1: No documentation links
   - 2: Whitepaper or docs link visible
   - 3: Comprehensive documentation portal or multiple doc resources linked

4. COMMUNITY & SOCIAL (1-3):
   - 1: No social media links
   - 2: Social media links present (Twitter, Discord, Telegram)
   - 3: Active community metrics shown OR notable endorsements/media coverage mentioned

5. SECURITY & TRUST (1-3):
   - 1: No security information
   - 2: Basic security mentions or safety claims
   - 3: Audit reports linked OR major security partner mentioned (CertiK, OpenZeppelin, etc.)

6. TEAM TRANSPARENCY (1-3):
   - 1: Completely anonymous
   - 2: Some team information or company details
   - 3: Full team with LinkedIn profiles OR notable founders mentioned (e.g., "Founded by ex-Apple engineers")

7. WEBSITE QUALITY (1-3):
   - 1: Basic or unprofessional
   - 2: Professional and well-organized
   - 3: Exceptional quality with interactive features or outstanding design

IMPORTANT: A single exceptional signal (like backing from Apple or Google) should immediately give a 3 in that category. We're looking for reasons to investigate deeper, not doing deep analysis yet.

STAGE 2 THRESHOLD: Projects scoring 10+ total points (out of 21) warrant deeper investigation.

Provide your analysis as JSON:
{
  "total_score": (sum of all 7 categories, max 21),
  "proceed_to_stage_2": (true if total_score >= 10, false otherwise),
  "tier": "HIGH/MEDIUM/LOW" (HIGH: 15-21, MEDIUM: 10-14, LOW: 1-9),
  "category_scores": {
    "technical_infrastructure": (1-3),
    "business_utility": (1-3),
    "documentation_quality": (1-3),
    "community_social": (1-3),
    "security_trust": (1-3),
    "team_transparency": (1-3),
    "website_presentation": (1-3)
  },
  "stage_2_links": [
    "List URLs that should be deep-parsed in Stage 2",
    "e.g., GitHub repo, whitepaper PDF, documentation site",
    "Only include if proceed_to_stage_2 is true"
  ],
  "exceptional_signals": ["list any exceptional findings that warranted a 3 score"],
  "missing_elements": ["list key missing elements that kept scores at 1"],
  "quick_assessment": "1-2 sentences on whether this warrants deeper investigation"
}

Return ONLY the JSON, no other text."""
        
        return prompt
    
    def save_to_database(self, url, parsed_data, ai_analyses):
        """Save results to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ensure table exists with all columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS website_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                url TEXT,
                parsed_content TEXT,
                documents_found INTEGER,
                team_members_found INTEGER,
                linkedin_profiles INTEGER,
                website_description TEXT,
                score REAL,
                tier TEXT,
                legitimacy_indicators TEXT,
                red_flags TEXT,
                technical_depth TEXT,
                team_transparency TEXT,
                reasoning TEXT,
                analyzed_at TIMESTAMP,
                parse_success BOOLEAN,
                parse_error TEXT
            )
        """)
        
        # Extract ticker from parsed_data
        ticker = parsed_data.get('ticker', 'N/A')
        
        # Calculate averages from AI analyses
        if ai_analyses:
            scores = [a['analysis'].get('score', 0) for a in ai_analyses]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Get consensus tier
            tiers = [a['analysis'].get('tier', '') for a in ai_analyses]
            tier = max(set(tiers), key=tiers.count) if tiers else 'UNKNOWN'
            
            # Combine team members from all models
            all_team_members = []
            for analysis in ai_analyses:
                all_team_members.extend(analysis['analysis'].get('team_members', []))
            
            # Combine indicators and flags
            all_indicators = []
            all_flags = []
            for analysis in ai_analyses:
                all_indicators.extend(analysis['analysis'].get('legitimacy_indicators', []))
                all_flags.extend(analysis['analysis'].get('red_flags', []))
            
            # Get first model's detailed assessments
            first_analysis = ai_analyses[0]['analysis'] if ai_analyses else {}
            
            # Extract category scores
            category_scores = first_analysis.get('category_scores', {})
            
            cursor.execute("""
                INSERT OR REPLACE INTO website_analysis 
                (ticker, url, parsed_content, documents_found, team_members_found, 
                 linkedin_profiles, score, tier, legitimacy_indicators, 
                 red_flags, technical_depth, team_transparency, business_utility,
                 community_strength, security_measures, reasoning, 
                 analyzed_at, parse_success, parse_error,
                 score_technical_infrastructure, score_business_utility,
                 score_documentation_quality, score_community_social,
                 score_security_trust, score_team_transparency,
                 score_website_presentation, category_scores,
                 total_score, proceed_to_stage_2, exceptional_signals,
                 missing_elements, quick_assessment, stage_2_links)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker,
                url,
                json.dumps(parsed_data),
                len(parsed_data.get('documents', [])),
                len(all_team_members),
                len(parsed_data.get('team_data', {}).get('linkedin_profiles', [])),
                avg_score,
                tier,
                json.dumps(list(set(all_indicators))),
                json.dumps(list(set(all_flags))),
                first_analysis.get('technical_depth', ''),
                first_analysis.get('team_transparency', ''),
                first_analysis.get('business_utility', ''),
                first_analysis.get('community_strength', ''),
                first_analysis.get('security_measures', ''),
                first_analysis.get('reasoning', ''),
                datetime.now().isoformat(),
                parsed_data.get('success', False),
                parsed_data.get('error', ''),
                category_scores.get('technical_infrastructure', 0),
                category_scores.get('business_utility', 0),
                category_scores.get('documentation_quality', 0),
                category_scores.get('community_social', 0),
                category_scores.get('security_trust', 0),
                category_scores.get('team_transparency', 0),
                category_scores.get('website_presentation', 0),
                json.dumps(category_scores),
                first_analysis.get('total_score', sum(category_scores.values())),
                first_analysis.get('proceed_to_stage_2', sum(category_scores.values()) >= 10),
                json.dumps(first_analysis.get('exceptional_signals', [])),
                json.dumps(first_analysis.get('missing_elements', [])),
                first_analysis.get('quick_assessment', ''),
                json.dumps(first_analysis.get('stage_2_links', []))
            ))
        
        conn.commit()
        conn.close()
        print(f"\n💾 Saved to database")
    
    def analyze_single_website(self, url):
        """Complete analysis pipeline for a single website"""
        print(f"\n{'='*60}")
        print(f"Analyzing: {url}")
        print(f"{'='*60}")
        
        # Stage 1: Parse website
        parsed_data = self.parse_website_with_playwright(url)
        
        if not parsed_data['success']:
            print(f"❌ Failed to parse website: {parsed_data.get('error')}")
            self.save_to_database(url, parsed_data, [])
            return None
        
        # Stage 2: Extract team names
        team_members = self.extract_team_names_from_content(parsed_data)
        parsed_data['extracted_team_members'] = team_members
        
        # Stage 3: Analyze with AI models
        ai_analyses = self.analyze_with_models(parsed_data)
        
        # Stage 4: Save to database
        self.save_to_database(url, parsed_data, ai_analyses)
        
        return {
            'url': url,
            'parsed_data': parsed_data,
            'ai_analyses': ai_analyses
        }
    
    def batch_analyze(self, limit=5):
        """Analyze multiple websites from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get unanalyzed websites
        cursor.execute("""
            SELECT DISTINCT website_url 
            FROM tokens 
            WHERE website_url IS NOT NULL 
            AND website_url != ''
            AND website_url NOT IN (
                SELECT url FROM website_analysis WHERE parse_success = 1
            )
            LIMIT ?
        """, (limit,))
        
        websites = cursor.fetchall()
        conn.close()
        
        print(f"\n🚀 Starting batch analysis of {len(websites)} websites")
        
        results = []
        for i, (url,) in enumerate(websites, 1):
            print(f"\n[{i}/{len(websites)}] Processing {url}")
            result = self.analyze_single_website(url)
            if result:
                results.append(result)
            time.sleep(3)  # Be nice to servers
        
        return results


def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE WEBSITE ANALYSIS SYSTEM")
    print("="*80)
    
    analyzer = ComprehensiveWebsiteAnalyzer()
    
    # Test with a single website first
    test_url = "https://tharwa.finance/"
    
    print("\n1️⃣ Testing single website analysis...")
    result = analyzer.analyze_single_website(test_url)
    
    if result:
        print("\n📊 Analysis Summary:")
        print(f"  Documents found: {len(result['parsed_data'].get('documents', []))}")
        print(f"  Team data: {len(result['parsed_data'].get('team_data', {}).get('linkedin_profiles', []))} LinkedIn profiles")
        
        if result['ai_analyses']:
            print("\n  AI Scores:")
            for analysis in result['ai_analyses']:
                score = analysis['analysis'].get('score', 'N/A')
                team_count = len(analysis['analysis'].get('team_members', []))
                print(f"    • {analysis['model']}: {score}/10 ({team_count} team members)")
    
    # Ask if user wants to run batch
    print("\n" + "="*80)
    print("Ready to run batch analysis?")
    print("This will analyze up to 5 unprocessed websites from the database")
    print("Press Enter to continue or Ctrl+C to exit...")
    try:
        input()
        
        print("\n2️⃣ Running batch analysis...")
        batch_results = analyzer.batch_analyze(limit=5)
        
        print(f"\n✅ Completed batch analysis of {len(batch_results)} websites")
        
    except KeyboardInterrupt:
        print("\n⏹️ Batch analysis cancelled")
    
    print("\n📁 All results saved to website_analysis_new.db")
    print("Use results_viewer.html to view the analysis results")

if __name__ == "__main__":
    main()
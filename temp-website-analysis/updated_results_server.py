#!/usr/bin/env python3
"""
Updated results viewer - List view with modal showing meters
Runs on port 5005
"""
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Website Analysis Results - Stage 1</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
            text-align: center;
        }
        
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        /* List View Styles */
        .results-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .result-item {
            display: flex;
            align-items: center;
            padding: 15px 20px;
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .result-item:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
            transform: translateX(5px);
        }
        
        .ticker-circle {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 16px;
            margin-right: 15px;
        }
        
        .item-info {
            flex: 1;
        }
        
        .item-ticker {
            font-weight: 600;
            font-size: 16px;
            color: #333;
        }
        
        .item-url {
            font-size: 12px;
            color: #9ca3af;
            margin-top: 2px;
        }
        
        .item-score {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            margin-right: 15px;
        }
        
        .item-tier {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .tier-high { background: #10b981; color: white; }
        .tier-medium { background: #f59e0b; color: white; }
        .tier-low { background: #ef4444; color: white; }
        
        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(5px);
        }
        
        .modal-content {
            position: relative;
            background-color: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 20px;
            width: 90%;
            max-width: 700px;
            max-height: 85vh;
            overflow-y: auto;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateY(-50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .close {
            position: absolute;
            right: 20px;
            top: 20px;
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover { color: #000; }
        
        /* Modal Header */
        .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e5e7eb;
        }
        
        .modal-ticker {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .modal-ticker-circle {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 20px;
        }
        
        .modal-ticker-info h2 {
            font-size: 24px;
            color: #333;
            margin-bottom: 4px;
        }
        
        .modal-score-display {
            text-align: center;
        }
        
        .modal-score {
            font-size: 48px;
            font-weight: bold;
            color: #667eea;
        }
        
        .modal-tier {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            margin-top: 8px;
            display: inline-block;
        }
        
        /* Stage 2 Decision */
        .stage2-decision {
            padding: 15px;
            border-radius: 12px;
            margin: 20px 0;
            text-align: center;
            font-weight: bold;
            font-size: 16px;
        }
        
        .proceed-yes {
            background: #10b98120;
            color: #059669;
            border: 2px solid #10b981;
        }
        
        .proceed-no {
            background: #ef444420;
            color: #dc2626;
            border: 2px solid #ef4444;
        }
        
        /* Category Meters */
        .meters-section {
            margin: 25px 0;
        }
        
        .meters-title {
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
        }
        
        .meter-item {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .meter-label {
            flex: 0 0 140px;
            font-size: 13px;
            color: #666;
            text-align: right;
            padding-right: 15px;
        }
        
        .meter-bar {
            flex: 1;
            height: 24px;
            background: #f3f4f6;
            border-radius: 12px;
            position: relative;
            overflow: hidden;
        }
        
        .meter-fill {
            height: 100%;
            border-radius: 12px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            color: white;
            font-size: 12px;
            font-weight: bold;
            transition: width 0.5s ease;
        }
        
        .meter-fill-0 { width: 0%; background: #e5e7eb; }
        .meter-fill-1 { width: 33.33%; background: linear-gradient(90deg, #ef4444, #f87171); }
        .meter-fill-2 { width: 66.66%; background: linear-gradient(90deg, #f59e0b, #fbbf24); }
        .meter-fill-3 { width: 100%; background: linear-gradient(90deg, #10b981, #34d399); }
        
        /* Navigation Analysis Section */
        .nav-section {
            margin: 25px 0;
            padding: 20px;
            background: #f9fafb;
            border-radius: 12px;
        }
        
        .nav-title {
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
        }
        
        .nav-subtitle {
            font-size: 13px;
            color: #666;
            margin-bottom: 15px;
        }
        
        .links-grid {
            display: grid;
            gap: 8px;
        }
        
        .link-item {
            display: flex;
            align-items: center;
            padding: 8px 12px;
            background: white;
            border-radius: 8px;
            font-size: 13px;
        }
        
        .link-type {
            font-weight: 600;
            color: #666;
            margin-right: 10px;
            text-transform: uppercase;
            font-size: 11px;
        }
        
        .link-text {
            flex: 1;
            color: #333;
        }
        
        .link-status {
            margin-left: 10px;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 12px;
        }
        
        .status-parsed {
            background: #10b98120;
            color: #059669;
        }
        
        .status-stage2 {
            background: #3b82f620;
            color: #2563eb;
            font-weight: bold;
        }
        
        /* Signals Section */
        .signals-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }
        
        .signal-box {
            padding: 15px;
            border-radius: 10px;
        }
        
        .exceptional-box {
            background: #f0fdf4;
            border: 1px solid #10b981;
        }
        
        .missing-box {
            background: #fef2f2;
            border: 1px solid #ef4444;
        }
        
        .signal-title {
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 8px;
            text-transform: uppercase;
        }
        
        .exceptional-box .signal-title { color: #059669; }
        .missing-box .signal-title { color: #dc2626; }
        
        .signal-list {
            list-style: none;
            font-size: 12px;
        }
        
        .exceptional-box .signal-list { color: #047857; }
        .missing-box .signal-list { color: #b91c1c; }
        
        /* Assessment Box */
        .assessment-box {
            margin: 20px 0;
            padding: 15px;
            background: #f9fafb;
            border-radius: 10px;
            font-size: 14px;
            color: #4b5563;
            font-style: italic;
            line-height: 1.6;
        }
        
        .modal-url {
            display: block;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e5e7eb;
            color: #667eea;
            text-decoration: none;
            font-size: 13px;
            text-align: center;
        }
        
        .modal-url:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Website Analysis Results</h1>
        <p class="subtitle">Stage 1 Assessment - Quick triage to identify projects worth deeper investigation</p>
        
        <div id="results" class="results-list">
            <div style="text-align: center; color: #999; padding: 20px;">Loading results...</div>
        </div>
    </div>
    
    <!-- Modal -->
    <div id="detailModal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <div id="modalBody"></div>
        </div>
    </div>
    
    <script>
        const categoryLabels = {
            'technical_infrastructure': 'Technical Infrastructure',
            'business_utility': 'Business & Utility',
            'documentation_quality': 'Documentation',
            'community_social': 'Community & Social',
            'security_trust': 'Security & Trust',
            'team_transparency': 'Team Transparency',
            'website_presentation': 'Website Presentation'
        };
        
        let allResults = [];
        
        async function loadResults() {
            try {
                const response = await fetch('/api/results');
                const data = await response.json();
                allResults = data.results;
                displayResults();
            } catch (error) {
                document.getElementById('results').innerHTML = 
                    `<div style="color: red; text-align: center;">Error loading results: ${error.message}</div>`;
            }
        }
        
        function displayResults() {
            const resultsDiv = document.getElementById('results');
            
            if (allResults.length === 0) {
                resultsDiv.innerHTML = '<div style="text-align: center; color: #999; padding: 20px;">No results found</div>';
                return;
            }
            
            resultsDiv.innerHTML = allResults.map((result, index) => {
                const ticker = result.ticker || 'N/A';
                const totalScore = result.total_score || 0;
                const tier = result.tier || 'LOW';
                
                return `
                    <div class="result-item" onclick="showModal(${index})">
                        <div class="ticker-circle">${ticker.substring(0, 2).toUpperCase()}</div>
                        <div class="item-info">
                            <div class="item-ticker">${ticker}</div>
                            <div class="item-url">${result.url}</div>
                        </div>
                        <div class="item-score">${totalScore}/21</div>
                        <div class="item-tier tier-${tier.toLowerCase()}">${tier}</div>
                    </div>
                `;
            }).join('');
        }
        
        function showModal(index) {
            const result = allResults[index];
            const modal = document.getElementById('detailModal');
            const modalBody = document.getElementById('modalBody');
            
            const ticker = result.ticker || 'N/A';
            const totalScore = result.total_score || 0;
            const tier = result.tier || 'LOW';
            const proceedToStage2 = result.proceed_to_stage_2 || false;
            const scores = result.category_scores || {};
            
            // Build meters HTML
            let metersHtml = '';
            for (const [key, value] of Object.entries(scores)) {
                const label = categoryLabels[key] || key;
                const score = value || 0;
                metersHtml += `
                    <div class="meter-item">
                        <div class="meter-label">${label}</div>
                        <div class="meter-bar">
                            <div class="meter-fill meter-fill-${score}">
                                ${score}/3
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Build navigation analysis HTML
            let navHtml = '';
            if (result.parsed_links) {
                const links = JSON.parse(result.parsed_links);
                const stage2Links = result.stage_2_links ? JSON.parse(result.stage_2_links) : [];
                
                navHtml = `
                    <div class="nav-section">
                        <div class="nav-title">🔍 Navigation Analysis</div>
                        <div class="nav-subtitle">Found ${links.length} links (${result.high_priority_count || 0} high priority)</div>
                        <div class="links-grid">
                            ${links.map(link => {
                                const isStage2 = stage2Links.includes(link.url);
                                const isParsed = link.parsed === 'true' || link.parsed === true;
                                return `
                                    <div class="link-item">
                                        <span class="link-type">${link.type}</span>
                                        <span class="link-text">${link.text}</span>
                                        ${isStage2 ? '<span class="link-status status-stage2">STAGE 2</span>' : 
                                          isParsed ? '<span class="link-status status-parsed">parsed</span>' : ''}
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;
            }
            
            // Build signals HTML
            let signalsHtml = '';
            const exceptional = result.exceptional_signals || [];
            const missing = result.missing_elements || [];
            
            if (exceptional.length > 0 || missing.length > 0) {
                signalsHtml = '<div class="signals-section">';
                
                if (exceptional.length > 0) {
                    signalsHtml += `
                        <div class="signal-box exceptional-box">
                            <div class="signal-title">✨ Exceptional Signals</div>
                            <ul class="signal-list">
                                ${exceptional.map(s => `<li>• ${s}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
                
                if (missing.length > 0) {
                    signalsHtml += `
                        <div class="signal-box missing-box">
                            <div class="signal-title">⚠️ Missing Elements</div>
                            <ul class="signal-list">
                                ${missing.map(s => `<li>• ${s}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
                
                signalsHtml += '</div>';
            }
            
            modalBody.innerHTML = `
                <div class="modal-header">
                    <div class="modal-ticker">
                        <div class="modal-ticker-circle">${ticker.substring(0, 2).toUpperCase()}</div>
                        <div class="modal-ticker-info">
                            <h2>${ticker}</h2>
                        </div>
                    </div>
                    <div class="modal-score-display">
                        <div class="modal-score">${totalScore}/21</div>
                        <div class="modal-tier tier-${tier.toLowerCase()}">${tier}</div>
                    </div>
                </div>
                
                <div class="stage2-decision ${proceedToStage2 ? 'proceed-yes' : 'proceed-no'}">
                    ${proceedToStage2 ? '✅ Proceed to Stage 2' : '❌ Skip Stage 2'}
                </div>
                
                <div class="meters-section">
                    <div class="meters-title">📊 Category Scores</div>
                    ${metersHtml}
                </div>
                
                ${navHtml}
                ${signalsHtml}
                
                ${result.quick_assessment ? `
                    <div class="assessment-box">
                        ${result.quick_assessment}
                    </div>
                ` : ''}
                
                <a href="${result.url}" target="_blank" class="modal-url">🔗 ${result.url}</a>
            `;
            
            modal.style.display = 'block';
        }
        
        // Close modal
        document.querySelector('.close').onclick = function() {
            document.getElementById('detailModal').style.display = 'none';
        }
        
        window.onclick = function(event) {
            const modal = document.getElementById('detailModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
        
        // Load results on page load
        loadResults();
        
        // Refresh every 10 seconds
        setInterval(loadResults, 10000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/results')
def get_results():
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            url, ticker, score, tier,
            score_technical_infrastructure,
            score_business_utility,
            score_documentation_quality,
            score_community_social,
            score_security_trust,
            score_team_transparency,
            score_website_presentation,
            category_scores,
            total_score,
            proceed_to_stage_2,
            exceptional_signals,
            missing_elements,
            quick_assessment,
            stage_2_links,
            parsed_content,
            analyzed_at
        FROM website_analysis
        ORDER BY analyzed_at DESC
    """)
    
    results = []
    for row in cursor.fetchall():
        # Parse category scores
        category_scores_json = {}
        if row[11]:
            try:
                category_scores_json = json.loads(row[11])
            except:
                pass
        
        # Use individual score columns if available
        category_scores = {
            'technical_infrastructure': row[4] or category_scores_json.get('technical_infrastructure', 0),
            'business_utility': row[5] or category_scores_json.get('business_utility', 0),
            'documentation_quality': row[6] or category_scores_json.get('documentation_quality', 0),
            'community_social': row[7] or category_scores_json.get('community_social', 0),
            'security_trust': row[8] or category_scores_json.get('security_trust', 0),
            'team_transparency': row[9] or category_scores_json.get('team_transparency', 0),
            'website_presentation': row[10] or category_scores_json.get('website_presentation', 0),
        }
        
        # Parse parsed content to get links
        parsed_links = []
        high_priority_count = 0
        if row[18]:
            try:
                parsed_data = json.loads(row[18])
                links = parsed_data.get('links_found', [])
                for link in links:
                    if link.get('priority') == 'high':
                        high_priority_count += 1
                parsed_links = links
            except:
                pass
        
        # Calculate total score if not present
        total_score = row[12] if row[12] is not None else sum(category_scores.values())
        
        # Determine proceed_to_stage_2
        proceed = row[13] if row[13] is not None else (total_score >= 10)
        
        # Parse JSON fields
        exceptional_signals = []
        if row[14]:
            try:
                exceptional_signals = json.loads(row[14])
            except:
                pass
        
        missing_elements = []
        if row[15]:
            try:
                missing_elements = json.loads(row[15])
            except:
                pass
        
        stage_2_links = []
        if row[17]:
            try:
                stage_2_links = json.loads(row[17])
            except:
                pass
        
        # Determine tier
        if total_score >= 15:
            tier = 'HIGH'
        elif total_score >= 10:
            tier = 'MEDIUM'
        else:
            tier = 'LOW'
        
        results.append({
            'url': row[0],
            'ticker': row[1],
            'total_score': total_score,
            'tier': tier,
            'proceed_to_stage_2': proceed,
            'category_scores': category_scores,
            'exceptional_signals': exceptional_signals,
            'missing_elements': missing_elements,
            'quick_assessment': row[16],
            'stage_2_links': stage_2_links,
            'parsed_links': json.dumps(parsed_links),
            'high_priority_count': high_priority_count,
            'analyzed_at': row[19]
        })
    
    conn.close()
    
    return jsonify({
        'results': results,
        'count': len(results)
    })

if __name__ == '__main__':
    print("Starting Updated Results Server on http://localhost:5005")
    print("Features:")
    print("- List view of all analyzed websites")
    print("- Click any item to see detailed modal with:")
    print("  - Category score meters (1-3 scale)")
    print("  - Navigation analysis with Stage 2 links")
    print("  - Exceptional signals and missing elements")
    app.run(port=5005, debug=True)
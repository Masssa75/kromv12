#!/usr/bin/env python3
"""
Enhanced results viewer with visual meters for website analysis
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
    <title>Website Analysis Results - Stage 1 Triage</title>
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
            max-width: 1200px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 32px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .subtitle {
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 30px;
            font-size: 16px;
        }
        
        .results-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .result-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
        }
        
        .result-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }
        
        .ticker {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }
        
        .total-score {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        
        .tier-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            margin-left: 10px;
        }
        
        .tier-high { background: #10b981; color: white; }
        .tier-medium { background: #f59e0b; color: white; }
        .tier-low { background: #ef4444; color: white; }
        
        .proceed-indicator {
            margin: 10px 0;
            padding: 8px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            font-size: 14px;
        }
        
        .proceed-yes {
            background: #10b98120;
            color: #059669;
            border: 1px solid #10b981;
        }
        
        .proceed-no {
            background: #ef444420;
            color: #dc2626;
            border: 1px solid #ef4444;
        }
        
        .meters-container {
            display: grid;
            grid-template-columns: 1fr;
            gap: 8px;
            margin: 15px 0;
        }
        
        .meter-row {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .meter-label {
            flex: 0 0 140px;
            font-size: 11px;
            color: #666;
            text-align: right;
        }
        
        .meter-bar {
            flex: 1;
            height: 20px;
            background: #f3f4f6;
            border-radius: 10px;
            position: relative;
            overflow: hidden;
        }
        
        .meter-fill {
            height: 100%;
            border-radius: 10px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 11px;
            font-weight: bold;
        }
        
        .meter-fill-1 {
            width: 33.33%;
            background: linear-gradient(90deg, #ef4444, #f87171);
        }
        
        .meter-fill-2 {
            width: 66.66%;
            background: linear-gradient(90deg, #f59e0b, #fbbf24);
        }
        
        .meter-fill-3 {
            width: 100%;
            background: linear-gradient(90deg, #10b981, #34d399);
        }
        
        .exceptional-signals {
            margin-top: 15px;
            padding: 10px;
            background: #f0fdf4;
            border-left: 3px solid #10b981;
            border-radius: 5px;
        }
        
        .exceptional-signals h4 {
            color: #059669;
            font-size: 12px;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        
        .exceptional-signals ul {
            list-style: none;
            font-size: 12px;
            color: #047857;
        }
        
        .missing-elements {
            margin-top: 10px;
            padding: 10px;
            background: #fef2f2;
            border-left: 3px solid #ef4444;
            border-radius: 5px;
        }
        
        .missing-elements h4 {
            color: #dc2626;
            font-size: 12px;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        
        .missing-elements ul {
            list-style: none;
            font-size: 12px;
            color: #b91c1c;
        }
        
        .quick-assessment {
            margin-top: 15px;
            padding: 10px;
            background: #f9fafb;
            border-radius: 8px;
            font-size: 13px;
            color: #4b5563;
            font-style: italic;
        }
        
        .url-link {
            display: block;
            margin-top: 10px;
            color: #667eea;
            text-decoration: none;
            font-size: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .url-link:hover {
            text-decoration: underline;
        }
        
        .stats {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            margin-top: 5px;
        }
        
        .loading {
            text-align: center;
            color: white;
            font-size: 18px;
            margin-top: 50px;
        }
        
        .error {
            background: #fee;
            color: #c00;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Website Analysis - Stage 1 Triage</h1>
        <p class="subtitle">Quick assessment to identify projects worth deeper investigation</p>
        
        <div class="stats">
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value" id="total-count">0</div>
                    <div class="stat-label">Total Analyzed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="high-count">0</div>
                    <div class="stat-label">High Priority</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="medium-count">0</div>
                    <div class="stat-label">Medium Priority</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="proceed-count">0</div>
                    <div class="stat-label">Ready for Stage 2</div>
                </div>
            </div>
        </div>
        
        <div id="results" class="results-grid">
            <div class="loading">Loading results...</div>
        </div>
    </div>
    
    <script>
        const categoryLabels = {
            'technical_infrastructure': 'Technical',
            'business_utility': 'Business',
            'documentation_quality': 'Documentation',
            'community_social': 'Community',
            'security_trust': 'Security',
            'team_transparency': 'Team',
            'website_presentation': 'Website'
        };
        
        function createMeterBar(label, score) {
            return `
                <div class="meter-row">
                    <div class="meter-label">${label}</div>
                    <div class="meter-bar">
                        <div class="meter-fill meter-fill-${score}">
                            ${score}/3
                        </div>
                    </div>
                </div>
            `;
        }
        
        async function loadResults() {
            try {
                const response = await fetch('/api/results');
                const data = await response.json();
                
                const resultsDiv = document.getElementById('results');
                
                if (data.results.length === 0) {
                    resultsDiv.innerHTML = '<p style="color: white; text-align: center;">No results found</p>';
                    return;
                }
                
                // Calculate stats
                let totalCount = data.results.length;
                let highCount = 0;
                let mediumCount = 0;
                let proceedCount = 0;
                
                resultsDiv.innerHTML = data.results.map(result => {
                    const scores = result.category_scores || {};
                    const totalScore = result.total_score || Object.values(scores).reduce((a, b) => a + b, 0);
                    const tier = result.tier || (totalScore >= 15 ? 'HIGH' : totalScore >= 10 ? 'MEDIUM' : 'LOW');
                    const proceedToStage2 = result.proceed_to_stage_2 !== undefined ? result.proceed_to_stage_2 : totalScore >= 10;
                    
                    // Update counters
                    if (tier === 'HIGH') highCount++;
                    if (tier === 'MEDIUM') mediumCount++;
                    if (proceedToStage2) proceedCount++;
                    
                    const metersHtml = Object.entries(scores).map(([key, value]) => 
                        createMeterBar(categoryLabels[key] || key, value)
                    ).join('');
                    
                    const exceptionalHtml = result.exceptional_signals && result.exceptional_signals.length > 0 ? `
                        <div class="exceptional-signals">
                            <h4>✨ Exceptional Signals</h4>
                            <ul>
                                ${result.exceptional_signals.map(s => `<li>• ${s}</li>`).join('')}
                            </ul>
                        </div>
                    ` : '';
                    
                    const missingHtml = result.missing_elements && result.missing_elements.length > 0 ? `
                        <div class="missing-elements">
                            <h4>⚠️ Missing Elements</h4>
                            <ul>
                                ${result.missing_elements.map(s => `<li>• ${s}</li>`).join('')}
                            </ul>
                        </div>
                    ` : '';
                    
                    return `
                        <div class="result-card">
                            <div class="card-header">
                                <div>
                                    <span class="ticker">${result.ticker || 'N/A'}</span>
                                    <span class="tier-badge tier-${tier.toLowerCase()}">${tier}</span>
                                </div>
                                <div class="total-score">${totalScore}/21</div>
                            </div>
                            
                            <div class="proceed-indicator ${proceedToStage2 ? 'proceed-yes' : 'proceed-no'}">
                                ${proceedToStage2 ? '✅ Proceed to Stage 2' : '❌ Skip Stage 2'}
                            </div>
                            
                            <div class="meters-container">
                                ${metersHtml}
                            </div>
                            
                            ${exceptionalHtml}
                            ${missingHtml}
                            
                            ${result.quick_assessment ? `
                                <div class="quick-assessment">
                                    ${result.quick_assessment}
                                </div>
                            ` : ''}
                            
                            <a href="${result.url}" target="_blank" class="url-link">${result.url}</a>
                        </div>
                    `;
                }).join('');
                
                // Update stats
                document.getElementById('total-count').textContent = totalCount;
                document.getElementById('high-count').textContent = highCount;
                document.getElementById('medium-count').textContent = mediumCount;
                document.getElementById('proceed-count').textContent = proceedCount;
                
            } catch (error) {
                document.getElementById('results').innerHTML = 
                    `<div class="error">Error loading results: ${error.message}</div>`;
            }
        }
        
        // Load results on page load
        loadResults();
        
        // Refresh every 5 seconds
        setInterval(loadResults, 5000);
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
            reasoning,
            analyzed_at
        FROM website_analysis
        ORDER BY analyzed_at DESC
    """)
    
    results = []
    for row in cursor.fetchall():
        # Parse category scores from JSON if available
        category_scores_json = {}
        if row[11]:  # category_scores column
            try:
                category_scores_json = json.loads(row[11])
            except:
                pass
        
        # Use individual score columns if available, otherwise use JSON
        category_scores = {
            'technical_infrastructure': row[4] or category_scores_json.get('technical_infrastructure', 0),
            'business_utility': row[5] or category_scores_json.get('business_utility', 0),
            'documentation_quality': row[6] or category_scores_json.get('documentation_quality', 0),
            'community_social': row[7] or category_scores_json.get('community_social', 0),
            'security_trust': row[8] or category_scores_json.get('security_trust', 0),
            'team_transparency': row[9] or category_scores_json.get('team_transparency', 0),
            'website_presentation': row[10] or category_scores_json.get('website_presentation', 0),
        }
        
        # Calculate total score
        total_score = sum(category_scores.values())
        
        # Determine tier based on total
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
            'proceed_to_stage_2': total_score >= 10,
            'category_scores': category_scores,
            'quick_assessment': row[12],  # reasoning
            'analyzed_at': row[13]
        })
    
    conn.close()
    
    return jsonify({
        'results': results,
        'count': len(results)
    })

if __name__ == '__main__':
    print("Starting Enhanced Results Server on http://localhost:5005")
    app.run(port=5005, debug=True)
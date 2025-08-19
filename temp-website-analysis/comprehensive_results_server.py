#!/usr/bin/env python3
"""
Results viewer for comprehensive website analysis
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
    <title>Website Analysis Results</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
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
            margin-bottom: 30px;
            font-size: 14px;
            text-align: center;
        }
        
        .filters {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }
        
        select {
            padding: 10px 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            background: white;
        }
        
        .results-grid {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .result-card {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            padding: 20px 25px;
            transition: all 0.3s ease;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .result-card:hover {
            border-color: #667eea;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.15);
            transform: translateY(-2px);
        }
        
        .result-card.alpha-tier {
            border-color: #10b981;
        }
        
        .result-card.solid-tier {
            border-color: #3b82f6;
        }
        
        .result-card.basic-tier {
            border-color: #f59e0b;
        }
        
        .result-card.trash-tier {
            border-color: #ef4444;
        }
        
        .card-left {
            display: flex;
            align-items: center;
            flex: 1;
        }
        
        .ticker-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            font-weight: bold;
            font-size: 18px;
            color: white;
            margin-right: 20px;
        }
        
        .card-info {
            flex: 1;
        }
        
        .card-title {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 4px;
        }
        
        .card-subtitle {
            font-size: 14px;
            color: #666;
        }
        
        .model-badge {
            font-size: 11px;
            color: #999;
            text-transform: uppercase;
            margin-left: 10px;
        }
        
        .card-right {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .score-display {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }
        
        .tier-badge {
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .tier-ALPHA { 
            background: #10b981; 
            color: white; 
        }
        
        .tier-SOLID { 
            background: #3b82f6; 
            color: white; 
        }
        
        .tier-BASIC { 
            background: #f59e0b; 
            color: white; 
        }
        
        .tier-TRASH { 
            background: #ef4444; 
            color: white; 
        }
        
        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            overflow-y: auto;
        }
        
        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 30px;
            border-radius: 15px;
            width: 90%;
            max-width: 800px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                transform: translateY(-50px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover,
        .close:focus {
            color: #000;
        }
        
        .modal-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .modal-ticker-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            font-weight: bold;
            font-size: 22px;
            color: white;
            margin-right: 20px;
        }
        
        .modal-title-section {
            flex: 1;
        }
        
        .modal-title {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        
        .modal-url {
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
            margin-top: 5px;
            display: inline-block;
        }
        
        .modal-url:hover {
            text-decoration: underline;
        }
        
        .modal-score-section {
            text-align: center;
        }
        
        .modal-score {
            font-size: 48px;
            font-weight: bold;
            color: #667eea;
        }
        
        .modal-tier {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: bold;
            margin-top: 10px;
        }
        
        .modal-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 25px 0;
        }
        
        .metric {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .metric-label {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        
        .section {
            margin-top: 25px;
            padding-top: 25px;
            border-top: 1px solid #e0e0e0;
        }
        
        .section-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 12px;
            color: #333;
        }
        
        .team-member {
            display: inline-block;
            background: #e3f2fd;
            padding: 6px 12px;
            border-radius: 20px;
            margin: 5px 5px 5px 0;
            font-size: 14px;
        }
        
        .team-member.has-linkedin {
            background: #c8e6c9;
        }
        
        .document-link {
            display: inline-block;
            background: #fff3e0;
            padding: 6px 12px;
            border-radius: 8px;
            margin: 5px 5px 5px 0;
            font-size: 13px;
            text-decoration: none;
            color: #333;
        }
        
        .document-link:hover {
            background: #ffe0b2;
        }
        
        .indicator-item {
            font-size: 14px;
            padding: 4px 0;
            color: #666;
        }
        
        .positive { color: #10b981; }
        .negative { color: #ef4444; }
        
        .reasoning {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            font-size: 14px;
            line-height: 1.6;
            color: #555;
        }
        
        .timestamp {
            text-align: right;
            font-size: 12px;
            color: #999;
            margin-top: 15px;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
        }
        
        .error {
            background: #fee;
            color: #c00;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Website Analysis Results</h1>
        <p class="subtitle">AI-powered legitimacy scoring for crypto projects</p>
        
        <div class="filters">
            <select id="modelFilter">
                <option value="">All Models</option>
                <option value="Claude 3.5 Sonnet">Claude 3.5 Sonnet</option>
                <option value="GPT-4o">GPT-4o</option>
                <option value="Gemini 2.0 Flash">Gemini 2.0 Flash</option>
            </select>
        </div>
        
        <div class="results-grid" id="results">
            <div class="loading">Loading analysis results...</div>
        </div>
    </div>
    
    <!-- Modal for detailed view -->
    <div id="detailModal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <div id="modalContent"></div>
        </div>
    </div>
    
    <script>
        let allResults = [];
        let currentModal = null;
        
        function getRandomColor(ticker) {
            const colors = ['#667eea', '#764ba2', '#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
            let hash = 0;
            for (let i = 0; i < (ticker || '').length; i++) {
                hash = ticker.charCodeAt(i) + ((hash << 5) - hash);
            }
            return colors[Math.abs(hash) % colors.length];
        }
        
        function getTierClass(tier) {
            if (!tier) return '';
            switch(tier.toUpperCase()) {
                case 'ALPHA': return 'alpha-tier';
                case 'SOLID': return 'solid-tier';
                case 'BASIC': return 'basic-tier';
                case 'TRASH': return 'trash-tier';
                default: return '';
            }
        }
        
        function getScoreColor(score) {
            if (score >= 8) return '#10b981';
            if (score >= 5) return '#3b82f6';
            if (score >= 3) return '#f59e0b';
            return '#ef4444';
        }
        
        function renderResults(results) {
            const container = document.getElementById('results');
            
            if (results.length === 0) {
                container.innerHTML = '<div class="error">No results found</div>';
                return;
            }
            
            container.innerHTML = results.map((r, index) => {
                const ticker = r.ticker || 'N/A';
                const tierClass = getTierClass(r.tier);
                
                return `
                    <div class="result-card ${tierClass}" onclick="showDetails(${index})">
                        <div class="card-left">
                            <div class="ticker-badge" style="background: ${getRandomColor(ticker)}">
                                ${ticker.substring(0, 2).toUpperCase()}
                            </div>
                            <div class="card-info">
                                <div class="card-title">
                                    ${ticker}
                                    <span class="model-badge">AVG OF 3 MODELS</span>
                                </div>
                                <div class="card-subtitle">${r.url}</div>
                            </div>
                        </div>
                        <div class="card-right">
                            <div class="score-display" style="color: ${getScoreColor(r.score)}">
                                ${r.score ? r.score.toFixed(0) : '-'}
                            </div>
                            <div class="tier-badge tier-${r.tier}">
                                ${r.tier || 'UNKNOWN'}
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function showDetails(index) {
            const r = allResults[index];
            if (!r) return;
            
            const modal = document.getElementById('detailModal');
            const modalContent = document.getElementById('modalContent');
            
            const ticker = r.ticker || 'N/A';
            const teamMembers = r.team_members || [];
            const documents = r.documents || [];
            const legitimacyIndicators = r.legitimacy_indicators || [];
            const redFlags = r.red_flags || [];
            
            modalContent.innerHTML = `
                <div class="modal-header">
                    <div class="modal-ticker-badge" style="background: ${getRandomColor(ticker)}">
                        ${ticker.substring(0, 2).toUpperCase()}
                    </div>
                    <div class="modal-title-section">
                        <div class="modal-title">${ticker}</div>
                        <a href="${r.url}" target="_blank" class="modal-url">${r.url} ↗</a>
                    </div>
                    <div class="modal-score-section">
                        <div class="modal-score" style="color: ${getScoreColor(r.score)}">
                            ${r.score ? r.score.toFixed(1) : 'N/A'}
                        </div>
                        <div class="modal-tier tier-badge tier-${r.tier}">
                            ${r.tier || 'UNKNOWN'}
                        </div>
                    </div>
                </div>
                
                <div class="modal-metrics">
                    <div class="metric">
                        <div class="metric-label">Team Members</div>
                        <div class="metric-value">${r.team_members_found || 0}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">LinkedIn</div>
                        <div class="metric-value">${r.linkedin_profiles || 0}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Documents</div>
                        <div class="metric-value">${r.documents_found || 0}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Parse Status</div>
                        <div class="metric-value">${r.parse_success ? '✅' : '❌'}</div>
                    </div>
                </div>
                
                ${teamMembers.length > 0 ? `
                    <div class="section">
                        <div class="section-title">👥 Team Members Identified</div>
                        ${teamMembers.map(m => `
                            <span class="team-member ${m.has_linkedin ? 'has-linkedin' : ''}">
                                ${m.name} ${m.role ? `(${m.role})` : ''} ${m.has_linkedin ? '🔗' : ''}
                            </span>
                        `).join('')}
                    </div>
                ` : ''}
                
                ${documents.length > 0 ? `
                    <div class="section">
                        <div class="section-title">📄 Documents Found</div>
                        ${documents.map(d => `
                            <a href="${d.url}" target="_blank" class="document-link">
                                ${d.type ? d.type.toUpperCase() : 'DOC'}: ${d.text || 'Document'}
                            </a>
                        `).join('')}
                    </div>
                ` : ''}
                
                ${r.navigation ? `
                    <div class="section">
                        <div class="section-title">🧭 Navigation Analysis</div>
                        <div style="margin-bottom: 15px;">
                            <strong>Found ${r.navigation.total_links || 0} total links</strong> 
                            (${r.navigation.high_priority || 0} high priority)
                        </div>
                        ${r.navigation.all_links && r.navigation.all_links.length > 0 ? `
                            <div>
                                <strong>All ${r.navigation.all_links.length} Links Found:</strong>
                                <div style="margin-top: 10px; max-height: 300px; overflow-y: auto; background: #f9fafb; padding: 10px; border-radius: 8px;">
                                    ${r.navigation.all_links.map(l => {
                                        const priorityColor = l.priority === 'high' ? '#fef3c7' : 
                                                            l.priority === 'medium' ? '#dbeafe' : '#e5e7eb';
                                        const typeColor = l.type === 'docs' || l.type === 'whitepaper' ? '#059669' :
                                                        l.type === 'team' ? '#7c3aed' :
                                                        l.type === 'external' ? '#dc2626' :
                                                        l.type === 'anchor' ? '#0284c7' : '#6b7280';
                                        
                                        // Check if this link was parsed (from backend)
                                        const wasParsed = l.parsed === true;
                                        
                                        return `
                                            <div style="padding: 4px 0; font-size: 13px; display: flex; align-items: center; border-bottom: 1px solid #e5e7eb;">
                                                <span style="background: ${priorityColor}; padding: 2px 6px; border-radius: 4px; font-size: 10px; min-width: 70px; text-align: center; margin-right: 8px; color: ${typeColor}; font-weight: bold;">
                                                    ${l.type.toUpperCase()}
                                                </span>
                                                <span style="color: #374151; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                                    ${l.text}
                                                    ${wasParsed ? '<span style="color: #10b981; font-weight: bold; margin-left: 8px;">(parsed)</span>' : ''}
                                                </span>
                                                ${l.priority === 'high' ? '<span style="color: #f59e0b; margin-left: 8px;">⭐</span>' : ''}
                                            </div>
                                        `;
                                    }).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                ` : ''}
                
                ${legitimacyIndicators.length > 0 ? `
                    <div class="section">
                        <div class="section-title positive">✅ Positive Indicators</div>
                        ${legitimacyIndicators.map(i => `
                            <div class="indicator-item positive">• ${i}</div>
                        `).join('')}
                    </div>
                ` : ''}
                
                ${redFlags.length > 0 ? `
                    <div class="section">
                        <div class="section-title negative">⚠️ Red Flags</div>
                        ${redFlags.map(f => `
                            <div class="indicator-item negative">• ${f}</div>
                        `).join('')}
                    </div>
                ` : ''}
                
                ${r.reasoning ? `
                    <div class="section">
                        <div class="section-title">🤖 AI Assessment</div>
                        <div class="reasoning">${r.reasoning}</div>
                    </div>
                ` : ''}
                
                ${r.technical_depth ? `
                    <div class="section">
                        <div class="section-title">💻 Technical Depth</div>
                        <div class="reasoning">${r.technical_depth}</div>
                    </div>
                ` : ''}
                
                ${r.team_transparency ? `
                    <div class="section">
                        <div class="section-title">👁️ Team Transparency</div>
                        <div class="reasoning">${r.team_transparency}</div>
                    </div>
                ` : ''}
                
                <div class="timestamp">
                    Analyzed: ${new Date(r.analyzed_at).toLocaleString()}
                </div>
            `;
            
            modal.style.display = 'block';
            currentModal = modal;
        }
        
        async function loadResults() {
            try {
                const response = await fetch('/api/comprehensive');
                const data = await response.json();
                allResults = data;
                
                // Sort by score by default
                allResults.sort((a, b) => (b.score || 0) - (a.score || 0));
                
                renderResults(allResults);
            } catch (error) {
                document.getElementById('results').innerHTML = 
                    '<div class="error">Error loading results: ' + error.message + '</div>';
            }
        }
        
        // Modal close handlers
        document.getElementsByClassName('close')[0].onclick = function() {
            document.getElementById('detailModal').style.display = 'none';
        }
        
        window.onclick = function(event) {
            const modal = document.getElementById('detailModal');
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        }
        
        // Filter handler
        document.getElementById('modelFilter').addEventListener('change', function() {
            // This is placeholder for model filtering
            // Currently showing average of all models
            renderResults(allResults);
        });
        
        // Load results on page load
        loadResults();
        
        // Refresh every 30 seconds
        setInterval(loadResults, 30000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/comprehensive')
def get_comprehensive_results():
    """Get comprehensive analysis results from database"""
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Get all analyzed websites with comprehensive data
    cursor.execute("""
        SELECT 
            wa.url,
            wa.score,
            wa.tier,
            wa.team_members_found,
            wa.linkedin_profiles,
            wa.documents_found,
            wa.legitimacy_indicators,
            wa.red_flags,
            wa.technical_depth,
            wa.team_transparency,
            wa.reasoning,
            wa.analyzed_at,
            wa.parse_success,
            wa.parsed_content,
            wa.ticker
        FROM website_analysis wa
        WHERE wa.parse_success = 1
        ORDER BY wa.analyzed_at DESC
    """)
    
    results = []
    for row in cursor.fetchall():
        parsed_content = json.loads(row[13]) if row[13] else {}
        
        # Extract team members from parsed content
        team_members = []
        if 'extracted_team_members' in parsed_content:
            for member in parsed_content['extracted_team_members']:
                team_members.append({
                    'name': member.get('name', ''),
                    'role': member.get('role', ''),
                    'has_linkedin': bool(member.get('linkedin'))
                })
        
        # Extract documents
        documents = parsed_content.get('documents', [])
        
        # Extract navigation data
        navigation = parsed_content.get('navigation', {})
        all_links = navigation.get('all_links', [])
        parsed_sections = navigation.get('parsed_sections', [])
        
        # Parse JSON fields
        legitimacy_indicators = json.loads(row[6]) if row[6] else []
        red_flags = json.loads(row[7]) if row[7] else []
        
        results.append({
            'url': row[0],
            'score': row[1],
            'tier': row[2],
            'team_members_found': row[3] or 0,
            'linkedin_profiles': row[4] or 0,
            'documents_found': row[5] or 0,
            'legitimacy_indicators': legitimacy_indicators,
            'red_flags': red_flags,
            'technical_depth': row[8],
            'team_transparency': row[9],
            'reasoning': row[10],
            'analyzed_at': row[11],
            'parse_success': row[12],
            'ticker': row[14],
            'team_members': team_members,
            'documents': documents[:5],  # Limit to 5 documents for display
            'navigation': {
                'total_links': len(all_links),
                'high_priority': len([l for l in all_links if l.get('priority') == 'high']),
                'parsed_sections': parsed_sections,
                'all_links': all_links  # Show all links
            }
        })
    
    conn.close()
    return jsonify(results)

if __name__ == '__main__':
    print("✨ Starting Comprehensive Website Analysis Results Viewer")
    print("📍 Open http://localhost:5005 in your browser")
    print("Press Ctrl+C to stop\n")
    app.run(host='0.0.0.0', port=5005, debug=True)
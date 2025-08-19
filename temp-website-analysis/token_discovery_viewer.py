#!/usr/bin/env python3
"""
Web UI for viewing token_discovery website analysis results
Based on fixed_results_server.py but for token_discovery data
"""

from flask import Flask, render_template_string, jsonify, request
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('token_discovery_analysis.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_analysis_results(sort_by='total_score', filter_stage2=None, search_query=None):
    """Get all analysis results with optional filtering and sorting"""
    conn = get_db_connection()
    
    # Base query
    query = """
        SELECT 
            ticker,
            url,
            parsed_content,
            total_score,
            category_scores,
            exceptional_signals,
            missing_elements,
            proceed_to_stage_2,
            automatic_stage_2_qualifiers,
            analysis_prompt,
            raw_ai_response,
            metadata,
            analyzed_at
        FROM website_analysis
    """
    
    # Add search filter if provided
    conditions = []
    params = []
    
    if search_query:
        conditions.append("(LOWER(ticker) LIKE ? OR LOWER(url) LIKE ?)")
        search_param = f"%{search_query.lower()}%"
        params.extend([search_param, search_param])
    
    if filter_stage2 is not None:
        conditions.append("proceed_to_stage_2 = ?")
        params.append(filter_stage2)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    # Add sorting
    if sort_by == 'total_score':
        query += " ORDER BY total_score DESC, ticker ASC"
    elif sort_by == 'ticker':
        query += " ORDER BY ticker ASC"
    elif sort_by == 'liquidity':
        query += " ORDER BY json_extract(metadata, '$.initial_liquidity_usd') DESC NULLS LAST"
    elif sort_by == 'volume':
        query += " ORDER BY json_extract(metadata, '$.initial_volume_24h') DESC NULLS LAST"
    else:
        query += " ORDER BY total_score DESC"
    
    cursor = conn.execute(query, params)
    results = []
    
    for row in cursor.fetchall():
        result = dict(row)
        
        # Parse JSON fields
        for field in ['parsed_content', 'category_scores', 'exceptional_signals', 
                     'missing_elements', 'automatic_stage_2_qualifiers', 'metadata']:
            if result.get(field):
                try:
                    result[field] = json.loads(result[field])
                except:
                    result[field] = {}
        
        results.append(result)
    
    conn.close()
    return results

@app.route('/')
def index():
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Token Discovery Website Analysis Results</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            h1 {
                margin: 0;
                font-size: 2.5em;
                font-weight: 700;
            }
            .subtitle {
                margin-top: 10px;
                opacity: 0.9;
                font-size: 1.1em;
            }
            .controls {
                padding: 20px 30px;
                background: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                display: flex;
                gap: 20px;
                align-items: center;
                flex-wrap: wrap;
            }
            .search-box {
                flex: 1;
                min-width: 200px;
            }
            .search-box input {
                width: 100%;
                padding: 10px 15px;
                border: 2px solid #dee2e6;
                border-radius: 10px;
                font-size: 14px;
            }
            .filter-group {
                display: flex;
                gap: 10px;
                align-items: center;
            }
            .filter-btn {
                padding: 8px 16px;
                border: 2px solid #dee2e6;
                background: white;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
            }
            .filter-btn:hover {
                background: #667eea;
                color: white;
                border-color: #667eea;
            }
            .filter-btn.active {
                background: #667eea;
                color: white;
                border-color: #667eea;
            }
            .stats {
                padding: 20px 30px;
                background: #f8f9fa;
                display: flex;
                gap: 30px;
                justify-content: center;
            }
            .stat-item {
                text-align: center;
            }
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
            }
            .stat-label {
                color: #6c757d;
                margin-top: 5px;
            }
            .results-container {
                padding: 30px;
            }
            .result-item {
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                transition: all 0.3s;
                cursor: pointer;
            }
            .result-item:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                border-color: #667eea;
            }
            .result-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            .ticker-name {
                font-size: 1.4em;
                font-weight: bold;
                color: #333;
            }
            .score-badge {
                padding: 8px 15px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 1.1em;
            }
            .high-score {
                background: linear-gradient(135deg, #00c851 0%, #00a940 100%);
                color: white;
            }
            .medium-score {
                background: linear-gradient(135deg, #ffbb33 0%, #ff8800 100%);
                color: white;
            }
            .low-score {
                background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
                color: white;
            }
            .metadata-row {
                display: flex;
                gap: 20px;
                margin: 10px 0;
                color: #6c757d;
                font-size: 0.9em;
            }
            .metadata-item {
                display: flex;
                align-items: center;
                gap: 5px;
            }
            .category-scores {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 10px;
                margin: 15px 0;
            }
            .category-item {
                padding: 8px;
                background: #f8f9fa;
                border-radius: 8px;
                text-align: center;
            }
            .category-name {
                font-size: 0.8em;
                color: #6c757d;
                margin-bottom: 5px;
            }
            .category-score {
                font-weight: bold;
                font-size: 1.1em;
            }
            .signals-section {
                margin-top: 15px;
                display: flex;
                gap: 20px;
            }
            .signal-box {
                flex: 1;
                padding: 10px;
                border-radius: 8px;
            }
            .exceptional-signals {
                background: #d4edda;
                border: 1px solid #c3e6cb;
            }
            .missing-elements {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
            }
            .signal-title {
                font-weight: bold;
                margin-bottom: 5px;
                color: #333;
            }
            .signal-item {
                font-size: 0.9em;
                margin: 3px 0;
            }
            .stage2-badge {
                display: inline-block;
                padding: 5px 10px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 5px;
                font-size: 0.85em;
                font-weight: bold;
                margin-left: 10px;
            }
            .url-link {
                color: #667eea;
                text-decoration: none;
                font-size: 0.9em;
            }
            .url-link:hover {
                text-decoration: underline;
            }
            
            /* Modal styles */
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
                margin: 50px auto;
                padding: 0;
                width: 90%;
                max-width: 1000px;
                border-radius: 15px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            .modal-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 15px 15px 0 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .modal-body {
                padding: 30px;
                max-height: 70vh;
                overflow-y: auto;
            }
            .close-btn {
                color: white;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
                background: none;
                border: none;
            }
            .close-btn:hover {
                opacity: 0.8;
            }
            .detail-section {
                margin-bottom: 25px;
            }
            .detail-title {
                font-size: 1.2em;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
                border-bottom: 2px solid #667eea;
                padding-bottom: 5px;
            }
            .navigation-links {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 10px;
            }
            .nav-link {
                padding: 5px 10px;
                background: #f8f9fa;
                border-radius: 5px;
                color: #667eea;
                text-decoration: none;
                font-size: 0.9em;
            }
            .nav-link:hover {
                background: #667eea;
                color: white;
            }
            .liquidity-value {
                color: #00c851;
                font-weight: bold;
            }
            .volume-value {
                color: #667eea;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Token Discovery Website Analysis</h1>
                <div class="subtitle">Analyzing tokens discovered via GeckoTerminal API</div>
            </div>
            
            <div class="controls">
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Search by ticker or URL...">
                </div>
                <div class="filter-group">
                    <button class="filter-btn" onclick="setSortBy('total_score')">Score</button>
                    <button class="filter-btn" onclick="setSortBy('liquidity')">Liquidity</button>
                    <button class="filter-btn" onclick="setSortBy('volume')">Volume</button>
                    <button class="filter-btn" onclick="setSortBy('ticker')">A-Z</button>
                </div>
                <div class="filter-group">
                    <button class="filter-btn" onclick="setStage2Filter('all')">All</button>
                    <button class="filter-btn" onclick="setStage2Filter('true')">Stage 2 ✓</button>
                    <button class="filter-btn" onclick="setStage2Filter('false')">Stage 2 ✗</button>
                </div>
            </div>
            
            <div class="stats" id="stats"></div>
            
            <div class="results-container" id="results"></div>
        </div>
        
        <!-- Modal for detailed view -->
        <div id="detailModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="modalTitle">Token Details</h2>
                    <button class="close-btn" onclick="closeModal()">&times;</button>
                </div>
                <div class="modal-body" id="modalBody"></div>
            </div>
        </div>
        
        <script>
            let currentSort = 'total_score';
            let currentFilter = 'all';
            let currentSearch = '';
            let allResults = [];
            
            async function loadResults() {
                const response = await fetch('/api/results');
                allResults = await response.json();
                displayResults();
            }
            
            function displayResults() {
                let filtered = [...allResults];
                
                // Apply search filter
                if (currentSearch) {
                    const search = currentSearch.toLowerCase();
                    filtered = filtered.filter(r => 
                        r.ticker.toLowerCase().includes(search) ||
                        r.url.toLowerCase().includes(search)
                    );
                }
                
                // Apply stage 2 filter
                if (currentFilter === 'true') {
                    filtered = filtered.filter(r => r.proceed_to_stage_2);
                } else if (currentFilter === 'false') {
                    filtered = filtered.filter(r => !r.proceed_to_stage_2);
                }
                
                // Sort
                if (currentSort === 'total_score') {
                    filtered.sort((a, b) => b.total_score - a.total_score);
                } else if (currentSort === 'ticker') {
                    filtered.sort((a, b) => a.ticker.localeCompare(b.ticker));
                } else if (currentSort === 'liquidity') {
                    filtered.sort((a, b) => {
                        const aLiq = a.metadata?.liquidity_usd || 0;
                        const bLiq = b.metadata?.liquidity_usd || 0;
                        return bLiq - aLiq;
                    });
                } else if (currentSort === 'volume') {
                    filtered.sort((a, b) => {
                        const aVol = a.metadata?.volume_24h || 0;
                        const bVol = b.metadata?.volume_24h || 0;
                        return bVol - aVol;
                    });
                }
                
                // Update stats
                const stats = document.getElementById('stats');
                const stage2Count = filtered.filter(r => r.proceed_to_stage_2).length;
                const avgScore = filtered.reduce((sum, r) => sum + r.total_score, 0) / filtered.length || 0;
                
                stats.innerHTML = `
                    <div class="stat-item">
                        <div class="stat-value">${filtered.length}</div>
                        <div class="stat-label">Total Analyzed</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stage2Count}</div>
                        <div class="stat-label">Stage 2 Qualified</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${avgScore.toFixed(1)}</div>
                        <div class="stat-label">Average Score</div>
                    </div>
                `;
                
                // Display results
                const container = document.getElementById('results');
                container.innerHTML = filtered.map((result, index) => {
                    const scoreClass = result.total_score >= 14 ? 'high-score' : 
                                      result.total_score >= 10 ? 'medium-score' : 'low-score';
                    
                    const liquidity = result.metadata?.liquidity_usd || 0;
                    const volume = result.metadata?.volume_24h || 0;
                    
                    return `
                        <div class="result-item" onclick="showDetails(${index})">
                            <div class="result-header">
                                <div>
                                    <span class="ticker-name">${result.ticker}</span>
                                    ${result.proceed_to_stage_2 ? '<span class="stage2-badge">STAGE 2</span>' : ''}
                                </div>
                                <div class="score-badge ${scoreClass}">${result.total_score}/21</div>
                            </div>
                            
                            <div class="metadata-row">
                                ${liquidity > 0 ? `<div class="metadata-item">💰 <span class="liquidity-value">$${formatNumber(liquidity)}</span> liquidity</div>` : ''}
                                ${volume > 0 ? `<div class="metadata-item">📊 <span class="volume-value">$${formatNumber(volume)}</span> volume</div>` : ''}
                                <div class="metadata-item">🔗 <a href="${result.url}" target="_blank" class="url-link" onclick="event.stopPropagation()">${formatUrl(result.url)}</a></div>
                            </div>
                            
                            <div class="metadata-row">
                                ${result.metadata?.contract_address ? `
                                    <div class="metadata-item">
                                        📋 <span style="font-family: monospace; font-size: 0.85em;">${result.metadata.contract_address.substring(0, 6)}...${result.metadata.contract_address.slice(-4)}</span>
                                    </div>
                                    <div class="metadata-item">
                                        📈 <a href="https://dexscreener.com/${result.metadata.network === 'eth' ? 'ethereum' : (result.metadata.network || 'solana')}/${result.metadata.contract_address}" target="_blank" class="url-link" onclick="event.stopPropagation()">View on DexScreener</a>
                                    </div>
                                ` : ''}
                            </div>
                            
                            <div class="category-scores">
                                ${Object.entries(result.category_scores || {}).map(([cat, score]) => `
                                    <div class="category-item">
                                        <div class="category-name">${cat.replace(/_/g, ' ')}</div>
                                        <div class="category-score">${score}/3</div>
                                    </div>
                                `).join('')}
                            </div>
                            
                            <div class="signals-section">
                                ${result.exceptional_signals?.length ? `
                                    <div class="signal-box exceptional-signals">
                                        <div class="signal-title">✅ Exceptional Signals</div>
                                        ${result.exceptional_signals.map(s => `<div class="signal-item">• ${s}</div>`).join('')}
                                    </div>
                                ` : ''}
                                ${result.missing_elements?.length ? `
                                    <div class="signal-box missing-elements">
                                        <div class="signal-title">❌ Missing Elements</div>
                                        ${result.missing_elements.map(s => `<div class="signal-item">• ${s}</div>`).join('')}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `;
                }).join('');
                
                // Update filter buttons
                document.querySelectorAll('.filter-btn').forEach(btn => {
                    btn.classList.remove('active');
                });
            }
            
            function formatNumber(num) {
                if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M';
                if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
                return num.toFixed(0);
            }
            
            function formatUrl(url) {
                if (url.length > 40) {
                    return url.substring(0, 37) + '...';
                }
                return url;
            }
            
            function setSortBy(sort) {
                currentSort = sort;
                displayResults();
            }
            
            function setStage2Filter(filter) {
                currentFilter = filter;
                displayResults();
            }
            
            function showDetails(index) {
                const filtered = getFilteredResults();
                const result = filtered[index];
                
                document.getElementById('modalTitle').textContent = `${result.ticker} - Detailed Analysis`;
                
                const modalBody = document.getElementById('modalBody');
                modalBody.innerHTML = `
                    <div class="detail-section">
                        <div class="detail-title">Overview</div>
                        <p><strong>Website:</strong> <a href="${result.url}" target="_blank">${result.url}</a></p>
                        <p><strong>Total Score:</strong> ${result.total_score}/21</p>
                        <p><strong>Stage 2 Recommendation:</strong> ${result.proceed_to_stage_2 ? 'Yes ✅' : 'No ❌'}</p>
                        ${result.metadata?.contract_address ? `
                            <p><strong>Contract:</strong> <span style="font-family: monospace;">${result.metadata.contract_address}</span></p>
                            <p><strong>Network:</strong> ${result.metadata.network || 'solana'}</p>
                            <p><strong>DexScreener:</strong> <a href="https://dexscreener.com/${result.metadata.network === 'eth' ? 'ethereum' : (result.metadata.network || 'solana')}/${result.metadata.contract_address}" target="_blank">View Chart & Analytics</a></p>
                        ` : ''}
                        ${result.metadata?.initial_liquidity_usd ? `<p><strong>Liquidity:</strong> $${formatNumber(result.metadata.initial_liquidity_usd)}</p>` : ''}
                        ${result.metadata?.initial_volume_24h ? `<p><strong>24h Volume:</strong> $${formatNumber(result.metadata.initial_volume_24h)}</p>` : ''}
                    </div>
                    
                    <div class="detail-section">
                        <div class="detail-title">Category Scores</div>
                        ${Object.entries(result.category_scores || {}).map(([cat, score]) => 
                            `<p><strong>${cat.replace(/_/g, ' ')}:</strong> ${score}/3</p>`
                        ).join('')}
                    </div>
                    
                    ${result.automatic_stage_2_qualifiers?.length ? `
                        <div class="detail-section">
                            <div class="detail-title">Automatic Stage 2 Qualifiers</div>
                            ${result.automatic_stage_2_qualifiers.map(q => `<p>• ${q}</p>`).join('')}
                        </div>
                    ` : ''}
                    
                    ${result.parsed_content?.navigation?.all_links?.length ? `
                        <div class="detail-section">
                            <div class="detail-title">Navigation Links Found</div>
                            <div class="navigation-links">
                                ${result.parsed_content.navigation.all_links.map(link => 
                                    `<a href="${link.url}" target="_blank" class="nav-link">${link.text || link.url}</a>`
                                ).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${result.analysis_prompt ? `
                        <div class="detail-section">
                            <div class="detail-title">Analysis Prompt</div>
                            <pre style="white-space: pre-wrap; background: #f8f9fa; padding: 15px; border-radius: 8px;">${result.analysis_prompt}</pre>
                        </div>
                    ` : ''}
                `;
                
                document.getElementById('detailModal').style.display = 'block';
            }
            
            function closeModal() {
                document.getElementById('detailModal').style.display = 'none';
            }
            
            function getFilteredResults() {
                let filtered = [...allResults];
                
                if (currentSearch) {
                    const search = currentSearch.toLowerCase();
                    filtered = filtered.filter(r => 
                        r.ticker.toLowerCase().includes(search) ||
                        r.url.toLowerCase().includes(search)
                    );
                }
                
                if (currentFilter === 'true') {
                    filtered = filtered.filter(r => r.proceed_to_stage_2);
                } else if (currentFilter === 'false') {
                    filtered = filtered.filter(r => !r.proceed_to_stage_2);
                }
                
                if (currentSort === 'total_score') {
                    filtered.sort((a, b) => b.total_score - a.total_score);
                } else if (currentSort === 'ticker') {
                    filtered.sort((a, b) => a.ticker.localeCompare(b.ticker));
                } else if (currentSort === 'liquidity') {
                    filtered.sort((a, b) => {
                        const aLiq = a.metadata?.liquidity_usd || 0;
                        const bLiq = b.metadata?.liquidity_usd || 0;
                        return bLiq - aLiq;
                    });
                } else if (currentSort === 'volume') {
                    filtered.sort((a, b) => {
                        const aVol = a.metadata?.volume_24h || 0;
                        const bVol = b.metadata?.volume_24h || 0;
                        return bVol - aVol;
                    });
                }
                
                return filtered;
            }
            
            // Search functionality
            document.getElementById('searchInput').addEventListener('input', (e) => {
                currentSearch = e.target.value;
                displayResults();
            });
            
            // Close modal when clicking outside
            window.onclick = function(event) {
                const modal = document.getElementById('detailModal');
                if (event.target == modal) {
                    modal.style.display = 'none';
                }
            }
            
            // Load results on page load
            loadResults();
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@app.route('/api/results')
def api_results():
    results = get_analysis_results()
    return jsonify(results)

if __name__ == '__main__':
    print("Starting Token Discovery Website Analysis Viewer...")
    print("Server running at http://localhost:5007")
    print("Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=5007, debug=False)
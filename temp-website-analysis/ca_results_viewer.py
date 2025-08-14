#!/usr/bin/env python3
"""
Flask server to view CA verification results from intelligent parser
"""

from flask import Flask, render_template_string
import sqlite3
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CA Verification Results - Intelligent Parser</title>
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
            max-width: 1400px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .subtitle {
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.2em;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .legitimate { color: #10b981; }
        .fake { color: #ef4444; }
        .error { color: #f59e0b; }
        .total { color: #6366f1; }
        
        .results-table {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        tr:hover {
            background: #f9fafb;
        }
        
        .verdict-badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .verdict-legitimate {
            background: #d1fae5;
            color: #065f46;
        }
        
        .verdict-fake {
            background: #fee2e2;
            color: #991b1b;
        }
        
        .verdict-error {
            background: #fed7aa;
            color: #92400e;
        }
        
        .verdict-no-website {
            background: #e5e7eb;
            color: #4b5563;
        }
        
        .location-type {
            display: inline-block;
            padding: 3px 8px;
            background: #eff6ff;
            color: #1e40af;
            border-radius: 5px;
            font-size: 0.8em;
        }
        
        .contract-address {
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #6b7280;
            cursor: pointer;
            transition: all 0.2s;
            word-break: break-all;
            max-width: 300px;
            display: inline-block;
        }
        
        .contract-address:hover {
            color: #4b5563;
            background: #f3f4f6;
            padding: 2px 4px;
            border-radius: 3px;
        }
        
        .search-btn {
            background: #6366f1;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.2s;
            min-width: 32px;
        }
        
        .search-btn:hover {
            background: #4f46e5;
            transform: scale(1.05);
        }
        
        .website-link {
            color: #6366f1;
            text-decoration: none;
            word-break: break-all;
        }
        
        .website-link:hover {
            text-decoration: underline;
        }
        
        .found-location {
            font-size: 0.85em;
            word-break: break-all;
        }
        
        .location-link {
            color: #10b981;
            text-decoration: none;
            transition: all 0.2s;
        }
        
        .location-link:hover {
            color: #059669;
            text-decoration: underline;
        }
        
        .error-message {
            color: #ef4444;
            font-size: 0.85em;
        }
        
        .ticker-badge {
            font-weight: bold;
            color: #1f2937;
        }
        
        .network-badge {
            display: inline-block;
            padding: 2px 6px;
            background: #f3f4f6;
            color: #6b7280;
            border-radius: 3px;
            font-size: 0.75em;
            text-transform: uppercase;
        }
        
        .urls-checked {
            color: #6b7280;
            font-size: 0.9em;
        }
        
        .timestamp {
            color: #9ca3af;
            font-size: 0.8em;
        }
        
        .refresh-note {
            text-align: center;
            color: rgba(255,255,255,0.8);
            margin-top: 20px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 CA Verification Results</h1>
        <div class="subtitle">Intelligent Website Parser - No AI Needed</div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number total">{{ stats.total }}</div>
                <div class="stat-label">Total Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-number legitimate">{{ stats.legitimate }}</div>
                <div class="stat-label">Legitimate</div>
            </div>
            <div class="stat-card">
                <div class="stat-number fake">{{ stats.fake }}</div>
                <div class="stat-label">Fake/Imposter</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error">{{ stats.error }}</div>
                <div class="stat-label">Errors/No Site</div>
            </div>
        </div>
        
        <div class="results-table">
            <table>
                <thead>
                    <tr>
                        <th>Token</th>
                        <th>Contract</th>
                        <th>Website</th>
                        <th>Verdict</th>
                        <th>Found Location</th>
                        <th>Pages Checked</th>
                        <th>Verified</th>
                    </tr>
                </thead>
                <tbody>
                    {% for result in results %}
                    <tr>
                        <td>
                            <span class="ticker-badge">{{ result.ticker }}</span>
                            <span class="network-badge">{{ result.network }}</span>
                        </td>
                        <td>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <span class="contract-address" title="Click to copy" onclick="copyToClipboard('{{ result.contract_address }}', this)">
                                    {{ result.contract_address }}
                                </span>
                                <button class="search-btn" onclick="searchGoogleSite('{{ result.website_url }}', '{{ result.contract_address }}')" title="Search contract on website">
                                    🔍
                                </button>
                            </div>
                        </td>
                        <td>
                            {% if result.website_url and result.website_url != 'None' %}
                                <a href="{{ result.website_url }}" target="_blank" class="website-link">
                                    {{ result.website_url[:40] }}{% if result.website_url|length > 40 %}...{% endif %}
                                </a>
                            {% else %}
                                <span style="color: #9ca3af;">No website</span>
                            {% endif %}
                        </td>
                        <td>
                            <span class="verdict-badge verdict-{{ result.verdict.lower().replace('_', '-') }}">
                                {% if result.verdict == 'LEGITIMATE' %}
                                    ✅ {{ result.verdict }}
                                {% elif result.verdict == 'FAKE' %}
                                    🚫 {{ result.verdict }}
                                {% elif result.verdict == 'ERROR' or result.verdict == 'WEBSITE_DOWN' %}
                                    ❌ {{ result.verdict }}
                                {% else %}
                                    ⚫ {{ result.verdict }}
                                {% endif %}
                            </span>
                        </td>
                        <td>
                            {% if result.found_location %}
                                <div class="found-location">
                                    <span class="location-type">{{ result.location_type or 'found' }}</span>
                                    <br>
                                    <a href="{{ result.found_location }}" target="_blank" class="location-link" 
                                       onclick="openAndSearch('{{ result.found_location }}', '{{ result.contract_address }}'); return false;">
                                        {{ result.found_location[:50] }}{% if result.found_location|length > 50 %}...{% endif %}
                                    </a>
                                </div>
                            {% elif result.error %}
                                <div class="error-message">
                                    {{ result.error[:50] }}{% if result.error|length > 50 %}...{% endif %}
                                </div>
                            {% else %}
                                <span style="color: #9ca3af;">-</span>
                            {% endif %}
                        </td>
                        <td>
                            <span class="urls-checked">{{ result.urls_checked or 0 }}</span>
                        </td>
                        <td>
                            <span class="timestamp">
                                {{ result.verified_at[:10] if result.verified_at else '-' }}
                            </span>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <div class="refresh-note">
            Page auto-refreshes every 30 seconds | Last updated: {{ current_time }}
        </div>
    </div>
    
    <script>
        // Auto-refresh every 30 seconds
        setTimeout(() => {
            window.location.reload();
        }, 30000);
        
        // Copy to clipboard function
        function copyToClipboard(text, element) {
            navigator.clipboard.writeText(text).then(() => {
                // Store original text
                const originalText = element.innerText;
                
                // Show feedback
                element.innerText = '✓ Copied!';
                element.style.color = '#10b981';
                
                // Reset after 2 seconds
                setTimeout(() => {
                    element.innerText = originalText;
                    element.style.color = '';
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
            });
        }
        
        // Open website and prepare for searching the contract
        function openAndSearch(url, contractAddress) {
            // Open the URL in a new tab
            const newWindow = window.open(url, '_blank');
            
            // Also copy the contract to clipboard for easy Ctrl+F
            navigator.clipboard.writeText(contractAddress).then(() => {
                // Show a tooltip or alert
                showTooltip('Contract copied! Use Ctrl+F (or Cmd+F) to search on the opened page');
            }).catch(err => {
                console.error('Failed to copy contract:', err);
            });
        }
        
        // Show tooltip message
        function showTooltip(message) {
            // Create tooltip element if it doesn't exist
            let tooltip = document.getElementById('search-tooltip');
            if (!tooltip) {
                tooltip = document.createElement('div');
                tooltip.id = 'search-tooltip';
                tooltip.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #10b981;
                    color: white;
                    padding: 12px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    z-index: 10000;
                    font-size: 14px;
                    animation: slideIn 0.3s ease;
                `;
                document.body.appendChild(tooltip);
            }
            
            tooltip.textContent = message;
            tooltip.style.display = 'block';
            
            // Hide after 3 seconds
            setTimeout(() => {
                tooltip.style.display = 'none';
            }, 3000);
        }
        
        // Search contract on website using Google site: search
        function searchGoogleSite(websiteUrl, contractAddress) {
            if (!websiteUrl || websiteUrl === 'None') {
                // If no website, just search for the contract
                const searchQuery = `"${contractAddress}"`;
                const googleUrl = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;
                window.open(googleUrl, '_blank');
                return;
            }
            
            // Extract domain from URL
            let domain = websiteUrl;
            try {
                const url = new URL(websiteUrl);
                domain = url.hostname.replace('www.', '');
            } catch (e) {
                // If URL parsing fails, try to extract domain manually
                domain = websiteUrl.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0];
            }
            
            // Create site: search query
            const searchQuery = `site:${domain} "${contractAddress}"`;
            const googleUrl = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}`;
            window.open(googleUrl, '_blank');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    conn = sqlite3.connect('utility_tokens_ca.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all verification results
    cursor.execute("""
        SELECT 
            ticker,
            network,
            contract_address,
            website_url,
            verdict,
            found_location,
            location_type,
            urls_checked,
            error,
            verified_at
        FROM ca_verification_results
        ORDER BY 
            CASE verdict 
                WHEN 'LEGITIMATE' THEN 1
                WHEN 'FAKE' THEN 2
                WHEN 'ERROR' THEN 3
                WHEN 'WEBSITE_DOWN' THEN 4
                ELSE 5
            END,
            ticker
    """)
    
    results = cursor.fetchall()
    
    # Calculate statistics
    stats = {
        'total': len(results),
        'legitimate': sum(1 for r in results if r['verdict'] == 'LEGITIMATE'),
        'fake': sum(1 for r in results if r['verdict'] == 'FAKE'),
        'error': sum(1 for r in results if r['verdict'] in ['ERROR', 'WEBSITE_DOWN', 'NO_WEBSITE'])
    }
    
    conn.close()
    
    return render_template_string(
        HTML_TEMPLATE,
        results=results,
        stats=stats,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

if __name__ == '__main__':
    print("="*60)
    print("CA VERIFICATION RESULTS VIEWER")
    print("="*60)
    print("Starting server at http://localhost:5003")
    print("Press Ctrl+C to stop")
    print("="*60)
    app.run(debug=True, port=5003, host='0.0.0.0')
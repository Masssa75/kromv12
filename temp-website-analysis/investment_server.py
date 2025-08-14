#!/usr/bin/env python3
"""
Flask server for Investment Analysis UI
Serves the dashboard and provides API endpoints
"""

from flask import Flask, render_template_string, jsonify, send_file
import sqlite3
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect('analysis_results.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Serve the main UI"""
    try:
        with open('investment_ui.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "UI file not found. Please run the analyzer first.", 404

@app.route('/api/tokens')
def get_tokens():
    """API endpoint to get token data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, let's add the investment columns if they don't exist
    try:
        cursor.execute("""
            ALTER TABLE website_analysis ADD COLUMN investment_score INTEGER
        """)
        cursor.execute("""
            ALTER TABLE website_analysis ADD COLUMN investment_tier TEXT
        """)
        cursor.execute("""
            ALTER TABLE website_analysis ADD COLUMN investment_summary TEXT
        """)
        cursor.execute("""
            ALTER TABLE website_analysis ADD COLUMN investment_green_flags TEXT
        """)
        cursor.execute("""
            ALTER TABLE website_analysis ADD COLUMN investment_red_flags TEXT
        """)
        cursor.execute("""
            ALTER TABLE website_analysis ADD COLUMN investment_reasoning TEXT
        """)
        cursor.execute("""
            ALTER TABLE website_analysis ADD COLUMN investment_analyzed_at TEXT
        """)
        conn.commit()
    except sqlite3.OperationalError:
        # Columns already exist
        pass
    
    # Get all tokens ordered by website score
    cursor.execute("""
        SELECT 
            ticker,
            network,
            contract_address,
            website_url,
            website_score,
            website_tier,
            investment_score,
            investment_tier,
            investment_summary,
            investment_green_flags,
            investment_red_flags,
            investment_reasoning,
            investment_analyzed_at
        FROM website_analysis
        WHERE website_score IS NOT NULL
        ORDER BY 
            CASE WHEN investment_score IS NOT NULL THEN 0 ELSE 1 END,
            COALESCE(investment_score, website_score) DESC
        LIMIT 20
    """)
    
    tokens = []
    for row in cursor.fetchall():
        token = dict(row)
        tokens.append(token)
    
    conn.close()
    
    return jsonify({"tokens": tokens})

@app.route('/api/analyze/<ticker>')
def analyze_token(ticker):
    """Trigger analysis for a specific token"""
    from website_investment_analyzer import WebsiteInvestmentAnalyzer
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get token data
    cursor.execute("""
        SELECT ticker, contract_address, website_url
        FROM website_analysis
        WHERE ticker = ?
    """, (ticker,))
    
    token = cursor.fetchone()
    
    if not token:
        return jsonify({"error": "Token not found"}), 404
    
    # Run analysis
    analyzer = WebsiteInvestmentAnalyzer()
    result = analyzer.analyze_website(
        ticker=token['ticker'],
        contract=token['contract_address'],
        url=token['website_url']
    )
    
    if result['success']:
        analysis = result['analysis']
        
        # Update database
        cursor.execute("""
            UPDATE website_analysis
            SET investment_score = ?,
                investment_tier = ?,
                investment_summary = ?,
                investment_green_flags = ?,
                investment_red_flags = ?,
                investment_reasoning = ?,
                investment_analyzed_at = ?
            WHERE ticker = ?
        """, (
            analysis['investment_score'],
            analysis['tier'],
            analysis['project_summary'],
            json.dumps(analysis['green_flags']),
            json.dumps(analysis['red_flags']),
            analysis['reasoning'],
            result['analyzed_at'],
            ticker
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "analysis": analysis})
    else:
        conn.close()
        return jsonify({"error": result['error']}), 500

@app.route('/api/analyze-all')
def analyze_all():
    """Trigger analysis for top 20 tokens"""
    from website_investment_analyzer import WebsiteInvestmentAnalyzer
    
    analyzer = WebsiteInvestmentAnalyzer()
    results = analyzer.analyze_top_tokens(20)
    
    successful = len([r for r in results if r.get('success')])
    
    return jsonify({
        "success": True,
        "analyzed": successful,
        "total": len(results)
    })

if __name__ == '__main__':
    print("\n🚀 Starting Investment Analysis Server...")
    print("📊 Dashboard: http://localhost:5002")
    print("🔄 API: http://localhost:5002/api/tokens")
    print("🔬 Analyze All: http://localhost:5002/api/analyze-all")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
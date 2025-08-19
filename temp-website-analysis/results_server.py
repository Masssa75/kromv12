#!/usr/bin/env python3
"""
Flask server to display website analysis results
"""
from flask import Flask, jsonify, send_file, request
import sqlite3
import json

app = Flask(__name__)

@app.route('/')
def index():
    """Serve the HTML viewer"""
    return send_file('results_viewer.html')

@app.route('/api/results')
def get_results():
    """Get analysis results from database"""
    
    # Get filter parameter
    model_filter = request.args.get('model', 'all')
    
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Build query based on filter
    if model_filter == 'all':
        where_clause = "WHERE ar.score IS NOT NULL"
    else:
        where_clause = f"WHERE ar.score IS NOT NULL AND ar.model_used = '{model_filter}'"
    
    cursor.execute(f'''
        SELECT 
            ar.ticker,
            ar.website_url,
            ar.score,
            ar.tier,
            ar.reasoning,
            ar.legitimacy_indicators,
            ar.red_flags,
            ar.technical_depth,
            ar.team_transparency,
            t.liquidity_usd,
            ar.website_description,
            ar.model_used
        FROM analysis_results ar
        JOIN tokens t ON ar.token_id = t.id
        {where_clause}
        ORDER BY ar.score DESC, ar.id DESC
        LIMIT 20
    ''')
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'ticker': row[0],
            'website_url': row[1],
            'score': row[2],
            'tier': row[3],
            'reasoning': row[4],
            'legitimacy_indicators': json.loads(row[5]) if row[5] else [],
            'red_flags': json.loads(row[6]) if row[6] else [],
            'technical_depth': row[7],
            'team_transparency': row[8],
            'liquidity_usd': row[9],
            'website_description': row[10] if len(row) > 10 else None,
            'model_used': row[11] if len(row) > 11 else 'unknown'
        })
    
    conn.close()
    
    return jsonify(results)

@app.route('/api/models')
def get_models():
    """Get list of available AI models"""
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT model_used, COUNT(*) as count
        FROM analysis_results
        WHERE model_used IS NOT NULL AND score IS NOT NULL
        GROUP BY model_used
    ''')
    
    models = []
    for row in cursor.fetchall():
        models.append({
            'model': row[0],
            'count': row[1]
        })
    
    conn.close()
    return jsonify(models)

if __name__ == '__main__':
    print("\n✨ Starting Website Analysis Results Viewer")
    print("📍 Open http://localhost:5004 in your browser")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, port=5004)
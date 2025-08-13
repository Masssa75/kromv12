#!/usr/bin/env python3
"""
Simple Flask server to serve website analysis data from SQLite database
"""

from flask import Flask, jsonify, send_file
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect('analysis_results.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Serve the HTML viewer"""
    return send_file('viewer.html')

@app.route('/api/analysis')
def get_analysis():
    """Get all analysis results"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all analysis results
    cursor.execute('''
        SELECT * FROM website_analysis 
        ORDER BY website_score DESC
    ''')
    
    rows = cursor.fetchall()
    results = []
    
    for row in rows:
        result = dict(row)
        
        # Parse JSON fields
        if result.get('red_flags'):
            try:
                result['red_flags'] = json.loads(result['red_flags'])
            except:
                result['red_flags'] = []
                
        if result.get('green_flags'):
            try:
                result['green_flags'] = json.loads(result['green_flags'])
            except:
                result['green_flags'] = []
                
        if result.get('analysis_json'):
            try:
                full_analysis = json.loads(result['analysis_json'])
                # Add any missing fields from full analysis
                for key, value in full_analysis.items():
                    if key not in result or result[key] is None:
                        result[key] = value
            except:
                pass
        
        results.append(result)
    
    # Get statistics
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN website_tier = 'ALPHA' THEN 1 END) as alpha,
            COUNT(CASE WHEN website_tier = 'SOLID' THEN 1 END) as solid,
            COUNT(CASE WHEN website_tier = 'BASIC' THEN 1 END) as basic,
            COUNT(CASE WHEN website_tier = 'TRASH' THEN 1 END) as trash,
            COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as errors,
            AVG(website_score) as avg_score
        FROM website_analysis
    ''')
    
    stats_row = cursor.fetchone()
    stats = {
        'total': stats_row['total'],
        'alpha': stats_row['alpha'],
        'solid': stats_row['solid'],
        'basic': stats_row['basic'],
        'trash': stats_row['trash'],
        'errors': stats_row['errors'],
        'avg_score': round(stats_row['avg_score'], 2) if stats_row['avg_score'] else 0
    }
    
    conn.close()
    
    return jsonify({
        'results': results,
        'stats': stats,
        'last_updated': datetime.now().isoformat()
    })

@app.route('/api/stats')
def get_stats():
    """Get analysis statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN website_tier = 'ALPHA' THEN 1 END) as alpha,
            COUNT(CASE WHEN website_tier = 'SOLID' THEN 1 END) as solid,
            COUNT(CASE WHEN website_tier = 'BASIC' THEN 1 END) as basic,
            COUNT(CASE WHEN website_tier = 'TRASH' THEN 1 END) as trash,
            COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as errors,
            AVG(website_score) as avg_score,
            COUNT(CASE WHEN has_real_utility = 1 THEN 1 END) as with_utility,
            COUNT(CASE WHEN has_audit = 1 THEN 1 END) as audited,
            COUNT(CASE WHEN has_whitepaper = 1 THEN 1 END) as with_whitepaper,
            COUNT(CASE WHEN has_roadmap = 1 THEN 1 END) as with_roadmap,
            COUNT(CASE WHEN has_working_product = 1 THEN 1 END) as with_product
        FROM website_analysis
    ''')
    
    row = cursor.fetchone()
    
    stats = {
        'total': row['total'],
        'by_tier': {
            'alpha': row['alpha'],
            'solid': row['solid'],
            'basic': row['basic'],
            'trash': row['trash']
        },
        'errors': row['errors'],
        'avg_score': round(row['avg_score'], 2) if row['avg_score'] else 0,
        'with_utility': row['with_utility'],
        'audited': row['audited'],
        'with_whitepaper': row['with_whitepaper'],
        'with_roadmap': row['with_roadmap'],
        'with_product': row['with_product']
    }
    
    conn.close()
    
    return jsonify(stats)

if __name__ == '__main__':
    print("=" * 60)
    print("Website Analysis Viewer Server")
    print("=" * 60)
    print("Server running at: http://localhost:5000")
    print("Open this URL in your browser to view the results")
    print("-" * 60)
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, port=5000)
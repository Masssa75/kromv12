#!/usr/bin/env python3
"""
Simple API server for the visualization dashboard
Serves data from the SQLite database with all new columns
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
import threading
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Add request logging
@app.before_request
def log_request():
    logger.info(f"Incoming request: {request.method} {request.path}")
    logger.debug(f"Request args: {request.args}")

@app.after_request
def log_response(response):
    logger.info(f"Response status: {response.status}")
    return response

# Database lock for thread safety
db_lock = threading.Lock()
DB_PATH = "krom_calls.db"

def get_db_connection():
    """Get a database connection"""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    return sqlite3.connect(DB_PATH)

def dict_factory(cursor, row):
    """Convert sqlite row to dictionary"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.route('/api/stats')
def get_stats():
    """Get database statistics"""
    try:
        with db_lock:
            conn = get_db_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute("SELECT COUNT(*) as total_calls FROM krom_calls")
            total_calls = cursor.fetchone()['total_calls']
            
            cursor.execute("SELECT COUNT(*) as calls_with_raw_data FROM krom_calls WHERE raw_data IS NOT NULL AND raw_data != ''")
            calls_with_raw_data = cursor.fetchone()['calls_with_raw_data']
            
            cursor.execute("SELECT AVG(roi) as avg_roi FROM krom_calls WHERE roi IS NOT NULL AND roi > 0")
            avg_roi_result = cursor.fetchone()
            avg_roi = avg_roi_result['avg_roi'] if avg_roi_result['avg_roi'] else 0
            
            cursor.execute("SELECT COUNT(*) as profitable_calls FROM krom_calls WHERE roi > 1")
            profitable_calls = cursor.fetchone()['profitable_calls']
            
            cursor.execute("SELECT COUNT(DISTINCT network) as networks FROM krom_calls WHERE network IS NOT NULL")
            networks = cursor.fetchone()['networks']
            
            cursor.execute("SELECT COUNT(DISTINCT group_id) as groups FROM krom_calls WHERE group_id IS NOT NULL")
            groups = cursor.fetchone()['groups']
            
            # ROI distribution
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN roi >= 2 THEN 'High (2x+)'
                        WHEN roi >= 1.5 THEN 'Good (1.5-2x)'
                        WHEN roi >= 1 THEN 'Profit (1-1.5x)'
                        WHEN roi >= 0.5 THEN 'Loss (0.5-1x)'
                        ELSE 'Major Loss (<0.5x)'
                    END as roi_range,
                    COUNT(*) as count
                FROM krom_calls 
                WHERE roi IS NOT NULL 
                GROUP BY roi_range
            """)
            roi_distribution = cursor.fetchall()
            
            # Network distribution  
            cursor.execute("""
                SELECT network, COUNT(*) as count 
                FROM krom_calls 
                WHERE network IS NOT NULL 
                GROUP BY network 
                ORDER BY count DESC 
                LIMIT 10
            """)
            network_distribution = cursor.fetchall()
            
            conn.close()
            
            return jsonify({
                'total_calls': total_calls,
                'calls_with_raw_data': calls_with_raw_data,
                'avg_roi': round(avg_roi, 2) if avg_roi else 0,
                'profitable_calls': profitable_calls,
                'win_rate': round((profitable_calls / total_calls * 100), 1) if total_calls > 0 else 0,
                'networks': networks,
                'groups': groups,
                'roi_distribution': roi_distribution,
                'network_distribution': network_distribution
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calls')
def get_calls():
    """Get paginated calls with all new columns"""
    logger.info("=== GET /api/calls endpoint called ===")
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        search = request.args.get('search', '')
        
        logger.debug(f"Parameters: page={page}, per_page={per_page}, search='{search}'")
        
        offset = (page - 1) * per_page
        
        with db_lock:
            conn = get_db_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            # Base query with all columns
            base_query = """
                SELECT 
                    c.*,
                    g.name as group_name,
                    CASE 
                        WHEN c.timestamp IS NOT NULL THEN datetime(c.timestamp, 'unixepoch')
                        WHEN c.call_timestamp IS NOT NULL THEN c.call_timestamp
                        ELSE datetime(c.created_at)
                    END as formatted_date,
                    CASE 
                        WHEN c.buy_timestamp IS NOT NULL THEN datetime(c.buy_timestamp, 'unixepoch')
                        ELSE NULL
                    END as formatted_buy_time,
                    CASE 
                        WHEN c.top_timestamp IS NOT NULL THEN datetime(c.top_timestamp, 'unixepoch')
                        ELSE NULL
                    END as formatted_top_time
                FROM krom_calls c
                LEFT JOIN groups g ON c.group_id = g.group_id
            """
            
            # Add search filter if provided
            where_clause = ""
            params = []
            if search:
                where_clause = """
                    WHERE (c.ticker LIKE ? OR c.network LIKE ? OR g.name LIKE ? 
                    OR c.contract_address LIKE ? OR c.pair_address LIKE ?)
                """
                search_term = f"%{search}%"
                params = [search_term] * 5
            
            # Count total
            count_query = f"SELECT COUNT(*) as total FROM krom_calls c LEFT JOIN groups g ON c.group_id = g.group_id {where_clause}"
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']
            
            # Get paginated results
            full_query = f"{base_query} {where_clause} ORDER BY c.timestamp DESC LIMIT ? OFFSET ?"
            cursor.execute(full_query, params + [per_page, offset])
            calls = cursor.fetchall()
            
            conn.close()
            
            return jsonify({
                'data': calls,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/call/<call_id>/raw')
def get_call_raw_data(call_id):
    """Get raw JSON data for a specific call"""
    try:
        with db_lock:
            conn = get_db_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            cursor.execute("SELECT raw_data FROM krom_calls WHERE id = ?", (call_id,))
            result = cursor.fetchone()
            
            conn.close()
            
            if not result:
                return jsonify({'error': 'Call not found'}), 404
            
            if not result['raw_data']:
                return jsonify({'error': 'No raw data available for this call'}), 404
            
            try:
                raw_data = json.loads(result['raw_data'])
                return jsonify({'raw_data': raw_data})
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON data'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups')
def get_groups():
    """Get group statistics"""
    try:
        with db_lock:
            conn = get_db_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    g.*,
                    COUNT(c.id) as total_calls_in_db,
                    AVG(c.roi) as avg_roi_calculated,
                    COUNT(CASE WHEN c.roi > 1 THEN 1 END) as profitable_calls_calculated
                FROM groups g
                LEFT JOIN krom_calls c ON g.group_id = c.group_id
                GROUP BY g.id
                ORDER BY g.win_rate_30d DESC
            """)
            groups = cursor.fetchall()
            
            conn.close()
            
            return jsonify({'data': groups})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    """Redirect to dashboard"""
    return send_file('krom-analysis-viz.html')

if __name__ == '__main__':
    print("🚀 Starting Dashboard API Server...")
    print(f"📊 Dashboard: http://localhost:8001/krom-analysis-viz.html")
    print(f"🔗 API Base: http://localhost:8001/api/")
    print(f"📁 Database: {DB_PATH}")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        print("Please run the database setup script first")
        exit(1)
    
    # Test database connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM krom_calls")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Database connected - {count:,} calls found")
    except Exception as e:
        print(f"❌ Database error: {e}")
        exit(1)
    
    print("\nPress Ctrl+C to stop")
    app.run(host='0.0.0.0', port=8001, debug=True)
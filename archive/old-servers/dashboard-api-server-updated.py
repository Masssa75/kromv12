#!/usr/bin/env python3
"""
Dashboard API server - Updated to use group_name directly from krom_calls table
Serves both the HTML interface and API endpoints for the KROM dashboard
"""

import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import logging
import threading

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.')
CORS(app)

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "krom_calls.db")
db_lock = threading.Lock()

def dict_factory(cursor, row):
    """Convert database rows to dictionaries"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db_connection():
    """Get a database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Serve HTML files
@app.route('/')
def index():
    return send_from_directory('.', 'krom-analysis-viz.html')

@app.route('/<path:path>')
def serve_static(path):
    if path.endswith('.html') or path.endswith('.js') or path.endswith('.css'):
        return send_from_directory('.', path)
    return "Not found", 404

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
            
            # Updated to use group_name instead of group_id
            cursor.execute("SELECT COUNT(DISTINCT group_name) as groups FROM krom_calls WHERE group_name IS NOT NULL")
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
            
            # Simplified query - no more JOIN needed!
            base_query = """
                SELECT 
                    c.*,
                    CASE 
                        WHEN c.timestamp IS NOT NULL THEN datetime(c.timestamp, 'unixepoch')
                        ELSE c.call_timestamp 
                    END as formatted_timestamp,
                    CASE 
                        WHEN c.buy_timestamp IS NOT NULL THEN datetime(c.buy_timestamp / 1000, 'unixepoch')
                        ELSE NULL 
                    END as formatted_buy_timestamp,
                    CASE 
                        WHEN c.top_timestamp IS NOT NULL THEN datetime(c.top_timestamp / 1000, 'unixepoch')
                        ELSE NULL 
                    END as formatted_top_timestamp
                FROM krom_calls c
            """
            
            where_clause = ""
            params = []
            
            if search:
                where_clause = "WHERE c.ticker LIKE ? OR c.name LIKE ? OR c.message LIKE ? OR c.group_name LIKE ?"
                search_param = f"%{search}%"
                params = [search_param, search_param, search_param, search_param]
            
            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM krom_calls c {where_clause}"
            if params:
                cursor.execute(count_query, params)
            else:
                cursor.execute(count_query)
            total = cursor.fetchone()['total']
            
            # Get paginated results
            query = f"{base_query} {where_clause} ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
            params.extend([per_page, offset])
            
            cursor.execute(query, params)
            calls = cursor.fetchall()
            
            logger.info(f"Found {len(calls)} calls out of {total} total")
            
            # Log sample data for debugging
            if calls and len(calls) > 0:
                sample = calls[0]
                logger.debug(f"Sample call - id: {sample.get('id')}, group_name: {sample.get('group_name')}")
            
            conn.close()
            
            return jsonify({
                'calls': calls,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            })
            
    except Exception as e:
        logger.error(f"Error in get_calls: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/raw/<call_id>')
def get_raw_data(call_id):
    """Get raw JSON data for a specific call"""
    logger.info(f"=== GET /api/raw/{call_id} endpoint called ===")
    
    try:
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT raw_data FROM krom_calls WHERE id = ?", (call_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Call not found: {call_id}")
                return jsonify({'error': 'Call not found'}), 404
                
            raw_data = result[0]
            
            if not raw_data:
                logger.warning(f"No raw data for call: {call_id}")
                return jsonify({'error': 'No raw data available'}), 404
            
            try:
                # Parse and return the JSON
                data = json.loads(raw_data)
                logger.info(f"Successfully loaded raw data for call {call_id}")
                return jsonify(data)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in raw_data for call {call_id}")
                return jsonify({'error': 'Invalid JSON data'}), 500
                
            conn.close()
            
    except Exception as e:
        logger.error(f"Error getting raw data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups')
def get_groups():
    """Get list of all groups with statistics"""
    try:
        with db_lock:
            conn = get_db_connection()
            conn.row_factory = dict_factory
            cursor = conn.cursor()
            
            # Get groups directly from krom_calls table
            cursor.execute("""
                SELECT 
                    group_name,
                    COUNT(*) as total_calls,
                    AVG(roi) as avg_roi,
                    COUNT(CASE WHEN roi > 1 THEN 1 END) as profitable_calls,
                    MIN(call_timestamp) as first_call,
                    MAX(call_timestamp) as last_call
                FROM krom_calls
                WHERE group_name IS NOT NULL
                GROUP BY group_name
                ORDER BY total_calls DESC
                LIMIT 100
            """)
            
            groups = cursor.fetchall()
            
            # Calculate win rate for each group
            for group in groups:
                if group['total_calls'] > 0:
                    group['win_rate'] = round((group['profitable_calls'] / group['total_calls'] * 100), 1)
                else:
                    group['win_rate'] = 0
                
                if group['avg_roi']:
                    group['avg_roi'] = round(group['avg_roi'], 2)
                else:
                    group['avg_roi'] = 0
            
            conn.close()
            
            return jsonify({
                'groups': groups,
                'total': len(groups)
            })
            
    except Exception as e:
        logger.error(f"Error in get_groups: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test')
def test():
    """Test endpoint to verify server is running"""
    return jsonify({
        'status': 'ok',
        'message': 'Dashboard API server is running',
        'endpoints': [
            '/api/stats',
            '/api/calls',
            '/api/raw/<call_id>',
            '/api/groups'
        ]
    })

if __name__ == '__main__':
    print("=" * 60)
    print("KROM Dashboard API Server - Simplified Group Storage")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print("Starting server on http://localhost:8000")
    print("\nAvailable endpoints:")
    print("  - http://localhost:8000/ (Dashboard)")
    print("  - http://localhost:8000/api/stats")
    print("  - http://localhost:8000/api/calls")
    print("  - http://localhost:8000/api/raw/<call_id>")
    print("  - http://localhost:8000/api/groups")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8000, debug=True)
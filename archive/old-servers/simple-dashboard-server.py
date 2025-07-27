#!/usr/bin/env python3
"""
Simple dashboard API server for the new single-table database structure
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

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
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Basic stats
        cursor.execute("SELECT COUNT(*) as total_calls FROM calls")
        total_calls = cursor.fetchone()['total_calls']
        
        cursor.execute("SELECT COUNT(*) as calls_with_raw_data FROM calls WHERE raw_data IS NOT NULL")
        calls_with_raw_data = cursor.fetchone()['calls_with_raw_data']
        
        cursor.execute("SELECT AVG(roi) as avg_roi FROM calls WHERE roi IS NOT NULL AND roi > 0")
        avg_roi_result = cursor.fetchone()
        avg_roi = avg_roi_result['avg_roi'] if avg_roi_result['avg_roi'] else 0
        
        cursor.execute("SELECT COUNT(*) as profitable_calls FROM calls WHERE roi > 1")
        profitable_calls = cursor.fetchone()['profitable_calls']
        
        cursor.execute("SELECT COUNT(DISTINCT network) as networks FROM calls WHERE network IS NOT NULL")
        networks = cursor.fetchone()['networks']
        
        cursor.execute("SELECT COUNT(DISTINCT group_name) as groups FROM calls WHERE group_name IS NOT NULL")
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
            FROM calls 
            WHERE roi IS NOT NULL 
            GROUP BY roi_range
        """)
        roi_distribution = cursor.fetchall()
        
        # Network distribution  
        cursor.execute("""
            SELECT network, COUNT(*) as count 
            FROM calls 
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
            'networks': networks,
            'groups': groups,
            'roi_distribution': roi_distribution,
            'network_distribution': network_distribution
        })
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/calls')
def get_calls():
    """Get paginated calls"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        sort_by = request.args.get('sort_by', 'timestamp')
        sort_order = request.args.get('sort_order', 'desc')
        search = request.args.get('search', '')
        
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Build query
        where_clause = ""
        params = []
        
        if search:
            where_clause = """
                WHERE (symbol LIKE ? OR network LIKE ? OR group_name LIKE ? 
                OR contract_address LIKE ? OR pair_address LIKE ?)
            """
            search_term = f"%{search}%"
            params = [search_term] * 5
        
        # Count total
        count_query = f"SELECT COUNT(*) as total FROM calls {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get paginated results
        order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
        query = f"""
            SELECT *,
                datetime(timestamp, 'unixepoch') as formatted_date,
                datetime(buy_timestamp, 'unixepoch') as formatted_buy_time,
                datetime(top_timestamp, 'unixepoch') as formatted_top_time
            FROM calls 
            {where_clause} 
            {order_clause} 
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, params + [per_page, offset])
        calls = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': calls,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        logger.error(f"Calls error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/call/<call_id>/raw')
def get_call_raw_data(call_id):
    """Get raw JSON data for a specific call"""
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute("SELECT raw_data FROM calls WHERE id = ?", (call_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if not result:
            return jsonify({'error': 'Call not found'}), 404
        
        if not result['raw_data']:
            return jsonify({'error': 'No raw data available'}), 404
        
        # Parse and return the raw JSON
        try:
            raw_json = json.loads(result['raw_data'])
            return jsonify(raw_json)
        except:
            return jsonify({'error': 'Invalid JSON data'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups')
def get_groups():
    """Get group statistics"""
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                group_name,
                COUNT(*) as total_calls,
                AVG(roi) as avg_roi,
                COUNT(CASE WHEN roi > 1 THEN 1 END) as profitable_calls,
                MIN(timestamp) as first_call,
                MAX(timestamp) as last_call
            FROM calls
            WHERE group_name IS NOT NULL
            GROUP BY group_name
            ORDER BY total_calls DESC
        """)
        groups = cursor.fetchall()
        
        conn.close()
        
        return jsonify({'success': True, 'data': groups})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/')
def home():
    """Serve the dashboard HTML"""
    return send_file('simple-dashboard.html')

if __name__ == '__main__':
    print("🚀 Starting Simple Dashboard Server...")
    print(f"📊 Dashboard: http://localhost:8001/")
    print(f"🔗 API Base: http://localhost:8001/api/")
    print(f"📁 Database: {DB_PATH}")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        print("Please run: python3 download-krom-simple.py")
        exit(1)
    
    # Test database connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM calls")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"✅ Database connected - {count:,} calls found")
    except Exception as e:
        print(f"❌ Database error: {e}")
        exit(1)
    
    print("\nPress Ctrl+C to stop")
    app.run(host='0.0.0.0', port=8001, debug=True)
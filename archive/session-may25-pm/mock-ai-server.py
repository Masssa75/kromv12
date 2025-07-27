#!/usr/bin/env python3
"""
Mock AI server for testing when API limits are reached
Provides pre-programmed responses for common visualization requests
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import random

app = Flask(__name__)
CORS(app)

# Pre-defined responses for different queries
MOCK_RESPONSES = {
    "roi": {
        "response": "I'll analyze the ROI patterns in your KROM calls data.",
        "tool_calls": [{
            "tool": "create_chart",
            "params": {
                "query": "SELECT network, AVG(roi) as avg_roi FROM calls WHERE roi IS NOT NULL GROUP BY network ORDER BY avg_roi DESC LIMIT 10",
                "chart_type": "bar",
                "title": "Average ROI by Network"
            }
        }]
    },
    "group": {
        "response": "Let me show you the performance by group.",
        "tool_calls": [{
            "tool": "create_chart",
            "params": {
                "query": "SELECT group_name, COUNT(*) as call_count FROM calls GROUP BY group_name ORDER BY call_count DESC LIMIT 10",
                "chart_type": "bar",
                "title": "Top 10 Groups by Call Volume"
            }
        }]
    },
    "time": {
        "response": "I'll analyze the time-based patterns.",
        "tool_calls": [{
            "tool": "execute_analysis",
            "params": {
                "code": """conn = get_db_connection()
df = pd.read_sql("SELECT DATE(datetime(buy_timestamp, 'unixepoch')) as date, COUNT(*) as calls FROM calls WHERE buy_timestamp > 0 GROUP BY date ORDER BY date DESC LIMIT 30", conn)
result = {'labels': df['date'].tolist(), 'values': df['calls'].tolist()}""",
                "visualization_type": "line",
                "title": "Daily Call Volume (Last 30 Days)"
            }
        }]
    },
    "win": {
        "response": "Let me calculate win rates across different dimensions.",
        "tool_calls": [{
            "tool": "create_chart", 
            "params": {
                "query": "SELECT network, CAST(SUM(CASE WHEN roi > 0 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as win_rate FROM calls WHERE roi IS NOT NULL GROUP BY network",
                "chart_type": "bar",
                "title": "Win Rate by Network (%)"
            }
        }]
    },
    "scatter": {
        "response": "I'll create a scatter plot analysis for you.",
        "tool_calls": [{
            "tool": "execute_analysis",
            "params": {
                "code": """conn = get_db_connection()
df = pd.read_sql("SELECT (top_timestamp - buy_timestamp)/3600.0 as hours_held, roi FROM calls WHERE roi > -90 AND roi < 1000 AND top_timestamp > buy_timestamp LIMIT 1000", conn)
result = {'x': df['hours_held'].tolist(), 'y': df['roi'].tolist(), 'labels': ['Call ' + str(i) for i in range(len(df))]}""",
                "visualization_type": "scatter",
                "title": "ROI vs Holding Time (Hours)"
            }
        }]
    }
}

def get_mock_response(message):
    """Generate a mock AI response based on the message"""
    message_lower = message.lower()
    
    # Check for keywords and return appropriate response
    if "roi" in message_lower or "return" in message_lower:
        return MOCK_RESPONSES["roi"]
    elif "group" in message_lower or "volume" in message_lower:
        return MOCK_RESPONSES["group"]
    elif "time" in message_lower or "daily" in message_lower or "trend" in message_lower:
        return MOCK_RESPONSES["time"]
    elif "win" in message_lower or "success" in message_lower:
        return MOCK_RESPONSES["win"]
    elif "scatter" in message_lower or "correlation" in message_lower:
        return MOCK_RESPONSES["scatter"]
    else:
        # Default response with random selection
        return random.choice(list(MOCK_RESPONSES.values()))

@app.route('/api/mock-chat', methods=['POST'])
def mock_chat():
    """Mock chat endpoint that returns pre-programmed responses"""
    data = request.json
    message = data.get('message', '')
    
    # Get appropriate mock response
    mock_data = get_mock_response(message)
    
    # Format response to match real API
    response = {
        "response": mock_data["response"],
        "tools_used": [call["tool"] for call in mock_data["tool_calls"]]
    }
    
    # Add tool calls to response for processing
    response["mock_tool_calls"] = mock_data["tool_calls"]
    
    return jsonify(response)

@app.route('/api/mock-tools', methods=['GET'])
def list_mock_patterns():
    """List available mock patterns"""
    return jsonify({
        "patterns": {
            "roi": "Analyze ROI patterns",
            "group": "Show group performance", 
            "time": "Time-based analysis",
            "win": "Win rate analysis",
            "scatter": "Correlation scatter plots"
        },
        "example_queries": [
            "Show me ROI by network",
            "What are the top performing groups?",
            "Show daily trends",
            "Calculate win rates",
            "Create a scatter plot of ROI vs time"
        ]
    })

if __name__ == '__main__':
    print("\n🤖 Mock AI Server Running!")
    print("This provides pre-programmed responses for testing")
    print("Available patterns: roi, group, time, win, scatter")
    print("\nRunning on http://localhost:5002")
    app.run(port=5002, debug=True)
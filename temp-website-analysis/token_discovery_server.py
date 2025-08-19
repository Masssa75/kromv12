#!/usr/bin/env python3
"""
Simple server to view token_discovery website analysis results on port 5007
"""

from flask import Flask, render_template_string
import sqlite3
import json

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Token Discovery Website Analysis</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .stats { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; }
        tr:hover { background-color: #f5f5f5; }
        .high-score { background-color: #e8f5e9; }
        .stage2 { color: #4CAF50; font-weight: bold; }
        .url { color: #1976d2; text-decoration: none; }
        .url:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>Token Discovery Website Analysis Results</h1>
    
    <div class="stats">
        <h2>Statistics</h2>
        <p>Total Analyzed: {{ total }}</p>
        <p>Stage 2 Recommended: {{ stage2_count }} ({{ stage2_pct }}%)</p>
        <p>High Scorers (≥10/21): {{ high_scorers }}</p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>Symbol</th>
                <th>Score</th>
                <th>Stage 2</th>
                <th>Website</th>
                <th>Categories</th>
            </tr>
        </thead>
        <tbody>
            {% for row in rows %}
            <tr class="{% if row.total_score >= 10 %}high-score{% endif %}">
                <td>{{ loop.index }}</td>
                <td><strong>{{ row.ticker }}</strong></td>
                <td>{{ row.total_score }}/21</td>
                <td>{% if row.proceed_to_stage_2 %}<span class="stage2">YES</span>{% else %}NO{% endif %}</td>
                <td><a href="{{ row.url }}" target="_blank" class="url">{{ row.url[:50] }}...</a></td>
                <td>
                    {% if row.category_scores %}
                        {% if row.category_scores is mapping %}
                            {% for cat, score in row.category_scores.items() %}
                                {{ cat[:4] }}:{{ score }}
                            {% endfor %}
                        {% elif row.category_scores is sequence %}
                            {{ row.category_scores | join(', ') }}
                        {% endif %}
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""

@app.route('/')
def index():
    conn = sqlite3.connect('token_discovery_analysis.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all results
    cursor.execute("""
        SELECT ticker, url, total_score, proceed_to_stage_2, 
               category_scores
        FROM website_analysis 
        ORDER BY total_score DESC, ticker
    """)
    rows = cursor.fetchall()
    
    # Convert rows to dicts and parse JSON
    results = []
    for row in rows:
        result = dict(row)
        try:
            scores = json.loads(row['category_scores']) if row['category_scores'] else []
            if isinstance(scores, list):
                # Convert list to readable format
                categories = ['Proj', 'Team', 'Docs', 'Comm', 'Part', 'Tech', 'Token']
                result['category_scores'] = [f"{cat}:{score}" for cat, score in zip(categories, scores)]
            else:
                result['category_scores'] = scores
        except:
            result['category_scores'] = []
        results.append(result)
    
    # Calculate stats
    total = len(results)
    stage2_count = sum(1 for r in results if r['proceed_to_stage_2'])
    high_scorers = sum(1 for r in results if r['total_score'] >= 10)
    
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, 
                                 rows=results,
                                 total=total,
                                 stage2_count=stage2_count,
                                 stage2_pct=round(stage2_count/total*100) if total > 0 else 0,
                                 high_scorers=high_scorers)

if __name__ == '__main__':
    print("Starting Token Discovery Analysis Server on http://localhost:5007")
    app.run(debug=True, port=5007)
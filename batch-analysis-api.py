#!/usr/bin/env python3
"""
Flask API for batch analysis - NO MOCK DATA
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import csv
import io
from datetime import datetime
from supabase import create_client
from anthropic import Anthropic
import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize clients
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Configure Gemini
gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key and '\n' in gemini_key:
    gemini_key = gemini_key.strip().split('\n')[-1]
if gemini_key:
    genai.configure(api_key=gemini_key)
    gemini = genai.GenerativeModel('gemini-pro')
else:
    gemini = None

# Store results for CSV download
last_analysis_results = []

@app.route('/analyze', methods=['POST'])
def analyze():
    """Run analysis on oldest calls"""
    global last_analysis_results
    
    try:
        data = request.json
        limit = data.get('limit', 5)
        model = data.get('model', 'claude-3-haiku-20240307')
        
        start_time = time.time()
        
        # Fetch oldest calls from Supabase
        result = supabase.table('crypto_calls') \
            .select('*') \
            .not_.is_('raw_data', 'null') \
            .order('buy_timestamp', desc=False) \
            .limit(limit) \
            .execute()
        
        if not result.data:
            return jsonify({'error': 'No calls found in database'}), 404
        
        # Analyze each call
        results = []
        for call in result.data:
            analysis_result = analyze_call(call, model)
            if analysis_result:
                results.append(analysis_result)
        
        duration = round(time.time() - start_time, 1)
        
        # Store for CSV download
        last_analysis_results = results
        
        return jsonify({
            'count': len(results),
            'model': model,
            'duration': duration,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_call(call, model):
    """Analyze a single call"""
    try:
        ticker = call.get('ticker', 'Unknown')
        raw_data = call.get('raw_data', {})
        message = raw_data.get('text', 'No message')
        group = raw_data.get('group', {}).get('name', 'Unknown')
        contract = raw_data.get('contract_address') or raw_data.get('pair_address')
        
        # Create prompt
        prompt = f"""Analyze this crypto call for legitimacy.

Token: {ticker}
Group: {group}
Message: {message[:500]}

Score 1-10 (1-3: shitcoin, 4-7: some legitimacy, 8-10: major backing like Binance/Google)

Respond with JSON only:
{{
  "score": <number>,
  "legitimacy_factor": "<1-6 words>",
  "explanation": "<brief>"
}}"""

        # Call AI based on model
        if model.startswith('claude'):
            result = analyze_with_claude(prompt, model)
        elif model == 'gemini-pro' and gemini:
            result = analyze_with_gemini(prompt)
        else:
            return None
        
        if result:
            score = result.get('score', 1)
            
            # Update database
            update_data = {
                'analysis_score': score,
                'analysis_model': model,
                'analysis_legitimacy_factor': result.get('legitimacy_factor', ''),
                'analysis_tier': get_tier(score),
                'analysis_description': result.get('explanation', ''),
                'analysis_reanalyzed_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            supabase.table('crypto_calls') \
                .update(update_data) \
                .eq('krom_id', call['krom_id']) \
                .execute()
            
            return {
                'token': ticker,
                'contract': contract,
                'score': score,
                'tier': get_tier(score),
                'legitimacy_factor': result.get('legitimacy_factor', ''),
                'explanation': result.get('explanation', ''),
                'date': call.get('buy_timestamp', ''),
                'roi_24h': raw_data.get('roi_24h', 0)
            }
    
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None

def analyze_with_claude(prompt, model):
    """Use Claude for analysis"""
    try:
        response = anthropic.messages.create(
            model=model,
            max_tokens=300,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
        return json.loads(content)
        
    except Exception as e:
        print(f"Claude error: {e}")
        return None

def analyze_with_gemini(prompt):
    """Use Gemini for analysis"""
    try:
        response = gemini.generate_content(prompt)
        content = response.text
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
        return json.loads(content)
        
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

def get_tier(score):
    """Convert score to tier"""
    if score >= 8:
        return 'ALPHA'
    elif score >= 6:
        return 'SOLID'
    elif score >= 4:
        return 'BASIC'
    else:
        return 'TRASH'

@app.route('/download-csv', methods=['GET'])
def download_csv():
    """Download last analysis results as CSV"""
    if not last_analysis_results:
        return jsonify({'error': 'No analysis results to download'}), 404
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'token', 'contract', 'score', 'tier', 'legitimacy_factor', 
        'explanation', 'date', 'roi_24h'
    ])
    
    writer.writeheader()
    writer.writerows(last_analysis_results)
    
    # Convert to bytes
    output.seek(0)
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    
    return send_file(
        mem,
        as_attachment=True,
        download_name=f'krom_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
        mimetype='text/csv'
    )

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("KROM Batch Analysis API")
    print("=" * 50)
    print("Endpoints:")
    print("  POST /analyze - Run batch analysis")
    print("  GET /download-csv - Download results as CSV")
    print("  GET /health - Health check")
    print("=" * 50)
    print("Starting server on http://localhost:5000")
    
    app.run(debug=True, port=5000)
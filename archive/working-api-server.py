#!/usr/bin/env python3
"""
Working API Server for KROM Crypto Analysis
"""

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import json
import os
from datetime import datetime
import aiohttp
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Read HTML content
try:
    with open('crypto-web-interface.html', 'r') as f:
        HTML_CONTENT = f.read()
except:
    HTML_CONTENT = "<h1>Error loading interface</h1>"

# Use synchronous requests instead of async for simplicity
def get_crypto_price_sync(symbol):
    """Get crypto price using CoinMarketCap API"""
    cmc_key = os.getenv("COINMARKETCAP_API_KEY")
    
    if cmc_key:
        try:
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            headers = {
                'X-CMC_PRO_API_KEY': cmc_key,
                'Accept': 'application/json'
            }
            params = {
                'symbol': symbol.upper(),
                'convert': 'USD'
            }
            
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['status']['error_code'] == 0:
                    crypto_data = data['data'][symbol.upper()]
                    quote = crypto_data['quote']['USD']
                    return {
                        "symbol": symbol.upper(),
                        "name": crypto_data['name'],
                        "price": round(quote['price'], 2 if quote['price'] > 1 else 6),
                        "market_cap": quote['market_cap'],
                        "24h_volume": quote['volume_24h'],
                        "24h_change": round(quote['percent_change_24h'], 2),
                        "1h_change": round(quote['percent_change_1h'], 2),
                        "7d_change": round(quote['percent_change_7d'], 2),
                        "market_cap_rank": crypto_data['cmc_rank'],
                        "last_updated": quote['last_updated'],
                        "source": "CoinMarketCap"
                    }
        except Exception as e:
            print(f"CMC Error: {e}")
    
    # Fallback to CoinGecko
    try:
        symbol_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
            "SOL": "solana", "ADA": "cardano", "XRP": "ripple"
        }
        coin_id = symbol_map.get(symbol.upper(), symbol.lower())
        
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }
        
        response = requests.get(url, params=params, verify=False)  # Skip SSL for now
        data = response.json()
        
        if coin_id in data:
            return {
                "symbol": symbol.upper(),
                "price": data[coin_id]["usd"],
                "market_cap": data[coin_id]["usd_market_cap"],
                "24h_volume": data[coin_id]["usd_24h_vol"],
                "24h_change": round(data[coin_id]["usd_24h_change"], 2),
                "source": "CoinGecko"
            }
    except Exception as e:
        print(f"CoinGecko Error: {e}")
    
    return {"error": f"Could not fetch price for {symbol}"}

def get_market_sentiment_sync():
    """Get Fear & Greed Index"""
    try:
        response = requests.get("https://api.alternative.me/fng/", verify=False)
        data = response.json()
        current = data["data"][0]
        value = int(current["value"])
        
        # Sentiment analysis
        if value <= 25:
            analysis = "Extreme Fear - Potential buying opportunity"
            emoji = "😱"
        elif value <= 45:
            analysis = "Fear - Market is fearful"
            emoji = "😨"
        elif value <= 55:
            analysis = "Neutral - Market is balanced"
            emoji = "😐"
        elif value <= 75:
            analysis = "Greed - Market is getting greedy"
            emoji = "😊"
        else:
            analysis = "Extreme Greed - High risk of correction"
            emoji = "🤑"
        
        return {
            "value": value,
            "classification": current["value_classification"],
            "timestamp": current["timestamp"],
            "analysis": analysis,
            "emoji": emoji
        }
    except Exception as e:
        return {"error": str(e)}

def get_crypto_news_sync(query):
    """Get crypto news"""
    api_key = os.getenv("NEWS_API_KEY")
    articles = []
    
    if api_key:
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": f"{query} cryptocurrency crypto",
                "apiKey": api_key,
                "sortBy": "publishedAt",
                "pageSize": 5,
                "language": "en"
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "ok":
                for article in data["articles"][:5]:
                    articles.append({
                        "title": article["title"],
                        "source": article["source"]["name"],
                        "published": article["publishedAt"],
                        "url": article["url"],
                        "description": (article.get("description") or "")[:200]
                    })
        except Exception as e:
            print(f"NewsAPI Error: {e}")
    
    return {"query": query, "articles": articles}

# Portfolio storage
portfolio = {}

@app.route('/')
def index():
    return Response(HTML_CONTENT, mimetype='text/html')

@app.route('/api/price/<symbol>')
def get_price(symbol):
    result = get_crypto_price_sync(symbol)
    return jsonify(result)

@app.route('/api/sentiment')
def get_sentiment():
    result = get_market_sentiment_sync()
    return jsonify(result)

@app.route('/api/news/<query>')
def get_news(query):
    result = get_crypto_news_sync(query)
    return jsonify(result)

@app.route('/api/trending')
def get_trending():
    # Simplified trending
    return jsonify({
        "trending": [
            {"symbol": "BTC", "name": "Bitcoin"},
            {"symbol": "ETH", "name": "Ethereum"},
            {"symbol": "SOL", "name": "Solana"}
        ]
    })

@app.route('/api/portfolio')
def check_portfolio():
    return jsonify({"portfolio": list(portfolio.values()), "total_value": 0})

@app.route('/api/portfolio/add', methods=['POST'])
def add_to_portfolio():
    data = request.json
    symbol = data['symbol'].upper()
    portfolio[symbol] = {
        "symbol": symbol,
        "quantity": data['quantity'],
        "entry_price": data['entry_price'],
        "total_cost": data['quantity'] * data['entry_price']
    }
    return jsonify({"success": True, **portfolio[symbol]})

@app.route('/api/compare', methods=['POST'])
def compare_cryptos():
    symbols = request.json.get('symbols', [])
    comparisons = []
    for symbol in symbols:
        price_data = get_crypto_price_sync(symbol)
        if "error" not in price_data:
            comparisons.append(price_data)
    return jsonify({"comparisons": comparisons})

@app.route('/api/position-size', methods=['POST'])
def calculate_position():
    data = request.json
    account_size = data['account_size']
    risk_percentage = data['risk_percentage']
    entry_price = data['entry_price']
    stop_loss = data['stop_loss']
    
    risk_amount = account_size * (risk_percentage / 100)
    price_diff = abs(entry_price - stop_loss)
    position_size = risk_amount / price_diff
    position_value = position_size * entry_price
    
    return jsonify({
        "position_size": round(position_size, 6),
        "position_value": round(position_value, 2),
        "risk_amount": round(risk_amount, 2),
        "stop_loss_percentage": round((price_diff / entry_price) * 100, 2),
        "leverage_required": round(position_value / account_size, 2) if position_value > account_size else 1,
        "risk_reward_ratios": {
            "1:1": round(entry_price + price_diff, 2),
            "1:2": round(entry_price + (price_diff * 2), 2),
            "1:3": round(entry_price + (price_diff * 3), 2)
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI chat endpoint that interprets user queries and uses appropriate tools"""
    try:
        data = request.json
        user_message = data.get('message', '').lower()
        
        # Debug: Print what we received
        print(f"Received message: '{user_message}'")
        
        # Parse the user's intent and call appropriate functions
        response = ""
        
        # Check for price queries
        price_keywords = ['price', 'cost', 'worth', 'value', 'trading at', 'how much']
        crypto_symbols = ['btc', 'bitcoin', 'eth', 'ethereum', 'bnb', 'sol', 'solana', 'ada', 'cardano', 'doge', 'dogecoin', 'xrp', 'ripple', 'api', 'apis']
        
        # Special check for "which apis" question
        if 'which api' in user_message or 'what api' in user_message:
            response = """I'm currently connected to these APIs:

🔹 <strong>CoinMarketCap API</strong> - Real-time crypto prices and market data
🔹 <strong>CoinGecko API</strong> - Backup price data source  
🔹 <strong>NewsAPI</strong> - Latest cryptocurrency news
🔹 <strong>Fear & Greed Index API</strong> - Market sentiment analysis
🔹 <strong>CryptoPanic API</strong> - Ready for crypto-specific news (API key needed)
🔹 <strong>Etherscan API</strong> - Ready for whale tracking (coming soon)

All these APIs work together to provide you with comprehensive crypto analysis!"""
        
        elif any(keyword in user_message for keyword in price_keywords):
            # Extract crypto symbol
            symbol = None
            for crypto in crypto_symbols:
                if crypto in user_message:
                    # Map common names to symbols
                    symbol_map = {
                        'bitcoin': 'BTC',
                        'ethereum': 'ETH',
                        'solana': 'SOL',
                        'cardano': 'ADA',
                        'dogecoin': 'DOGE',
                        'ripple': 'XRP'
                    }
                    symbol = symbol_map.get(crypto, crypto.upper())
                    break
            
            if symbol:
                price_data = get_crypto_price_sync(symbol)
                if 'error' not in price_data:
                    response = f"📊 <strong>{price_data['name']} ({price_data['symbol']})</strong><br><br>"
                    response += f"💰 Price: ${price_data['price']:,.2f}<br>"
                    response += f"📈 24h Change: {price_data['24h_change']:+.2f}%<br>"
                    if '1h_change' in price_data:
                        response += f"⏰ 1h Change: {price_data['1h_change']:+.2f}%<br>"
                    if '7d_change' in price_data:
                        response += f"📅 7d Change: {price_data['7d_change']:+.2f}%<br>"
                    response += f"💎 Market Cap: ${price_data['market_cap']/1e9:.2f}B<br>"
                    response += f"📊 24h Volume: ${price_data['24h_volume']/1e6:.2f}M"
                    if 'market_cap_rank' in price_data:
                        response += f"<br>🏆 Rank: #{price_data['market_cap_rank']}"
                else:
                    response = f"Sorry, I couldn't fetch the price for {symbol}. Please try again."
            else:
                response = "I can help you check crypto prices! Please specify which cryptocurrency you'd like to know about. For example: 'What's the price of Bitcoin?' or 'How much is ETH?'"
        
        # Check for sentiment queries
        elif any(keyword in user_message for keyword in ['sentiment', 'fear', 'greed', 'mood', 'feeling', 'market sentiment']):
            sentiment_data = get_market_sentiment()
            if 'error' not in sentiment_data:
                response = f"🎭 <strong>Market Sentiment Analysis</strong><br><br>"
                response += f"Fear & Greed Index: <strong>{sentiment_data['value']}</strong><br>"
                response += f"Classification: <strong>{sentiment_data['classification']}</strong><br><br>"
                response += f"📊 {sentiment_data['description']}"
            else:
                response = "Sorry, I couldn't fetch the market sentiment data. Please try again later."
        
        # Check for news queries
        elif any(keyword in user_message for keyword in ['news', 'latest', 'happening', 'update', 'headlines']):
            # Extract specific crypto if mentioned
            query = "cryptocurrency"
            for crypto in crypto_symbols:
                if crypto in user_message:
                    query = crypto
                    break
            
            news_data = get_crypto_news(query)
            if 'error' not in news_data and news_data['articles']:
                response = f"📰 <strong>Latest Crypto News</strong><br><br>"
                for i, article in enumerate(news_data['articles'][:5], 1):
                    response += f"{i}. <strong>{article['title']}</strong><br>"
                    response += f"   {article['description']}<br>"
                    response += f"   <small>Source: {article['source']['name']}</small><br><br>"
            else:
                response = "Sorry, I couldn't fetch the latest news. Please try again later."
        
        # Check for whale/Etherscan queries
        elif any(keyword in user_message for keyword in ['whale', 'etherscan', 'transaction', 'blockchain']):
            response = "🐋 Whale tracking and blockchain analysis features are coming soon! Once fully implemented, I'll be able to show you large transactions and on-chain activity."
        
        # Check for portfolio queries
        elif any(keyword in user_message for keyword in ['portfolio', 'position', 'risk', 'calculate']):
            response = "📊 I can help you with portfolio management! Use the Portfolio Tracker above to add positions, or the Position Size Calculator to determine optimal trade sizes based on your risk tolerance."
        
        # General help
        else:
            response = """I'm your AI crypto assistant! Here's what I can help you with:

📊 <strong>Price Checks:</strong> Ask "What's the price of Bitcoin?" or "How much is ETH?"

🎭 <strong>Market Sentiment:</strong> Ask "How's the market sentiment?" or "What's the Fear & Greed Index?"

📰 <strong>Latest News:</strong> Ask "What's the latest crypto news?" or "Any Bitcoin news?"

💼 <strong>Portfolio Help:</strong> Use the tools above for portfolio tracking and position sizing

🐋 <strong>Coming Soon:</strong> Whale tracking and on-chain analysis

Try asking me something specific!"""
        
        return jsonify({"response": response})
        
    except Exception as e:
        return jsonify({
            "response": f"Sorry, I encountered an error: {str(e)}. Please try again."
        }), 500

if __name__ == '__main__':
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings()
    
    print("\n🚀 KROM Crypto Analysis Server")
    print("==============================")
    print("🌐 API running at: http://localhost:5001")
    print("\nAPI Endpoints:")
    print("  GET  /api/price/<symbol>")
    print("  GET  /api/sentiment")
    print("  GET  /api/news/<query>")
    print("  POST /api/portfolio/add")
    print("  POST /api/chat - AI Chat Assistant")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=False, host='127.0.0.1', port=5001)
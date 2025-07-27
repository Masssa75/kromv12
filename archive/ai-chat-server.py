#!/usr/bin/env python3
"""
AI-Powered Chat API Server for KROM Crypto Analysis
Uses Claude AI to intelligently answer questions using crypto tools
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import json
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# In-memory portfolio
portfolio = {}

# In-memory conversation history (in production, use a database)
conversation_history = {}

# Helper functions for crypto tools
def get_crypto_price_sync(symbol):
    """Fetch crypto price from CoinMarketCap or CoinGecko"""
    # Try CoinMarketCap first
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
            print(f"CoinMarketCap error: {e}")
    
    # Fallback to CoinGecko
    try:
        response = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true")
        data = response.json()
        if symbol in data:
            return {
                "symbol": symbol.upper(),
                "price": data[symbol]["usd"],
                "market_cap": data[symbol].get("usd_market_cap", 0),
                "24h_volume": data[symbol].get("usd_24h_vol", 0),
                "24h_change": data[symbol].get("usd_24h_change", 0),
                "source": "CoinGecko"
            }
    except:
        pass
    
    return {"error": f"Could not fetch price for {symbol}"}

def get_market_sentiment():
    """Fetch Fear & Greed Index"""
    try:
        response = requests.get("https://api.alternative.me/fng/")
        data = response.json()
        if data and 'data' in data:
            fng = data['data'][0]
            value = int(fng['value'])
            classification = fng['value_classification']
            
            # Add description based on value
            if value < 25:
                description = "The market is experiencing extreme fear. This could be a buying opportunity for long-term investors."
            elif value < 45:
                description = "The market is fearful. Investors are cautious and selling pressure may be high."
            elif value < 55:
                description = "The market is neutral. No strong emotions dominating either way."
            elif value < 75:
                description = "The market is greedy. Optimism is high and buying activity is strong."
            else:
                description = "The market is extremely greedy. Be cautious as corrections often follow periods of extreme greed."
            
            return {
                "value": value,
                "classification": classification,
                "description": description,
                "last_updated": fng['timestamp']
            }
    except:
        pass
    return {"error": "Could not fetch sentiment data"}

def get_crypto_news(query="cryptocurrency"):
    """Fetch crypto news from NewsAPI"""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return {"error": "News API key not configured"}
    
    try:
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') == 'ok':
            return {
                "articles": data['articles'][:10],
                "total": data['totalResults']
            }
    except:
        pass
    
    return {"error": "Could not fetch news"}

def get_whale_transactions(address=None, limit=10):
    """Fetch whale transactions from Etherscan"""
    etherscan_key = os.getenv("ETHERSCAN_API_KEY")
    if not etherscan_key:
        return {"error": "Etherscan API key not configured"}
    
    try:
        # If no address provided, get latest large transactions
        if not address:
            # Get latest block number
            url = f"https://api.etherscan.io/api?module=proxy&action=eth_blockNumber&apikey={etherscan_key}"
            response = requests.get(url)
            if response.status_code == 200:
                block_hex = response.json().get('result', '0x0')
                block_number = int(block_hex, 16)
                
                # Get transactions from recent blocks
                transactions = []
                for i in range(3):  # Check last 3 blocks
                    block_url = f"https://api.etherscan.io/api?module=proxy&action=eth_getBlockByNumber&tag={hex(block_number - i)}&boolean=true&apikey={etherscan_key}"
                    block_response = requests.get(block_url)
                    if block_response.status_code == 200:
                        block_data = block_response.json().get('result', {})
                        if block_data and 'transactions' in block_data:
                            for tx in block_data['transactions'][:limit]:
                                # Convert value from hex to ETH
                                value_wei = int(tx.get('value', '0x0'), 16)
                                value_eth = value_wei / 1e18
                                
                                # Only include large transactions (> 10 ETH)
                                if value_eth > 10:
                                    transactions.append({
                                        "hash": tx.get('hash'),
                                        "from": tx.get('from'),
                                        "to": tx.get('to'),
                                        "value_eth": round(value_eth, 4),
                                        "value_usd": round(value_eth * 3800, 2),  # Approximate ETH price
                                        "block": int(tx.get('blockNumber', '0x0'), 16),
                                        "gas": int(tx.get('gas', '0x0'), 16)
                                    })
                
                return {
                    "transactions": transactions[:limit],
                    "total": len(transactions)
                }
        else:
            # Get transactions for specific address
            url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset={limit}&sort=desc&apikey={etherscan_key}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == '1':
                    transactions = []
                    for tx in data.get('result', []):
                        value_eth = int(tx.get('value', '0')) / 1e18
                        transactions.append({
                            "hash": tx.get('hash'),
                            "from": tx.get('from'),
                            "to": tx.get('to'),
                            "value_eth": round(value_eth, 4),
                            "value_usd": round(value_eth * 3800, 2),
                            "block": tx.get('blockNumber'),
                            "timestamp": datetime.fromtimestamp(int(tx.get('timeStamp', 0))).isoformat()
                        })
                    return {
                        "address": address,
                        "transactions": transactions,
                        "total": len(transactions)
                    }
    except Exception as e:
        print(f"Etherscan API error: {e}")
    
    return {"error": "Could not fetch whale transactions"}

def get_krom_calls(limit=10):
    """Fetch latest crypto calls from KROM API"""
    krom_token = os.getenv("KROM_API_TOKEN")
    if not krom_token:
        return {"error": "KROM API token not configured"}
    
    try:
        url = f"https://krom.one/api/v1/calls?limit={limit}"
        headers = {
            'Authorization': f'Bearer {krom_token}'
        }
        print(f"Fetching KROM calls from: {url}")
        response = requests.get(url, headers=headers)
        print(f"KROM API response status: {response.status_code}")
        
        if response.status_code == 200:
            calls = response.json()
            print(f"Got {len(calls)} calls from KROM API")
            # Process and format the calls
            formatted_calls = []
            for call in calls[:limit]:
                token = call.get("token", {})
                trade = call.get("trade", {})
                group = call.get("group", {})
                
                # Calculate profit percentage
                buy_price = trade.get("buyPrice", 0)
                top_price = trade.get("topPrice", 0)
                roi = trade.get("roi", 0)
                profit_pct = (roi - 1) * 100 if roi > 0 else 0
                
                formatted_calls.append({
                    "id": call.get("id"),
                    "ticker": token.get("symbol", "Unknown"),
                    "contract": token.get("ca", ""),
                    "network": token.get("network", ""),
                    "buy_price": buy_price,
                    "top_price": top_price,
                    "roi": roi,
                    "profit_percent": round(profit_pct, 2),
                    "call_timestamp": trade.get("buyTimestamp"),
                    "group_name": call.get("groupName", "Unknown"),
                    "group_stats": {
                        "win_rate": group.get("stats", {}).get("winRate30", 0),
                        "profit_30d": group.get("stats", {}).get("profit30", 0),
                        "call_frequency": group.get("stats", {}).get("callFrequency", 0)
                    },
                    "message": call.get("text", "").strip()[:200] + "..." if len(call.get("text", "")) > 200 else call.get("text", ""),
                    "image_url": token.get("imageUrl", "")
                })
            return {
                "calls": formatted_calls,
                "total": len(formatted_calls)
            }
        else:
            print(f"KROM API error response: {response.text}")
            return {"error": f"KROM API returned status {response.status_code}"}
    except Exception as e:
        print(f"KROM API error: {e}")
        import traceback
        traceback.print_exc()
    
    return {"error": "Could not fetch KROM calls"}

def analyze_with_ai(user_message, session_id="default"):
    """Use Claude AI to analyze the message and determine what tools to use"""
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not anthropic_key:
        # If no Anthropic key, provide instructions
        return {
            "response": """I'd love to help you with intelligent crypto analysis, but I need an Anthropic API key to use Claude AI.

To enable AI-powered responses:
1. Get an API key from https://console.anthropic.com/
2. Add it to your .env file: ANTHROPIC_API_KEY=your_key_here
3. Restart the server

Once configured, I'll be able to:
- Answer complex questions about crypto markets
- Combine data from multiple sources intelligently
- Provide detailed analysis and insights
- Understand context and nuance in your questions""",
            "needs_ai_key": True
        }
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        
        # Create a system prompt that explains available tools
        system_prompt = """You are a helpful crypto analysis assistant with access to real-time data through these tools:

1. get_crypto_price(symbol) - Get real-time price data for any cryptocurrency
2. get_market_sentiment() - Get the current Fear & Greed Index
3. get_crypto_news(query) - Get latest news about crypto topics

When users ask questions, analyze what they need and use the appropriate tools. Format your responses with HTML for better readability.

For each tool you want to use, respond with a JSON block like this:
```json
{"tool": "get_crypto_price", "params": {"symbol": "BTC"}}
```

Then continue with your natural language response using the data from the tools."""

        # First, let's collect any data the user might need
        tool_results = {}
        
        # Simple pattern matching for common requests
        message_lower = user_message.lower()
        
        # Check if asking about price
        if any(word in message_lower for word in ['price', 'cost', 'worth', 'value', 'how much']):
            # Extract crypto symbols
            cryptos = []
            crypto_map = {
                'bitcoin': 'BTC', 'btc': 'BTC',
                'ethereum': 'ETH', 'eth': 'ETH',
                'solana': 'SOL', 'sol': 'SOL',
                'cardano': 'ADA', 'ada': 'ADA',
                'dogecoin': 'DOGE', 'doge': 'DOGE',
                'ripple': 'XRP', 'xrp': 'XRP',
                'bnb': 'BNB', 'binance': 'BNB'
            }
            
            for name, symbol in crypto_map.items():
                if name in message_lower:
                    cryptos.append(symbol)
            
            # Get price data for mentioned cryptos
            for symbol in cryptos:
                price_data = get_crypto_price_sync(symbol)
                if 'error' not in price_data:
                    tool_results[f'price_{symbol}'] = price_data
        
        # Check if asking about sentiment
        if any(word in message_lower for word in ['sentiment', 'fear', 'greed', 'market feeling', 'market mood']):
            sentiment_data = get_market_sentiment()
            if 'error' not in sentiment_data:
                tool_results['sentiment'] = sentiment_data
        
        # Check if asking about news
        if any(word in message_lower for word in ['news', 'latest', 'happening', 'update']):
            # Check for specific crypto
            news_query = 'cryptocurrency'
            for crypto in ['bitcoin', 'ethereum', 'solana', 'cardano']:
                if crypto in message_lower:
                    news_query = crypto
                    break
            
            news_data = get_crypto_news(news_query)
            if 'error' not in news_data:
                tool_results['news'] = news_data
        
        # Check if asking about KROM calls
        if any(word in message_lower for word in ['krom', 'calls', 'signals', 'alerts', 'recommendations']):
            krom_data = get_krom_calls(limit=5)
            if 'error' not in krom_data:
                tool_results['krom_calls'] = krom_data
        
        # Check if asking about whale transactions or Etherscan
        if any(word in message_lower for word in ['whale', 'whales', 'etherscan', 'large transaction', 'big transaction']):
            whale_data = get_whale_transactions(limit=5)
            if 'error' not in whale_data:
                tool_results['whale_transactions'] = whale_data
        
        # Get or create conversation history for this session
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        # Add current message to history
        conversation_history[session_id].append({
            "role": "user",
            "content": user_message
        })
        
        # Keep only last 10 messages to avoid token limits
        if len(conversation_history[session_id]) > 20:
            conversation_history[session_id] = conversation_history[session_id][-20:]
        
        # Create conversation messages for Claude
        messages = []
        
        # Add conversation history
        for msg in conversation_history[session_id][:-1]:  # All except the current message
            messages.append(msg)
        
        # Add the current message with enhanced data
        enhanced_prompt = f"""User asked: {user_message}

Available real-time data:
{json.dumps(tool_results, indent=2)}

Please provide a helpful, conversational response using this data. Format your response with HTML tags for better readability. Use <strong> for emphasis, <br> for line breaks, and organize information clearly. Don't mention the JSON data directly - incorporate it naturally into your response. Remember the context of our conversation."""
        
        messages.append({
            "role": "user",
            "content": enhanced_prompt
        })
        
        # Send to Claude with conversation history
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0.7,
            system="""You are KROM Crypto Assistant, an AI-powered crypto analysis tool. You have access to these real-time data sources:

1. **KROM API** ✅ - Latest crypto calls/signals from KROM platform with ROI, win rates, and trader messages
2. **CoinMarketCap API** ✅ - Real-time prices, market cap, volume, 1h/24h/7d changes for any cryptocurrency
3. **CoinGecko API** ✅ (backup) - Alternative price data source
4. **NewsAPI** ✅ - Latest cryptocurrency news and updates
5. **Fear & Greed Index** ✅ - Real-time market sentiment analysis
6. **Etherscan API** ✅ - Ethereum whale tracking, large transactions, and blockchain analysis
7. **CryptoPanic API** ✅ - Crypto-specific news (configured and ready)

IMPORTANT: You DO have access to Etherscan! You can track whale movements, analyze large transactions, and provide on-chain insights. When users ask about whales or Etherscan, use the whale transaction data provided.

When users ask about your capabilities, mention all these APIs including Etherscan whale tracking. Use the real-time data provided to give accurate, up-to-date information. Remember previous messages in the conversation for context.""",
            messages=messages
        )
        
        final_response = message.content[0].text
        
        # Add assistant's response to history
        conversation_history[session_id].append({
            "role": "assistant",
            "content": final_response
        })
        
        return {"response": final_response}
        
    except Exception as e:
        print(f"AI Error: {e}")
        return {"response": f"Sorry, I encountered an error with the AI service: {str(e)}"}

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI-powered chat endpoint"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')  # Allow clients to provide session ID
        
        print(f"Received message: '{user_message}' (session: {session_id})")
        
        # Use AI to analyze and respond
        result = analyze_with_ai(user_message, session_id)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "response": f"Sorry, I encountered an error: {str(e)}. Please try again."
        }), 500

# Keep all the other endpoints from working-api-server.py
@app.route('/api/price/<symbol>')
def get_price(symbol):
    price_data = get_crypto_price_sync(symbol)
    return jsonify(price_data)

@app.route('/api/sentiment')
def get_sentiment():
    sentiment_data = get_market_sentiment()
    return jsonify(sentiment_data)

@app.route('/api/news/<query>')
def get_news(query):
    news_data = get_crypto_news(query)
    return jsonify(news_data)

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

if __name__ == '__main__':
    print("\n🚀 AI-Powered KROM Crypto Analysis Server")
    print("==========================================")
    print("🌐 API running at: http://localhost:5001")
    print("\nFeatures:")
    print("  ✨ AI-powered chat with Claude")
    print("  📊 Real-time crypto prices")
    print("  🎭 Market sentiment analysis")
    print("  📰 Latest crypto news")
    print("\nPress Ctrl+C to stop\n")
    
    # Check for Anthropic API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  WARNING: No Anthropic API key found!")
        print("   Add ANTHROPIC_API_KEY to your .env file for AI features")
        print("")
    
    app.run(debug=False, host='127.0.0.1', port=5001)
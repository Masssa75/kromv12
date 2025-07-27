#!/usr/bin/env python3
"""
True MCP Implementation - AI-Powered Chat API Server for KROM Crypto Analysis
This version gives Claude full control over tool selection and execution
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime
import requests
from dotenv import load_dotenv
import anthropic
import re
from typing import Dict, Any, List, Optional
import sqlite3
import threading
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database lock for thread safety
db_lock = threading.Lock()

app = Flask(__name__)
CORS(app)

# In-memory conversation history (in production, use a database)
conversation_history = {}

# Session-based dynamic tools (created on-the-fly)
dynamic_tools = {}

# System prompt template (capability-focused)
system_prompt_template = """You are KROM Crypto Assistant, an AI with sophisticated analytical capabilities.

## Core Capabilities

I have direct access to:
- **Python Code Execution**: I can write and run Python code with pandas, numpy, and full database access
- **Dynamic Visualizations**: I can create charts, graphs, and tables from any data analysis
- **Cryptocurrency APIs**: Real-time prices, news, whale tracking, market sentiment
- **KROM Database**: 98,000+ crypto calls with detailed performance metrics
- **Tool Creation**: I can create new tools on-the-fly for specific tasks
- **Background Monitoring**: I can run continuous analysis and alert on discoveries

## My Approach

I think like a data scientist and crypto analyst. When you ask me to analyze something, I:
1. Understand what insights would be most valuable
2. Choose the best tools and data sources
3. Execute analysis and create visualizations
4. Present findings concisely

I prefer action over explanation - I'll show you results rather than describe what I could do.

## Database Schema
The KROM calls database has ~100,000 calls in the 'calls' table with these key columns:
- symbol (not ticker or token_symbol)
- buy_price, top_price, roi
- buy_timestamp, top_timestamp
- network, contract_address
- group_name, message_id
- hidden, trade_error

## CRITICAL: Efficient Data Extraction
When querying the database or analyzing data:
1. **ALWAYS limit results** - Never return more than 100 rows unless specifically asked
2. **Aggregate by default** - Use COUNT, AVG, SUM, GROUP BY to extract insights
3. **Sample intelligently** - If you need examples, use LIMIT with ORDER BY
4. **Return insights, not dumps** - Transform data into meaningful summaries
5. **Think like a data scientist** - Extract patterns and statistics, not raw records

Example good query: "SELECT group_name, COUNT(*) as calls, AVG(roi) as avg_roi FROM calls GROUP BY group_name ORDER BY avg_roi DESC LIMIT 20"
Example bad query: "SELECT * FROM calls"

## Creating Visualizations
When using execute_analysis to create charts:
1. Query data directly in your Python code using get_db_connection()
2. Set 'result' variable to a structure compatible with Chart.js
3. For scatter plots: result = {'x': [1,2,3], 'y': [4,5,6], 'labels': ['A','B','C']}
4. For bar charts: result = {'labels': ['Group A', 'Group B'], 'values': [10, 20]}
5. Don't use matplotlib/seaborn - return data for frontend charts

Example execute_analysis code:
```python
conn = get_db_connection()
df = pd.read_sql("SELECT group_name, AVG(roi) as avg_roi FROM calls GROUP BY group_name LIMIT 20", conn)
result = {'labels': df['group_name'].tolist(), 'values': df['avg_roi'].tolist()}
# Don't use 'return' - just set the 'result' variable
```

IMPORTANT: In execute_analysis, set the 'result' variable, don't use 'return' statements!

Remember: The goal is to extract insights that fit in visualizations, not to dump entire datasets."""

# Define available tools with their schemas
AVAILABLE_TOOLS = {
    "get_crypto_price": {
        "description": "Get real-time cryptocurrency price data including market cap, volume, and price changes",
        "parameters": {
            "symbol": {"type": "string", "description": "Cryptocurrency symbol (e.g., BTC, ETH, SOL)"}
        },
        "required": ["symbol"]
    },
    "get_market_sentiment": {
        "description": "Get the current cryptocurrency market sentiment using the Fear & Greed Index",
        "parameters": {},
        "required": []
    },
    "get_crypto_news": {
        "description": "Fetch latest cryptocurrency news articles",
        "parameters": {
            "query": {"type": "string", "description": "Search query for news (default: 'cryptocurrency')"}
        },
        "required": []
    },
    "get_whale_transactions": {
        "description": "Fetch large cryptocurrency transactions (whale movements) from Ethereum blockchain",
        "parameters": {
            "address": {"type": "string", "description": "Ethereum address to check (optional)"},
            "limit": {"type": "integer", "description": "Number of transactions to return (default: 10)"}
        },
        "required": []
    },
    "get_krom_calls": {
        "description": "Fetch crypto trading calls/signals from KROM platform with ROI and win rate data. Supports pagination.",
        "parameters": {
            "limit": {"type": "integer", "description": "Number of calls to return (default: 100, max: 100)"},
            "before_timestamp": {"type": "integer", "description": "Unix timestamp to get calls before (for pagination)"}
        },
        "required": []
    },
    "get_token_info": {
        "description": "Get detailed information about a specific token including contract details and holders",
        "parameters": {
            "contract_address": {"type": "string", "description": "Token contract address"},
            "network": {"type": "string", "description": "Blockchain network (e.g., ethereum, bsc, polygon)"}
        },
        "required": ["contract_address"]
    },
    "get_token_transactions": {
        "description": "Get recent transactions for a specific token",
        "parameters": {
            "contract_address": {"type": "string", "description": "Token contract address"},
            "limit": {"type": "integer", "description": "Number of transactions (default: 20)"}
        },
        "required": ["contract_address"]
    },
    "analyze_wallet": {
        "description": "Analyze a wallet address for holdings, transaction history, and patterns",
        "parameters": {
            "address": {"type": "string", "description": "Wallet address to analyze"},
            "network": {"type": "string", "description": "Blockchain network (default: ethereum)"}
        },
        "required": ["address"]
    },
    "call_api": {
        "description": "Make HTTP requests to any API endpoint. Use this for APIs not covered by existing tools",
        "parameters": {
            "url": {"type": "string", "description": "Full URL of the API endpoint"},
            "method": {"type": "string", "description": "HTTP method (GET, POST, PUT, DELETE). Default: GET"},
            "headers": {"type": "object", "description": "HTTP headers as key-value pairs (e.g., {'Authorization': 'Bearer token'})"},
            "params": {"type": "object", "description": "URL parameters for GET requests"},
            "data": {"type": "object", "description": "Request body for POST/PUT requests"},
            "api_key_env": {"type": "string", "description": "Environment variable name containing API key (e.g., 'COINGECKO_API_KEY')"}
        },
        "required": ["url"]
    },
    "create_tool": {
        "description": "Create a custom tool for a specific API endpoint that can be reused in this session",
        "parameters": {
            "tool_name": {"type": "string", "description": "Name for the new tool (e.g., 'get_defi_tvl')"},
            "description": {"type": "string", "description": "What this tool does"},
            "base_url": {"type": "string", "description": "Base API URL"},
            "endpoint": {"type": "string", "description": "Specific endpoint path"},
            "method": {"type": "string", "description": "HTTP method (default: GET)"},
            "required_params": {"type": "array", "description": "List of required parameter names"},
            "optional_params": {"type": "array", "description": "List of optional parameter names"}, 
            "api_key_env": {"type": "string", "description": "Environment variable for API key (optional)"},
            "example_params": {"type": "object", "description": "Example parameters to test the tool"}
        },
        "required": ["tool_name", "description", "base_url", "endpoint"]
    },
    "analyze_token_launch": {
        "description": "Analyze initial token distribution and detect potential sniping/manipulation in first transactions",
        "parameters": {
            "contract_address": {"type": "string", "description": "Token contract address"},
            "network": {"type": "string", "description": "Blockchain network (ethereum or solana, default: ethereum)"},
            "snipe_threshold": {"type": "number", "description": "Percentage threshold for flagging concentrated ownership (default: 30)"},
            "initial_blocks": {"type": "integer", "description": "Number of initial blocks to analyze (default: 5)"}
        },
        "required": ["contract_address"]
    },
    "solscan_api_call": {
        "description": "Make calls to various Solscan API endpoints for Solana blockchain data",
        "parameters": {
            "endpoint": {"type": "string", "description": "Solscan endpoint (e.g., 'token/transfer', 'account/transactions')"},
            "token": {"type": "string", "description": "Token contract address (optional)"},
            "account": {"type": "string", "description": "Account address (optional)"},
            "limit": {"type": "integer", "description": "Number of results (default: 50)"},
            "offset": {"type": "integer", "description": "Offset for pagination (default: 0)"}
        },
        "required": ["endpoint"]
    },
    "download_krom_calls": {
        "description": "Download KROM calls from API and store in local SQLite database",
        "parameters": {
            "limit": {"type": "integer", "description": "Number of calls to download (max: 10000)", "default": 1000}
        },
        "required": []
    },
    "query_krom_database": {
        "description": "Query the local KROM calls database with SQL",
        "parameters": {
            "query": {"type": "string", "description": "SQL query to execute on the database"},
            "params": {"type": "array", "description": "Query parameters for safe SQL execution", "items": {"type": "string"}}
        },
        "required": ["query"]
    },
    "analyze_krom_stats": {
        "description": "Get statistical analysis of KROM calls data",
        "parameters": {
            "analysis_type": {"type": "string", "description": "Type of analysis: 'overview', 'groups', 'performance', 'trends', 'top_performers'"},
            "timeframe": {"type": "string", "description": "Timeframe: 'all', '7d', '30d', '90d'", "default": "all"},
            "group_name": {"type": "string", "description": "Optional: filter by specific group"}
        },
        "required": ["analysis_type"]
    },
    "create_chart": {
        "description": "Simple chart creation - just provide a SQL query that returns 2 columns (labels, values)",
        "parameters": {
            "query": {"type": "string", "description": "SQL query returning 2 columns: first for labels, second for values"},
            "chart_type": {"type": "string", "description": "Chart type: 'bar', 'line', 'pie' (default: bar)"},
            "title": {"type": "string", "description": "Chart title"}
        },
        "required": ["query"]
    },
    "execute_analysis": {
        "description": "Execute Python code for custom data analysis. Use this for complex queries, data transformations, and creating custom visualizations.",
        "parameters": {
            "code": {"type": "string", "description": "Python code to execute. Has access to: pandas as pd, numpy as np, get_db_connection() for database, and can return data for visualization"},
            "visualization_type": {"type": "string", "description": "Type of visualization to create: 'chart', 'table', 'stat_card', 'heatmap', 'scatter', 'custom'"},
            "title": {"type": "string", "description": "Title for the visualization"}
        },
        "required": ["code"]
    }
}

# Tool implementation functions
def get_crypto_price(symbol: str) -> Dict[str, Any]:
    """Fetch crypto price from CoinMarketCap or CoinGecko"""
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
                        "success": True,
                        "data": {
                            "symbol": symbol.upper(),
                            "name": crypto_data['name'],
                            "price": round(quote['price'], 2 if quote['price'] > 1 else 6),
                            "market_cap": quote['market_cap'],
                            "market_cap_rank": crypto_data['cmc_rank'],
                            "volume_24h": quote['volume_24h'],
                            "circulating_supply": crypto_data['circulating_supply'],
                            "total_supply": crypto_data['total_supply'],
                            "max_supply": crypto_data['max_supply'],
                            "changes": {
                                "1h": round(quote['percent_change_1h'], 2),
                                "24h": round(quote['percent_change_24h'], 2),
                                "7d": round(quote['percent_change_7d'], 2),
                                "30d": round(quote.get('percent_change_30d', 0), 2),
                                "60d": round(quote.get('percent_change_60d', 0), 2),
                                "90d": round(quote.get('percent_change_90d', 0), 2)
                            },
                            "last_updated": quote['last_updated'],
                            "source": "CoinMarketCap"
                        }
                    }
        except Exception as e:
            print(f"CoinMarketCap error: {e}")
    
    # Fallback to CoinGecko
    try:
        # First, search for the coin ID
        search_url = f"https://api.coingecko.com/api/v3/search?query={symbol}"
        search_resp = requests.get(search_url)
        if search_resp.status_code == 200:
            search_data = search_resp.json()
            if search_data['coins']:
                coin_id = search_data['coins'][0]['id']
                
                # Get detailed data
                detail_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
                detail_resp = requests.get(detail_url)
                if detail_resp.status_code == 200:
                    coin_data = detail_resp.json()
                    return {
                        "success": True,
                        "data": {
                            "symbol": symbol.upper(),
                            "name": coin_data['name'],
                            "price": coin_data['market_data']['current_price']['usd'],
                            "market_cap": coin_data['market_data']['market_cap']['usd'],
                            "market_cap_rank": coin_data['market_cap_rank'],
                            "volume_24h": coin_data['market_data']['total_volume']['usd'],
                            "circulating_supply": coin_data['market_data']['circulating_supply'],
                            "total_supply": coin_data['market_data']['total_supply'],
                            "max_supply": coin_data['market_data']['max_supply'],
                            "changes": {
                                "1h": round(coin_data['market_data']['price_change_percentage_1h_in_currency']['usd'], 2),
                                "24h": round(coin_data['market_data']['price_change_percentage_24h'], 2),
                                "7d": round(coin_data['market_data']['price_change_percentage_7d'], 2),
                                "30d": round(coin_data['market_data']['price_change_percentage_30d'], 2),
                                "60d": round(coin_data['market_data']['price_change_percentage_60d'], 2),
                                "200d": round(coin_data['market_data']['price_change_percentage_200d'], 2),
                                "1y": round(coin_data['market_data']['price_change_percentage_1y'], 2)
                            },
                            "ath": coin_data['market_data']['ath']['usd'],
                            "ath_date": coin_data['market_data']['ath_date']['usd'],
                            "atl": coin_data['market_data']['atl']['usd'],
                            "atl_date": coin_data['market_data']['atl_date']['usd'],
                            "source": "CoinGecko"
                        }
                    }
    except Exception as e:
        print(f"CoinGecko error: {e}")
    
    return {"success": False, "error": f"Could not fetch price for {symbol}"}

def get_market_sentiment() -> Dict[str, Any]:
    """Fetch Fear & Greed Index"""
    try:
        response = requests.get("https://api.alternative.me/fng/?limit=10")
        data = response.json()
        if data and 'data' in data:
            # Get current and historical data
            current = data['data'][0]
            history = data['data'][1:6] if len(data['data']) > 1 else []
            
            value = int(current['value'])
            
            # Calculate trend
            if history:
                prev_value = int(history[0]['value'])
                trend = "increasing" if value > prev_value else "decreasing" if value < prev_value else "stable"
            else:
                trend = "unknown"
            
            return {
                "success": True,
                "data": {
                    "current": {
                        "value": value,
                        "classification": current['value_classification'],
                        "timestamp": current['timestamp']
                    },
                    "trend": trend,
                    "history": [
                        {
                            "value": int(h['value']),
                            "classification": h['value_classification'],
                            "timestamp": h['timestamp']
                        } for h in history
                    ],
                    "analysis": get_sentiment_analysis(value, trend)
                }
            }
    except Exception as e:
        print(f"Sentiment API error: {e}")
    
    return {"success": False, "error": "Could not fetch sentiment data"}

def get_sentiment_analysis(value: int, trend: str) -> str:
    """Provide detailed sentiment analysis"""
    if value < 25:
        base = "The market is experiencing extreme fear."
        action = "This often presents buying opportunities for contrarian investors."
    elif value < 45:
        base = "The market is fearful."
        action = "Caution is warranted, but selective opportunities may exist."
    elif value < 55:
        base = "The market sentiment is neutral."
        action = "Neither fear nor greed dominates - a balanced approach is suitable."
    elif value < 75:
        base = "The market is greedy."
        action = "Consider taking some profits and being selective with new positions."
    else:
        base = "The market is extremely greedy."
        action = "High risk of correction - consider reducing exposure."
    
    if trend == "increasing":
        trend_text = "Sentiment is improving, suggesting growing confidence."
    elif trend == "decreasing":
        trend_text = "Sentiment is deteriorating, indicating increasing caution."
    else:
        trend_text = "Sentiment remains stable."
    
    return f"{base} {trend_text} {action}"

def get_crypto_news(query: str = "cryptocurrency") -> Dict[str, Any]:
    """Fetch crypto news from multiple sources"""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return {"success": False, "error": "News API key not configured"}
    
    try:
        # Try NewsAPI
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&language=en&apiKey={api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                articles = []
                for article in data['articles'][:15]:
                    articles.append({
                        "title": article['title'],
                        "description": article['description'],
                        "source": article['source']['name'],
                        "url": article['url'],
                        "published_at": article['publishedAt'],
                        "image_url": article.get('urlToImage')
                    })
                
                return {
                    "success": True,
                    "data": {
                        "articles": articles,
                        "total": data['totalResults'],
                        "query": query
                    }
                }
    except Exception as e:
        print(f"News API error: {e}")
    
    return {"success": False, "error": "Could not fetch news"}

def get_whale_transactions(address: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Enhanced whale transaction fetching with token support"""
    etherscan_key = os.getenv("ETHERSCAN_API_KEY")
    if not etherscan_key:
        return {"success": False, "error": "Etherscan API key not configured"}
    
    try:
        transactions = []
        
        if not address:
            # Get latest large ETH transactions
            url = f"https://api.etherscan.io/api?module=proxy&action=eth_blockNumber&apikey={etherscan_key}"
            response = requests.get(url)
            if response.status_code == 200:
                block_hex = response.json().get('result', '0x0')
                block_number = int(block_hex, 16)
                
                # Check last 5 blocks for large transactions
                for i in range(5):
                    block_url = f"https://api.etherscan.io/api?module=proxy&action=eth_getBlockByNumber&tag={hex(block_number - i)}&boolean=true&apikey={etherscan_key}"
                    block_response = requests.get(block_url)
                    if block_response.status_code == 200:
                        block_data = block_response.json().get('result', {})
                        if block_data and 'transactions' in block_data:
                            for tx in block_data['transactions']:
                                value_wei = int(tx.get('value', '0x0'), 16)
                                value_eth = value_wei / 1e18
                                
                                # Only include transactions > 100 ETH
                                if value_eth > 100:
                                    transactions.append({
                                        "type": "ETH Transfer",
                                        "hash": tx.get('hash'),
                                        "from": tx.get('from'),
                                        "to": tx.get('to'),
                                        "value": round(value_eth, 4),
                                        "value_usd": round(value_eth * 3800, 2),
                                        "block": int(tx.get('blockNumber', '0x0'), 16),
                                        "gas_used": int(tx.get('gas', '0x0'), 16),
                                        "timestamp": "recent"
                                    })
        else:
            # Get transactions for specific address (including tokens)
            # First get ETH transactions
            eth_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset={limit}&sort=desc&apikey={etherscan_key}"
            eth_response = requests.get(eth_url)
            if eth_response.status_code == 200 and eth_response.json().get('status') == '1':
                for tx in eth_response.json().get('result', [])[:limit//2]:
                    value_eth = int(tx.get('value', '0')) / 1e18
                    if value_eth > 0:
                        transactions.append({
                            "type": "ETH Transfer",
                            "hash": tx.get('hash'),
                            "from": tx.get('from'),
                            "to": tx.get('to'),
                            "value": round(value_eth, 4),
                            "value_usd": round(value_eth * 3800, 2),
                            "block": tx.get('blockNumber'),
                            "timestamp": datetime.fromtimestamp(int(tx.get('timeStamp', 0))).isoformat()
                        })
            
            # Get ERC20 token transactions
            token_url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&page=1&offset={limit}&sort=desc&apikey={etherscan_key}"
            token_response = requests.get(token_url)
            if token_response.status_code == 200 and token_response.json().get('status') == '1':
                for tx in token_response.json().get('result', [])[:limit//2]:
                    decimals = int(tx.get('tokenDecimal', '18'))
                    value = int(tx.get('value', '0')) / (10 ** decimals)
                    transactions.append({
                        "type": "Token Transfer",
                        "token_name": tx.get('tokenName'),
                        "token_symbol": tx.get('tokenSymbol'),
                        "hash": tx.get('hash'),
                        "from": tx.get('from'),
                        "to": tx.get('to'),
                        "value": round(value, 4),
                        "contract_address": tx.get('contractAddress'),
                        "block": tx.get('blockNumber'),
                        "timestamp": datetime.fromtimestamp(int(tx.get('timeStamp', 0))).isoformat()
                    })
        
        # Sort by block number (most recent first)
        transactions.sort(key=lambda x: int(x.get('block', 0)), reverse=True)
        
        return {
            "success": True,
            "data": {
                "transactions": transactions[:limit],
                "total": len(transactions),
                "address": address if address else "latest blocks"
            }
        }
        
    except Exception as e:
        print(f"Etherscan API error: {e}")
        return {"success": False, "error": f"Etherscan API error: {str(e)}"}

def get_krom_calls(limit: int = 100, before_timestamp: Optional[int] = None) -> Dict[str, Any]:
    """Fetch crypto calls from KROM API with pagination support"""
    krom_token = os.getenv("KROM_API_TOKEN")
    if not krom_token:
        return {"success": False, "error": "KROM API token not configured"}
    
    try:
        url = f"https://krom.one/api/v1/calls?limit={limit}"
        if before_timestamp:
            url += f"&beforetimestamp={before_timestamp}"
        headers = {'Authorization': f'Bearer {krom_token}'}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            calls = response.json()
            formatted_calls = []
            
            for call in calls[:limit]:
                token = call.get("token", {})
                trade = call.get("trade", {})
                group = call.get("group", {})
                
                buy_price = trade.get("buyPrice", 0)
                top_price = trade.get("topPrice", 0)
                roi = trade.get("roi", 0)
                profit_pct = (roi - 1) * 100 if roi > 0 else 0
                
                formatted_calls.append({
                    "id": call.get("id"),
                    "ticker": token.get("symbol", "Unknown"),
                    "name": token.get("name", ""),
                    "contract": token.get("ca", ""),
                    "network": token.get("network", ""),
                    "market_cap": token.get("marketCap", 0),
                    "buy_price": buy_price,
                    "top_price": top_price,
                    "current_price": trade.get("currentPrice", 0),
                    "roi": roi,
                    "profit_percent": round(profit_pct, 2),
                    "status": "profit" if roi > 1 else "loss" if roi < 1 else "breakeven",
                    "call_timestamp": trade.get("buyTimestamp"),
                    "group": {
                        "name": call.get("groupName", "Unknown"),
                        "win_rate_30d": group.get("stats", {}).get("winRate30", 0),
                        "profit_30d": group.get("stats", {}).get("profit30", 0),
                        "total_calls": group.get("stats", {}).get("totalCalls", 0),
                        "call_frequency": group.get("stats", {}).get("callFrequency", 0)
                    },
                    "message": call.get("text", ""),
                    "image_url": token.get("imageUrl", "")
                })
            
            # Calculate summary statistics
            total_calls = len(formatted_calls)
            profitable_calls = sum(1 for c in formatted_calls if c['status'] == 'profit')
            average_roi = sum(c['roi'] for c in formatted_calls) / total_calls if total_calls > 0 else 0
            
            return {
                "success": True,
                "data": {
                    "calls": formatted_calls,
                    "summary": {
                        "total": total_calls,
                        "profitable": profitable_calls,
                        "win_rate": round((profitable_calls / total_calls * 100) if total_calls > 0 else 0, 2),
                        "average_roi": round(average_roi, 2)
                    }
                }
            }
        else:
            return {"success": False, "error": f"KROM API returned status {response.status_code}"}
            
    except Exception as e:
        print(f"KROM API error: {e}")
        return {"success": False, "error": f"KROM API error: {str(e)}"}

def get_token_info(contract_address: str, network: str = "ethereum") -> Dict[str, Any]:
    """Get detailed token information"""
    etherscan_key = os.getenv("ETHERSCAN_API_KEY")
    if not etherscan_key:
        return {"success": False, "error": "Etherscan API key not configured"}
    
    try:
        # Get token info from Etherscan
        token_url = f"https://api.etherscan.io/api?module=token&action=tokeninfo&contractaddress={contract_address}&apikey={etherscan_key}"
        response = requests.get(token_url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1' and data.get('result'):
                result = data['result'][0] if isinstance(data['result'], list) else data['result']
                
                # Get additional data
                # Get total supply
                supply_url = f"https://api.etherscan.io/api?module=stats&action=tokensupply&contractaddress={contract_address}&apikey={etherscan_key}"
                supply_resp = requests.get(supply_url)
                total_supply = 0
                if supply_resp.status_code == 200:
                    supply_data = supply_resp.json()
                    if supply_data.get('status') == '1':
                        decimals = int(result.get('divisor', '18').replace('E', 'e'))
                        total_supply = int(supply_data.get('result', '0')) / (10 ** decimals)
                
                return {
                    "success": True,
                    "data": {
                        "contract_address": contract_address,
                        "name": result.get('tokenName', 'Unknown'),
                        "symbol": result.get('symbol', 'Unknown'),
                        "decimals": result.get('divisor', '18'),
                        "total_supply": total_supply,
                        "type": result.get('tokenType', 'ERC20'),
                        "website": result.get('website', ''),
                        "social_links": {
                            "twitter": result.get('twitter', ''),
                            "telegram": result.get('telegram', ''),
                            "discord": result.get('discord', '')
                        },
                        "network": network
                    }
                }
        
        # Try CoinGecko as fallback
        try:
            gecko_url = f"https://api.coingecko.com/api/v3/coins/{network}/contract/{contract_address}"
            gecko_resp = requests.get(gecko_url)
            if gecko_resp.status_code == 200:
                gecko_data = gecko_resp.json()
                return {
                    "success": True,
                    "data": {
                        "contract_address": contract_address,
                        "name": gecko_data.get('name', 'Unknown'),
                        "symbol": gecko_data.get('symbol', 'Unknown').upper(),
                        "decimals": 18,
                        "total_supply": gecko_data.get('market_data', {}).get('total_supply', 0),
                        "market_cap": gecko_data.get('market_data', {}).get('market_cap', {}).get('usd', 0),
                        "price": gecko_data.get('market_data', {}).get('current_price', {}).get('usd', 0),
                        "website": gecko_data.get('links', {}).get('homepage', [''])[0],
                        "social_links": {
                            "twitter": gecko_data.get('links', {}).get('twitter_screen_name', ''),
                            "telegram": gecko_data.get('links', {}).get('telegram_channel_identifier', ''),
                            "discord": gecko_data.get('links', {}).get('discord', '')
                        },
                        "network": network,
                        "source": "CoinGecko"
                    }
                }
        except:
            pass
            
    except Exception as e:
        print(f"Token info error: {e}")
    
    return {"success": False, "error": f"Could not fetch token info for {contract_address}"}

def get_token_transactions(contract_address: str, limit: int = 20) -> Dict[str, Any]:
    """Get recent transactions for a specific token"""
    etherscan_key = os.getenv("ETHERSCAN_API_KEY")
    if not etherscan_key:
        return {"success": False, "error": "Etherscan API key not configured"}
    
    try:
        # Get token transfer events
        url = f"https://api.etherscan.io/api?module=logs&action=getLogs&address={contract_address}&topic0=0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef&page=1&offset={limit}&sort=desc&apikey={etherscan_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == '1':
                transactions = []
                
                for log in data.get('result', []):
                    # Decode transfer event
                    topics = log.get('topics', [])
                    if len(topics) >= 3:
                        from_address = '0x' + topics[1][-40:]
                        to_address = '0x' + topics[2][-40:]
                        value_hex = log.get('data', '0x0')
                        
                        # Get transaction details
                        tx_hash = log.get('transactionHash')
                        tx_url = f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}&apikey={etherscan_key}"
                        tx_resp = requests.get(tx_url)
                        
                        gas_price = 0
                        if tx_resp.status_code == 200:
                            tx_data = tx_resp.json().get('result', {})
                            gas_price = int(tx_data.get('gasPrice', '0x0'), 16) / 1e9  # Convert to Gwei
                        
                        transactions.append({
                            "hash": tx_hash,
                            "from": from_address,
                            "to": to_address,
                            "value": value_hex,  # Would need token decimals to convert
                            "block": int(log.get('blockNumber', '0x0'), 16),
                            "gas_price_gwei": round(gas_price, 2)
                        })
                
                return {
                    "success": True,
                    "data": {
                        "contract_address": contract_address,
                        "transactions": transactions,
                        "total": len(transactions)
                    }
                }
                
    except Exception as e:
        print(f"Token transactions error: {e}")
    
    return {"success": False, "error": f"Could not fetch transactions for token {contract_address}"}

def analyze_wallet(address: str, network: str = "ethereum") -> Dict[str, Any]:
    """Analyze a wallet address"""
    etherscan_key = os.getenv("ETHERSCAN_API_KEY")
    if not etherscan_key:
        return {"success": False, "error": "Etherscan API key not configured"}
    
    try:
        # Get ETH balance
        balance_url = f"https://api.etherscan.io/api?module=account&action=balance&address={address}&tag=latest&apikey={etherscan_key}"
        balance_resp = requests.get(balance_url)
        eth_balance = 0
        if balance_resp.status_code == 200:
            balance_data = balance_resp.json()
            if balance_data.get('status') == '1':
                eth_balance = int(balance_data.get('result', '0')) / 1e18
        
        # Get transaction count
        tx_count_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=1&apikey={etherscan_key}"
        tx_count_resp = requests.get(tx_count_url)
        total_transactions = 0
        first_tx_time = None
        if tx_count_resp.status_code == 200:
            tx_data = tx_count_resp.json()
            if tx_data.get('status') == '1':
                # Get total from a different endpoint
                count_url = f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionCount&address={address}&tag=latest&apikey={etherscan_key}"
                count_resp = requests.get(count_url)
                if count_resp.status_code == 200:
                    count_data = count_resp.json()
                    total_transactions = int(count_data.get('result', '0x0'), 16)
                
                # Get first transaction time
                if tx_data.get('result'):
                    first_tx_time = datetime.fromtimestamp(int(tx_data['result'][0].get('timeStamp', 0))).isoformat()
        
        # Get token balances
        tokens_url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={etherscan_key}"
        tokens_resp = requests.get(tokens_url)
        token_holdings = {}
        if tokens_resp.status_code == 200:
            tokens_data = tokens_resp.json()
            if tokens_data.get('status') == '1':
                # Track unique tokens
                for tx in tokens_data.get('result', []):
                    token_symbol = tx.get('tokenSymbol')
                    token_name = tx.get('tokenName')
                    contract = tx.get('contractAddress')
                    if token_symbol and contract not in token_holdings:
                        token_holdings[contract] = {
                            "symbol": token_symbol,
                            "name": token_name,
                            "contract_address": contract
                        }
        
        # Get ENS name if exists
        ens_url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&endblock=99999999&page=1&offset=1&apikey={etherscan_key}"
        # This is a simplified check - proper ENS resolution would require web3
        
        return {
            "success": True,
            "data": {
                "address": address,
                "eth_balance": round(eth_balance, 6),
                "eth_balance_usd": round(eth_balance * 3800, 2),  # Approximate
                "total_transactions": total_transactions,
                "first_seen": first_tx_time,
                "token_holdings": list(token_holdings.values()),
                "total_tokens_interacted": len(token_holdings),
                "network": network,
                "explorer_url": f"https://etherscan.io/address/{address}"
            }
        }
        
    except Exception as e:
        print(f"Wallet analysis error: {e}")
    
    return {"success": False, "error": f"Could not analyze wallet {address}"}

def call_api(url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None, 
             params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None,
             api_key_env: Optional[str] = None) -> Dict[str, Any]:
    """Generic API caller with safety features"""
    try:
        # Safety checks
        allowed_domains = [
            "api.coingecko.com",
            "api.etherscan.io", 
            "pro-api.coinmarketcap.com",
            "api.binance.com",
            "api.kraken.com",
            "api.coinbase.com",
            "api.dexscreener.com",
            "api.1inch.io",
            "api.0x.org",
            "api.thegraph.com",
            "api.covalenthq.com",
            "api.moralis.io",
            "api.nftport.xyz",
            "api.opensea.io",
            "api.chainlink.com",
            "api.compound.finance",
            "api.aave.com",
            "api.sushi.com",
            "api.uniswap.org",
            "api.blockchain.info",
            "api.blockcypher.com",
            "min-api.cryptocompare.com",
            "api.alternative.me",
            "api.lunarcrush.com",
            "api.messari.io",
            "api.nomics.com",
            "api.zapper.fi",
            "api.zerion.io",
            "data.chain.link",
            "api.debank.com",
            "newsapi.org",
            "api.twitter.com",
            "nitter.net",
            "api.telegram.org",
            "public-api.solscan.io",
            "api.solscan.io",
            "pro-api.solscan.io",
            "api-v2.solscan.io",
            "api.mainnet-beta.solana.com",
            "quote-api.jup.ag",
            "api.helius.xyz",
            "krom.one",
            "api.krom.app"
        ]
        
        # Extract domain from URL
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Check if domain is allowed
        if not any(allowed in domain for allowed in allowed_domains):
            return {
                "success": False,
                "error": f"Domain {domain} is not in the allowed list for safety reasons"
            }
        
        # Prepare headers
        request_headers = headers or {}
        
        # Add API key from environment if specified
        if api_key_env:
            api_key = os.getenv(api_key_env)
            if not api_key:
                return {
                    "success": False,
                    "error": f"API key environment variable '{api_key_env}' not found"
                }
            # Common API key header patterns
            if "etherscan" in domain:
                if params is None:
                    params = {}
                params['apikey'] = api_key
            elif "coinmarketcap" in domain:
                request_headers['X-CMC_PRO_API_KEY'] = api_key
            elif "newsapi" in domain:
                if params is None:
                    params = {}
                params['apiKey'] = api_key
            elif "solscan" in domain:
                request_headers['Authorization'] = f'Bearer {api_key}'
            elif "helius" in domain:
                # Helius uses API key in URL path
                if "?" in url:
                    url = f"{url}&api-key={api_key}"
                else:
                    url = f"{url}?api-key={api_key}"
            else:
                # Default to Authorization header
                request_headers['Authorization'] = f'Bearer {api_key}'
        
        # Make the request
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=request_headers,
            params=params,
            json=data if method.upper() in ['POST', 'PUT'] else None,
            timeout=30
        )
        
        # Check response
        if response.status_code >= 200 and response.status_code < 300:
            try:
                response_data = response.json()
                return {
                    "success": True,
                    "data": response_data,
                    "status_code": response.status_code,
                    "headers": dict(response.headers)
                }
            except:
                # Response is not JSON
                return {
                    "success": True,
                    "data": response.text,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content_type": response.headers.get('content-type', 'text/plain')
                }
        else:
            return {
                "success": False,
                "error": f"API returned status code {response.status_code}",
                "status_code": response.status_code,
                "response": response.text[:500]  # First 500 chars of error
            }
            
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Request timed out after 30 seconds"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "Failed to connect to the API"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

def create_tool(tool_name: str, description: str, base_url: str, endpoint: str,
                method: str = "GET", required_params: Optional[List[str]] = None,
                optional_params: Optional[List[str]] = None, 
                api_key_env: Optional[str] = None,
                example_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a dynamic tool for a specific API endpoint"""
    try:
        # Validate tool name
        if not tool_name.replace('_', '').isalnum():
            return {"success": False, "error": "Tool name must contain only letters, numbers, and underscores"}
        
        if tool_name in AVAILABLE_TOOLS:
            return {"success": False, "error": f"Tool name '{tool_name}' conflicts with existing tool"}
        
        # Construct full URL
        full_url = base_url.rstrip('/') + '/' + endpoint.lstrip('/')
        
        # Create tool definition
        tool_def = {
            "description": description,
            "base_url": base_url,
            "endpoint": endpoint,
            "full_url": full_url,
            "method": method.upper(),
            "required_params": required_params or [],
            "optional_params": optional_params or [],
            "api_key_env": api_key_env
        }
        
        # Test the tool if example params provided
        if example_params:
            test_result = call_api(
                url=full_url,
                method=method,
                params=example_params if method.upper() == 'GET' else None,
                data=example_params if method.upper() in ['POST', 'PUT'] else None,
                api_key_env=api_key_env
            )
            
            if not test_result.get("success"):
                return {
                    "success": False,
                    "error": f"Tool test failed: {test_result.get('error')}",
                    "test_result": test_result
                }
            
            tool_def["test_result"] = test_result
        
        # Store the dynamic tool (session-based)
        dynamic_tools[tool_name] = tool_def
        
        return {
            "success": True,
            "message": f"Tool '{tool_name}' created successfully",
            "tool_definition": tool_def,
            "usage": f"Use this tool by calling: {tool_name}(params)"
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to create tool: {str(e)}"}

def call_dynamic_tool(tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute a dynamically created tool"""
    if tool_name not in dynamic_tools:
        return {"success": False, "error": f"Dynamic tool '{tool_name}' not found"}
    
    tool_def = dynamic_tools[tool_name]
    params = params or {}
    
    # Check required parameters
    missing_params = [p for p in tool_def["required_params"] if p not in params]
    if missing_params:
        return {
            "success": False, 
            "error": f"Missing required parameters: {missing_params}"
        }
    
    # Call the API using the stored definition
    return call_api(
        url=tool_def["full_url"],
        method=tool_def["method"],
        params=params if tool_def["method"] == 'GET' else None,
        data=params if tool_def["method"] in ['POST', 'PUT'] else None,
        api_key_env=tool_def.get("api_key_env")
    )

def analyze_token_launch(contract_address: str, network: str = "ethereum", 
                        snipe_threshold: float = 30.0, initial_blocks: int = 5) -> Dict[str, Any]:
    """Analyze token launch for potential sniping and manipulation"""
    try:
        if network.lower() == "ethereum":
            return analyze_eth_token_launch(contract_address, snipe_threshold, initial_blocks)
        elif network.lower() == "solana":
            return analyze_sol_token_launch(contract_address, snipe_threshold, initial_blocks)
        else:
            return {"success": False, "error": f"Unsupported network: {network}"}
    except Exception as e:
        return {"success": False, "error": f"Token launch analysis failed: {str(e)}"}

def analyze_eth_token_launch(contract_address: str, snipe_threshold: float, initial_blocks: int) -> Dict[str, Any]:
    """Analyze Ethereum token launch"""
    etherscan_key = os.getenv("ETHERSCAN_API_KEY")
    if not etherscan_key:
        return {"success": False, "error": "Etherscan API key required"}
    
    try:
        # Get first 200 token transactions
        url = f"https://api.etherscan.io/api?module=account&action=tokentx&contractaddress={contract_address}&page=1&offset=200&sort=asc&apikey={etherscan_key}"
        response = requests.get(url)
        
        if response.status_code != 200:
            return {"success": False, "error": f"API error: {response.status_code}"}
        
        data = response.json()
        if data.get('status') != '1':
            return {"success": False, "error": "No token transactions found"}
        
        transactions = data.get('result', [])
        if not transactions:
            return {"success": False, "error": "No transactions found"}
        
        # Get token decimals
        first_tx = transactions[0]
        decimals = int(first_tx.get('tokenDecimal', '18'))
        
        # Find the first few blocks
        first_block = int(transactions[0]['blockNumber'])
        target_blocks = set(str(first_block + i) for i in range(initial_blocks))
        
        # Analyze initial transactions
        initial_txs = [tx for tx in transactions if tx['blockNumber'] in target_blocks]
        
        # Track wallet accumulation
        wallet_accumulation = {}
        total_transferred = 0
        
        for tx in initial_txs:
            to_address = tx['to'].lower()
            value = int(tx['value']) / (10 ** decimals)
            
            if to_address not in wallet_accumulation:
                wallet_accumulation[to_address] = 0
            wallet_accumulation[to_address] += value
            total_transferred += value
        
        # Calculate concentrations
        sorted_wallets = sorted(wallet_accumulation.items(), key=lambda x: x[1], reverse=True)
        top_10_wallets = sorted_wallets[:10]
        
        # Calculate percentages
        top_10_total = sum(amount for _, amount in top_10_wallets)
        top_10_percentage = (top_10_total / total_transferred * 100) if total_transferred > 0 else 0
        
        # Risk assessment
        risk_level = "HIGH" if top_10_percentage > snipe_threshold else "MEDIUM" if top_10_percentage > 15 else "LOW"
        
        # Gas analysis for sniper detection
        gas_prices = []
        for tx in initial_txs:
            gas_price = int(tx.get('gasPrice', '0')) / 1e9  # Convert to Gwei
            gas_prices.append(gas_price)
        
        avg_gas = sum(gas_prices) / len(gas_prices) if gas_prices else 0
        high_gas_txs = sum(1 for gas in gas_prices if gas > avg_gas * 2)
        
        return {
            "success": True,
            "data": {
                "contract_address": contract_address,
                "network": "ethereum",
                "analysis": {
                    "total_initial_transactions": len(initial_txs),
                    "blocks_analyzed": list(target_blocks),
                    "total_tokens_transferred": round(total_transferred, 2),
                    "unique_wallets": len(wallet_accumulation),
                    "top_10_concentration": round(top_10_percentage, 2),
                    "risk_level": risk_level,
                    "exceeds_threshold": top_10_percentage > snipe_threshold,
                    "threshold_used": snipe_threshold
                },
                "top_wallets": [
                    {
                        "address": addr,
                        "tokens_acquired": round(amount, 2),
                        "percentage": round((amount / total_transferred * 100), 2)
                    } for addr, amount in top_10_wallets
                ],
                "gas_analysis": {
                    "average_gas_price_gwei": round(avg_gas, 2),
                    "high_gas_transactions": high_gas_txs,
                    "potential_snipers": high_gas_txs > len(initial_txs) * 0.3
                },
                "summary": f"{'🚨 HIGH RISK' if risk_level == 'HIGH' else '⚠️ MEDIUM RISK' if risk_level == 'MEDIUM' else '✅ LOW RISK'}: Top 10 wallets control {top_10_percentage:.1f}% of initial distribution"
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Ethereum analysis failed: {str(e)}"}

def analyze_sol_token_launch(contract_address: str, snipe_threshold: float, initial_blocks: int) -> Dict[str, Any]:
    """Analyze Solana token launch using Helius API"""
    try:
        # Try Helius API first (better data)
        helius_key = os.getenv("HELIUS_API_KEY")
        if helius_key:
            try:
                # Use Helius parsed transactions endpoint
                url = f"https://api.helius.xyz/v0/addresses/{contract_address}/transactions?api-key={helius_key}&limit=200"
                
                response = requests.get(url)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Helius API success: {len(data)} transactions found")
                    return analyze_helius_token_data(data, contract_address, snipe_threshold)
                else:
                    print(f"Helius API failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"Helius API exception: {e}")
        
        # Fallback to Solscan if Helius fails
        url = f"https://api.solscan.io/v2/token/transfer"
        headers = {}
        params = {
            'token': contract_address,
            'limit': 200,
            'offset': 0
        }
        
        solscan_key = os.getenv("SOLSCAN_API_KEY")
        if solscan_key:
            headers['Authorization'] = f'Bearer {solscan_key}'
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            return {"success": False, "error": f"Solscan API error: {response.status_code}"}
        
        data = response.json()
        transfers = data.get('data', [])
        
        if not transfers:
            return {"success": False, "error": "No token transfers found"}
        
        # Sort by time (earliest first)
        transfers.sort(key=lambda x: x.get('blockTime', 0))
        
        # Analyze first 100 transfers (initial distribution)
        initial_transfers = transfers[:100]
        
        # Track wallet accumulation
        wallet_accumulation = {}
        total_transferred = 0
        
        for transfer in initial_transfers:
            to_address = transfer.get('dst', '').strip()
            amount = float(transfer.get('amount', 0))
            
            if to_address and to_address != contract_address:
                if to_address not in wallet_accumulation:
                    wallet_accumulation[to_address] = 0
                wallet_accumulation[to_address] += amount
                total_transferred += amount
        
        # Calculate concentrations
        sorted_wallets = sorted(wallet_accumulation.items(), key=lambda x: x[1], reverse=True)
        top_10_wallets = sorted_wallets[:10]
        
        # Calculate percentages
        top_10_total = sum(amount for _, amount in top_10_wallets)
        top_10_percentage = (top_10_total / total_transferred * 100) if total_transferred > 0 else 0
        
        # Risk assessment
        risk_level = "HIGH" if top_10_percentage > snipe_threshold else "MEDIUM" if top_10_percentage > 15 else "LOW"
        
        return {
            "success": True,
            "data": {
                "contract_address": contract_address,
                "network": "solana",
                "analysis": {
                    "total_initial_transfers": len(initial_transfers),
                    "total_tokens_transferred": round(total_transferred, 2),
                    "unique_wallets": len(wallet_accumulation),
                    "top_10_concentration": round(top_10_percentage, 2),
                    "risk_level": risk_level,
                    "exceeds_threshold": top_10_percentage > snipe_threshold,
                    "threshold_used": snipe_threshold
                },
                "top_wallets": [
                    {
                        "address": addr,
                        "tokens_acquired": round(amount, 2),
                        "percentage": round((amount / total_transferred * 100), 2)
                    } for addr, amount in top_10_wallets
                ],
                "summary": f"{'🚨 HIGH RISK' if risk_level == 'HIGH' else '⚠️ MEDIUM RISK' if risk_level == 'MEDIUM' else '✅ LOW RISK'}: Top 10 wallets control {top_10_percentage:.1f}% of initial distribution"
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Solana analysis failed: {str(e)}"}

def analyze_helius_token_data(transactions: List[Dict], contract_address: str, snipe_threshold: float) -> Dict[str, Any]:
    """Analyze Helius transaction data for token launch"""
    try:
        if not transactions:
            return {"success": False, "error": "No transaction data found"}
        
        # Sort by timestamp (earliest first)
        transactions.sort(key=lambda x: x.get('timestamp', 0))
        
        # Get first 100 transactions (initial 5 seconds for pump.fun)
        initial_txs = transactions[:100]
        
        # Track wallet accumulation from token transfers
        wallet_accumulation = {}
        total_transferred = 0
        
        for tx in initial_txs:
            # Parse Helius enhanced transaction data
            token_transfers = tx.get('tokenTransfers', [])
            
            for transfer in token_transfers:
                if transfer.get('mint') == contract_address:
                    to_address = transfer.get('toUserAccount', '')
                    amount = float(transfer.get('tokenAmount', 0))
                    
                    if to_address and amount > 0:
                        if to_address not in wallet_accumulation:
                            wallet_accumulation[to_address] = 0
                        wallet_accumulation[to_address] += amount
                        total_transferred += amount
        
        if total_transferred == 0:
            return {"success": False, "error": "No token transfers found in initial transactions"}
        
        # Calculate concentrations
        sorted_wallets = sorted(wallet_accumulation.items(), key=lambda x: x[1], reverse=True)
        top_10_wallets = sorted_wallets[:10]
        
        # Calculate percentages
        top_10_total = sum(amount for _, amount in top_10_wallets)
        top_10_percentage = (top_10_total / total_transferred * 100) if total_transferred > 0 else 0
        
        # Risk assessment
        risk_level = "HIGH" if top_10_percentage > snipe_threshold else "MEDIUM" if top_10_percentage > 15 else "LOW"
        
        # Analyze transaction timing (for pump.fun sniping detection)
        timestamps = [tx.get('timestamp', 0) for tx in initial_txs]
        if timestamps:
            first_tx_time = min(timestamps)
            # Count transactions in first 5 seconds
            early_txs = sum(1 for ts in timestamps if ts - first_tx_time <= 5)
            snipe_ratio = early_txs / len(initial_txs) if initial_txs else 0
        else:
            early_txs = 0
            snipe_ratio = 0
        
        return {
            "success": True,
            "data": {
                "contract_address": contract_address,
                "network": "solana",
                "analysis": {
                    "total_initial_transactions": len(initial_txs),
                    "total_tokens_transferred": round(total_transferred, 2),
                    "unique_wallets": len(wallet_accumulation),
                    "top_10_concentration": round(top_10_percentage, 2),
                    "risk_level": risk_level,
                    "exceeds_threshold": top_10_percentage > snipe_threshold,
                    "threshold_used": snipe_threshold,
                    "early_transactions": early_txs,
                    "snipe_ratio": round(snipe_ratio * 100, 2)
                },
                "top_wallets": [
                    {
                        "address": addr,
                        "tokens_acquired": round(amount, 2),
                        "percentage": round((amount / total_transferred * 100), 2)
                    } for addr, amount in top_10_wallets
                ],
                "timing_analysis": {
                    "transactions_first_5_seconds": early_txs,
                    "snipe_percentage": round(snipe_ratio * 100, 2),
                    "likely_coordinated": snipe_ratio > 0.5
                },
                "summary": f"{'🚨 HIGH RISK' if risk_level == 'HIGH' else '⚠️ MEDIUM RISK' if risk_level == 'MEDIUM' else '✅ LOW RISK'}: Top 10 wallets control {top_10_percentage:.1f}% of initial distribution. {early_txs} transactions in first 5 seconds ({snipe_ratio*100:.1f}% snipe ratio)",
                "api_used": "Helius"
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Helius data analysis failed: {str(e)}"}

def solscan_api_call(endpoint: str, token: Optional[str] = None, account: Optional[str] = None, 
                     limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Generic Solscan API caller with proper authentication"""
    try:
        # Try different Solscan API versions
        base_urls = [
            "https://api.solscan.io/v2",
            "https://api.solscan.io",
            "https://pro-api.solscan.io"
        ]
        
        solscan_key = os.getenv("SOLSCAN_API_KEY")
        if not solscan_key:
            return {"success": False, "error": "Solscan API key not configured"}
        
        headers = {
            'Authorization': f'Bearer {solscan_key}',
            'Accept': 'application/json'
        }
        
        # Build parameters
        params = {
            'limit': limit,
            'offset': offset
        }
        
        if token:
            params['token'] = token
        if account:
            params['account'] = account
        
        # Try each base URL
        for base_url in base_urls:
            try:
                url = f"{base_url}/{endpoint.lstrip('/')}"
                print(f"Trying Solscan API: {url}")
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "data": data,
                        "api_used": base_url,
                        "endpoint": endpoint,
                        "status_code": response.status_code
                    }
                elif response.status_code == 403:
                    print(f"403 Forbidden for {base_url} - trying next...")
                    continue
                else:
                    print(f"Status {response.status_code} for {base_url}: {response.text}")
                    
            except Exception as e:
                print(f"Error with {base_url}: {e}")
                continue
        
        return {
            "success": False, 
            "error": "All Solscan API endpoints failed",
            "tried_urls": base_urls,
            "last_status": response.status_code if 'response' in locals() else "No response"
        }
        
    except Exception as e:
        return {"success": False, "error": f"Solscan API call failed: {str(e)}"}

# Database functions
def download_krom_calls(limit: int = 1000) -> Dict[str, Any]:
    """Download KROM calls and store in SQLite database"""
    try:
        # Ensure database exists
        if not os.path.exists('krom_calls.db'):
            return {"success": False, "error": "Database not found. Run setup-krom-database.py first."}
        
        # Fetch calls from API
        krom_result = get_krom_calls(min(limit, 10000))
        if not krom_result.get("success"):
            return krom_result
        
        # Extract calls from the nested structure
        data = krom_result.get("data", {})
        calls_data = data.get("calls", []) if isinstance(data, dict) else data
        
        # Debug logging
        print(f"DEBUG: data type: {type(data)}")
        print(f"DEBUG: data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        print(f"DEBUG: calls_data type: {type(calls_data)}")
        if calls_data and len(calls_data) > 0:
            print(f"DEBUG: First call type: {type(calls_data[0])}")
            print(f"DEBUG: First call keys: {calls_data[0].keys() if isinstance(calls_data[0], dict) else 'Not a dict'}")
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            inserted_count = 0
            updated_count = 0
            
            for i, call in enumerate(calls_data):
                try:
                    # Validate call structure
                    if not isinstance(call, dict):
                        print(f"DEBUG: Call {i} is not a dict: {type(call)} - {call}")
                        continue
                    
                    call_id = call.get('id')
                    if not call_id:
                        print(f"DEBUG: Call {i} missing 'id' field. Keys: {call.keys()}")
                        continue
                    
                    # Check if call already exists
                    cursor.execute("SELECT id FROM calls WHERE id = ?", (call_id,))
                    exists = cursor.fetchone()
                except Exception as e:
                    print(f"DEBUG: Error processing call {i}: {e}")
                    print(f"DEBUG: call type: {type(call)}")
                    print(f"DEBUG: call keys: {call.keys() if isinstance(call, dict) else 'Not a dict'}")
                    if isinstance(call, dict) and 'id' in call:
                        print(f"DEBUG: call id: {call['id']}")
                    raise
                
                if exists:
                    # Update existing call
                    cursor.execute('''
                        UPDATE calls SET 
                            current_price = ?, roi = ?, profit_percent = ?, 
                            status = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (
                        call['current_price'], call['roi'], call['profit_percent'],
                        call['status'], call['id']
                    ))
                    updated_count += 1
                else:
                    # Insert new call
                    cursor.execute('''
                        INSERT INTO calls (
                            id, ticker, name, contract, network, market_cap,
                            buy_price, top_price, current_price, roi, profit_percent,
                            status, call_timestamp, message, image_url
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        call['id'], call['ticker'], call['name'], call['contract'],
                        call['network'], call['market_cap'], call['buy_price'],
                        call['top_price'], call['current_price'], call['roi'],
                        call['profit_percent'], call['status'], call['call_timestamp'],
                        call['message'], call['image_url']
                    ))
                    inserted_count += 1
                    
                    # Handle group data
                    group_data = call.get('group', {})
                    if group_data.get('name'):
                        # Insert or update group
                        cursor.execute('''
                            INSERT OR REPLACE INTO groups (
                                name, win_rate_30d, profit_30d, total_calls, call_frequency
                            ) VALUES (?, ?, ?, ?, ?)
                        ''', (
                            group_data['name'], group_data.get('win_rate_30d', 0),
                            group_data.get('profit_30d', 0), group_data.get('total_calls', 0),
                            group_data.get('call_frequency', 0)
                        ))
                        
                        # Group is already stored in the calls table, no need for separate linking
            
            conn.commit()
            conn.close()
            
        return {
            "success": True,
            "data": {
                "total_processed": len(calls_data),
                "new_calls": inserted_count,
                "updated_calls": updated_count,
                "message": f"Successfully downloaded {len(calls_data)} calls"
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Database operation failed: {str(e)}"}

def query_krom_database(query: str, params: List = None) -> Dict[str, Any]:
    """Execute SQL query on KROM database"""
    try:
        if not os.path.exists('krom_calls.db'):
            return {"success": False, "error": "Database not found. Run download_krom_calls first."}
        
        # Basic SQL injection prevention
        forbidden_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        query_upper = query.upper()
        for keyword in forbidden_keywords:
            if keyword in query_upper and not query_upper.startswith('SELECT'):
                return {"success": False, "error": f"Query contains forbidden keyword: {keyword}"}
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            columns = [description[0] for description in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            conn.close()
            
            # Convert rows to dictionaries
            results = [dict(row) for row in rows]
            
        return {
            "success": True,
            "data": {
                "columns": columns,
                "rows": results,
                "count": len(results)
            }
        }
        
    except Exception as e:
        return {"success": False, "error": f"Query failed: {str(e)}"}

def analyze_krom_stats(analysis_type: str, timeframe: str = "all", group_name: str = None) -> Dict[str, Any]:
    """Perform statistical analysis on KROM calls data"""
    try:
        if not os.path.exists('krom_calls.db'):
            return {"success": False, "error": "Database not found. Run download_krom_calls first."}
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build timeframe filter
            timeframe_filter = ""
            if timeframe == "7d":
                timeframe_filter = "AND datetime(call_timestamp) >= datetime('now', '-7 days')"
            elif timeframe == "30d":
                timeframe_filter = "AND datetime(call_timestamp) >= datetime('now', '-30 days')"
            elif timeframe == "90d":
                timeframe_filter = "AND datetime(call_timestamp) >= datetime('now', '-90 days')"
            
            # Build group filter
            group_filter = ""
            if group_name:
                group_filter = f"AND g.name = '{group_name}'"
            
            if analysis_type == "overview":
                cursor.execute(f'''
                    SELECT 
                        COUNT(*) as total_calls,
                        COUNT(CASE WHEN status = 'profit' THEN 1 END) as profitable_calls,
                        COUNT(CASE WHEN status = 'loss' THEN 1 END) as loss_calls,
                        ROUND(AVG(roi), 2) as avg_roi,
                        ROUND(MAX(roi), 2) as max_roi,
                        ROUND(MIN(roi), 2) as min_roi,
                        ROUND(AVG(profit_percent), 2) as avg_profit_percent,
                        COUNT(DISTINCT ticker) as unique_tokens
                    FROM calls
                    WHERE 1=1 {timeframe_filter}
                ''')
                overview = dict(cursor.fetchone())
                
                # Calculate win rate
                if overview['total_calls'] > 0:
                    overview['win_rate'] = round(
                        (overview['profitable_calls'] / overview['total_calls']) * 100, 2
                    )
                else:
                    overview['win_rate'] = 0
                
                return {"success": True, "data": overview}
            
            elif analysis_type == "groups":
                cursor.execute(f'''
                    SELECT 
                        group_name as name,
                        COUNT(id) as calls_count,
                        ROUND(AVG(roi), 2) as avg_roi,
                        COUNT(CASE WHEN roi > 1 THEN 1 END) as wins,
                        ROUND(CAST(COUNT(CASE WHEN roi > 1 THEN 1 END) AS FLOAT) / COUNT(id) * 100, 2) as win_rate
                    FROM calls
                    WHERE group_name IS NOT NULL {timeframe_filter} {group_filter}
                    GROUP BY group_name
                    ORDER BY calls_count DESC
                ''')
                groups = [dict(row) for row in cursor.fetchall()]
                
                return {"success": True, "data": groups}
            
            elif analysis_type == "performance":
                cursor.execute(f'''
                    SELECT 
                        ticker,
                        name,
                        COUNT(*) as call_count,
                        ROUND(AVG(roi), 2) as avg_roi,
                        ROUND(MAX(roi), 2) as max_roi,
                        ROUND(AVG(profit_percent), 2) as avg_profit
                    FROM calls
                    WHERE 1=1 {timeframe_filter}
                    GROUP BY ticker
                    HAVING COUNT(*) > 1
                    ORDER BY avg_roi DESC
                    LIMIT 20
                ''')
                performance = [dict(row) for row in cursor.fetchall()]
                
                return {"success": True, "data": performance}
            
            elif analysis_type == "trends":
                cursor.execute(f'''
                    SELECT 
                        date(call_timestamp) as date,
                        COUNT(*) as calls,
                        COUNT(CASE WHEN status = 'profit' THEN 1 END) as wins,
                        ROUND(AVG(roi), 2) as avg_roi
                    FROM calls
                    WHERE 1=1 {timeframe_filter}
                    GROUP BY date(call_timestamp)
                    ORDER BY date DESC
                    LIMIT 30
                ''')
                trends = [dict(row) for row in cursor.fetchall()]
                
                return {"success": True, "data": trends}
            
            elif analysis_type == "top_performers":
                cursor.execute(f'''
                    SELECT 
                        symbol as ticker,
                        token_symbol as name,
                        roi,
                        ROUND((roi - 1) * 100, 2) as profit_percent,
                        buy_price,
                        top_price,
                        buy_timestamp as call_timestamp,
                        group_name
                    FROM calls
                    WHERE roi > 2 {timeframe_filter} {group_filter}
                    ORDER BY roi DESC
                    LIMIT 50
                ''')
                top_performers = [dict(row) for row in cursor.fetchall()]
                
                return {"success": True, "data": top_performers}
            
            else:
                return {"success": False, "error": f"Unknown analysis type: {analysis_type}"}
            
            conn.close()
            
    except Exception as e:
        return {"success": False, "error": f"Analysis failed: {str(e)}"}

def create_chart(query: str, chart_type: str = "bar", title: str = "Chart") -> Dict[str, Any]:
    """Simpler chart creation tool that just runs SQL and returns visualization"""
    try:
        conn = get_db_connection()
        df = pd.read_sql(query, conn)
        
        # Assume first column is labels, second is values
        if len(df.columns) >= 2:
            result = {
                'labels': df.iloc[:, 0].tolist(),
                'values': df.iloc[:, 1].tolist()
            }
            
            return {
                "success": True,
                "data": result,
                "visualization": {
                    "type": chart_type,
                    "title": title,
                    "data": result
                }
            }
        else:
            return {"success": False, "error": "Query must return at least 2 columns"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_analysis(code: str, visualization_type: str = "chart", title: str = "Analysis Result") -> Dict[str, Any]:
    """Execute Python code for custom data analysis in a sandboxed environment"""
    logger.info(f"=== Execute Analysis Started ===")
    logger.info(f"Visualization type: {visualization_type}")
    logger.info(f"Title: {title}")
    logger.debug(f"Code to execute:\n{code[:500]}...")
    
    import pandas as pd
    import numpy as np
    from io import StringIO
    import sys
    import ast
    
    # Security check - basic validation
    forbidden_imports = ['os', 'subprocess', 'eval', 'exec', '__import__', 'open', 'file', 'input', 'raw_input']
    code_lower = code.lower()
    for forbidden in forbidden_imports:
        if forbidden in code_lower:
            return {"success": False, "error": f"Forbidden operation: {forbidden}"}
    
    # Create sandboxed environment
    sandbox_globals = {
        'pd': pd,
        'np': np,
        'get_db_connection': get_db_connection,
        # Don't include datetime directly to avoid os module issues
        # 'datetime': datetime,
        'json': json,
        'sqlite3': sqlite3,
        '__builtins__': {
            'print': print,
            'len': len,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'sorted': sorted,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'type': type,
            'isinstance': isinstance,
            'hasattr': hasattr,
            'getattr': getattr,
            'any': any,
            'all': all,
        }
    }
    
    # Capture output
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        # Execute the code
        exec(code, sandbox_globals)
        output = sys.stdout.getvalue()
        
        # Check if result variable exists
        if 'result' in sandbox_globals:
            result = sandbox_globals['result']
            
            # Log result info
            if isinstance(result, pd.DataFrame):
                logger.info(f"Result is DataFrame: {len(result)} rows, {len(result.columns)} columns")
                result = {
                    'columns': result.columns.tolist(),
                    'data': result.to_dict('records'),
                    'index': result.index.tolist()
                }
            elif isinstance(result, dict):
                logger.info(f"Result is dict with {len(result)} keys")
            elif isinstance(result, list):
                logger.info(f"Result is list with {len(result)} items")
            else:
                logger.info(f"Result type: {type(result)}")
            
            logger.info(f"Successfully executed analysis, returning visualization data")
            return {
                "success": True,
                "data": result,
                "output": output,
                "visualization": {
                    "type": visualization_type,
                    "title": title,
                    "data": result
                }
            }
        else:
            return {
                "success": True,
                "output": output,
                "message": "Code executed successfully. Set 'result' variable to return data."
            }
    
    except Exception as e:
        output = sys.stdout.getvalue()
        error_detail = f"{type(e).__name__}: {str(e)}"
        
        # Add line number if available
        import traceback
        tb = traceback.format_exc()
        if "line" in tb:
            lines = tb.split('\n')
            for line in lines:
                if "line" in line and "<string>" in line:
                    error_detail += f"\n{line.strip()}"
                    break
        
        if output:
            error_detail += f"\n\nPython output:\n{output}"
        
        logger.error(f"Execute analysis error: {error_detail}")
        return {"success": False, "error": error_detail, "output": output}
    
    finally:
        sys.stdout = old_stdout

# Execute tool function
def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool with given parameters"""
    tool_map = {
        "get_crypto_price": get_crypto_price,
        "get_market_sentiment": get_market_sentiment,
        "get_crypto_news": get_crypto_news,
        "get_whale_transactions": get_whale_transactions,
        "get_krom_calls": get_krom_calls,
        "get_token_info": get_token_info,
        "get_token_transactions": get_token_transactions,
        "analyze_wallet": analyze_wallet,
        "call_api": call_api,
        "create_tool": create_tool,
        "analyze_token_launch": analyze_token_launch,
        "solscan_api_call": solscan_api_call,
        "download_krom_calls": download_krom_calls,
        "query_krom_database": query_krom_database,
        "analyze_krom_stats": analyze_krom_stats,
        "create_chart": create_chart,
        "execute_analysis": execute_analysis
    }
    
    # Check static tools first
    if tool_name in tool_map:
        try:
            result = tool_map[tool_name](**params)
            return result
        except TypeError as e:
            return {"success": False, "error": f"Invalid parameters for {tool_name}: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Tool execution error: {str(e)}"}
    
    # Check dynamic tools
    elif tool_name in dynamic_tools:
        return call_dynamic_tool(tool_name, params)
    
    else:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

def create_tool_descriptions() -> str:
    """Create a formatted description of all available tools"""
    descriptions = []
    
    # Static tools
    for tool_name, tool_info in AVAILABLE_TOOLS.items():
        params_str = ", ".join([
            f"{p}: {info['type']}" + (" (required)" if p in tool_info.get('required', []) else " (optional)")
            for p, info in tool_info.get('parameters', {}).items()
        ])
        descriptions.append(f"- {tool_name}({params_str}): {tool_info['description']}")
    
    # Dynamic tools (session-specific)
    if dynamic_tools:
        descriptions.append("\n## Dynamic Tools (Created This Session)")
        for tool_name, tool_def in dynamic_tools.items():
            required_str = ", ".join(tool_def['required_params']) if tool_def['required_params'] else "none"
            optional_str = ", ".join(tool_def['optional_params']) if tool_def['optional_params'] else "none"
            descriptions.append(f"- {tool_name}(required: {required_str}, optional: {optional_str}): {tool_def['description']}")
    
    return "\n".join(descriptions)

def parse_tool_calls_old(response_text: str) -> List[Dict[str, Any]]:
    """Parse tool calls from Claude's response"""
    tool_calls = []
    logger.info(f"Parsing tool calls from response of length {len(response_text)}")
    
    # Look for tool call patterns in the response
    # Pattern 1: JSON blocks with tool calls
    # The .*? is non-greedy to match the first closing brace at the right level
    json_pattern = r'```json\s*\n\s*(\{[^`]*?\n\})\s*\n\s*```'
    json_matches = re.findall(json_pattern, response_text, re.DOTALL)
    logger.info(f"Found {len(json_matches)} JSON blocks")
    
    if not json_matches:
        # Try a more flexible pattern
        json_pattern2 = r'```json\s*(\{[\s\S]*?\})\s*```'
        json_matches = re.findall(json_pattern2, response_text)
        logger.info(f"Found {len(json_matches)} JSON blocks with flexible pattern")
    
    for i, match in enumerate(json_matches):
        try:
            logger.info(f"Attempting to parse JSON block {i+1}: {match[:100]}...")
            
            # The AI is using Python triple-quoted strings in JSON, which isn't valid
            # We need to extract the actual content and create valid JSON
            if '"""' in match:
                # Extract the code from the params
                import re as re2
                # Match the structure: "code": """actual code"""
                code_pattern = r'"code":\s*"""([\s\S]*?)"""'
                code_match = re2.search(code_pattern, match)
                
                if code_match:
                    # Extract the code content
                    code_content = code_match.group(1)
                    # Escape the code content for JSON
                    escaped_code = json.dumps(code_content)
                    # Replace the triple-quoted section with properly escaped JSON string
                    cleaned_match = re2.sub(code_pattern, f'"code": {escaped_code}', match)
                else:
                    cleaned_match = match
            else:
                cleaned_match = match
            
            # Try to parse the cleaned JSON
            call_data = json.loads(cleaned_match)
            if 'tool' in call_data:
                logger.info(f"Found tool call: {call_data['tool']}")
                tool_calls.append({
                    'tool': call_data['tool'],
                    'params': call_data.get('params', {})
                })
            else:
                logger.warning(f"JSON block {i+1} missing 'tool' key. Keys: {list(call_data.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON block {i+1}: {e}")
            logger.error(f"JSON content: {match[:200]}...")
            
            # Try a more aggressive fix for triple-quoted strings
            if '"""' in match:
                try:
                    # Replace all triple quotes with escaped quotes
                    fixed_match = match
                    # Find all triple-quoted sections and replace them
                    parts = fixed_match.split('"""')
                    if len(parts) >= 3:
                        # Reconstruct with proper JSON escaping
                        code_content = parts[1]
                        # Escape newlines and quotes
                        escaped = code_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                        fixed_match = parts[0] + '"' + escaped + '"' + '"""'.join(parts[2:])
                        fixed_match = fixed_match.replace('"""', '"')
                        
                        logger.info(f"Trying aggressive fix for triple quotes...")
                        call_data = json.loads(fixed_match)
                        if 'tool' in call_data:
                            logger.info(f"Success! Found tool call: {call_data['tool']}")
                            tool_calls.append({
                                'tool': call_data['tool'],
                                'params': call_data.get('params', {})
                            })
                            continue
                except Exception as e2:
                    logger.error(f"Aggressive fix also failed: {e2}")
            
            # Last resort: try to extract tool and code manually
            try:
                if '"tool": "execute_analysis"' in match and '"code":' in match:
                    logger.info("Trying manual extraction for execute_analysis...")
                    # Extract code between triple quotes
                    code_start = match.find('"""') + 3
                    code_end = match.rfind('"""')
                    if code_start > 3 and code_end > code_start:
                        code = match[code_start:code_end]
                        # Extract other params
                        viz_type = "chart"
                        if '"visualization_type":' in match:
                            import re as re3
                            viz_match = re3.search(r'"visualization_type":\s*"([^"]+)"', match)
                            if viz_match:
                                viz_type = viz_match.group(1)
                        
                        logger.info("Manual extraction successful!")
                        tool_calls.append({
                            'tool': 'execute_analysis',
                            'params': {
                                'code': code,
                                'visualization_type': viz_type
                            }
                        })
                        continue
            except Exception as e3:
                logger.error(f"Manual extraction failed: {e3}")
            
            continue
    
    # Pattern 2: Function call syntax
    func_pattern = r'(\w+)\((.*?)\)'
    func_matches = re.findall(func_pattern, response_text)
    
    for func_name, params_str in func_matches:
        if func_name in AVAILABLE_TOOLS:
            # Try to parse parameters
            params = {}
            if params_str:
                # Simple parameter parsing (handles key=value format)
                param_pattern = r'(\w+)=(["\']?)([^"\']*)\2'
                param_matches = re.findall(param_pattern, params_str)
                for param_name, _, param_value in param_matches:
                    # Try to convert to appropriate type
                    try:
                        if param_value.lower() in ['true', 'false']:
                            params[param_name] = param_value.lower() == 'true'
                        elif param_value.isdigit():
                            params[param_name] = int(param_value)
                        else:
                            params[param_name] = param_value
                    except:
                        params[param_name] = param_value
            
            tool_calls.append({
                'tool': func_name,
                'params': params
            })
    
    return tool_calls

def parse_tool_calls(response_text: str) -> List[Dict[str, Any]]:
    """New simplified parser that handles triple-quoted strings"""
    tool_calls = []
    
    # Find all JSON code blocks
    import re
    json_blocks = re.findall(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    
    logger.info(f"Found {len(json_blocks)} JSON blocks in response")
    
    for i, block in enumerate(json_blocks):
        logger.info(f"Processing block {i+1}, length: {len(block)}")
        # Check if this looks like a tool call
        if '"tool"' not in block:
            continue
            
        # Special handling for execute_analysis with triple quotes
        if '"tool": "execute_analysis"' in block and '"""' in block:
            try:
                # Extract tool name
                tool_match = re.search(r'"tool":\s*"([^"]+)"', block)
                if not tool_match:
                    continue
                    
                tool_name = tool_match.group(1)
                
                # Extract code between triple quotes
                code_match = re.search(r'"code":\s*"""(.*?)"""', block, re.DOTALL)
                if not code_match:
                    continue
                    
                code = code_match.group(1)
                
                # Extract visualization type if present
                viz_type = "chart"
                viz_match = re.search(r'"visualization_type":\s*"([^"]+)"', block)
                if viz_match:
                    viz_type = viz_match.group(1)
                
                # Extract title if present
                title = "Analysis Result"
                title_match = re.search(r'"title":\s*"([^"]+)"', block)
                if title_match:
                    title = title_match.group(1)
                
                tool_calls.append({
                    'tool': tool_name,
                    'params': {
                        'code': code,
                        'visualization_type': viz_type,
                        'title': title
                    }
                })
                logger.info(f"Successfully parsed execute_analysis tool call")
                
            except Exception as e:
                logger.error(f"Failed to parse execute_analysis block: {e}")
                continue
        else:
            # Try standard JSON parsing for other tools
            try:
                # Clean up common issues
                cleaned = block.strip()
                if cleaned.endswith(','):
                    cleaned = cleaned[:-1]
                    
                tool_data = json.loads(cleaned)
                if 'tool' in tool_data:
                    tool_calls.append({
                        'tool': tool_data['tool'],
                        'params': tool_data.get('params', {})
                    })
                    logger.info(f"Successfully parsed {tool_data['tool']} tool call")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse as JSON: {block[:100]}...")
                continue
    
    logger.info(f"Found {len(tool_calls)} tool calls total")
    return tool_calls

def analyze_with_mcp(user_message: str, session_id: str = "default") -> Dict[str, Any]:
    """True MCP implementation - AI has full control over tool usage"""
    logger.info(f"=== MCP Analysis Started ===")
    logger.info(f"Session: {session_id}")
    logger.info(f"User message: {user_message[:100]}...")
    
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not anthropic_key:
        return {
            "response": """I need an Anthropic API key to provide intelligent responses.

To enable AI features:
1. Get an API key from https://console.anthropic.com/
2. Add it to your .env file: ANTHROPIC_API_KEY=your_key_here
3. Restart the server

Once configured, I'll be able to use all available crypto analysis tools intelligently.""",
            "needs_ai_key": True
        }
    
    try:
        client = anthropic.Anthropic(api_key=anthropic_key)
        
        # Get or create conversation history
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        # Aggressively limit conversation history to prevent token overflow
        # Keep only last 4 messages (2 exchanges)
        if len(conversation_history[session_id]) > 4:
            logger.info(f"Trimming conversation history from {len(conversation_history[session_id])} to 4 messages")
            conversation_history[session_id] = conversation_history[session_id][-4:]
        
        # Also truncate very long messages (e.g., large tool results)
        for i, msg in enumerate(conversation_history[session_id]):
            if len(msg['content']) > 10000:  # ~2500 tokens
                logger.warning(f"Truncating message {i} from {len(msg['content'])} to 10000 chars")
                conversation_history[session_id][i]['content'] = msg['content'][:10000] + "...[truncated]"
        
        # Use the system prompt template with tool descriptions
        tool_descriptions = create_tool_descriptions()
        print(f"Tool descriptions length: {len(tool_descriptions)} characters")
        system_prompt = system_prompt_template + f"""

## Available Tools

{tool_descriptions}

When you need to use a tool, include a JSON code block in your response like this:
```json
{{"tool": "tool_name", "params": {{"param1": "value1", "param2": value2}}}}
```

CRITICAL JSON RULES:
- NEVER use triple quotes (\"\"\") in JSON
- For multi-line strings like code, use proper JSON escaping
- Newlines must be escaped as \\n
- Example for execute_analysis:
```json
{{
    "tool": "execute_analysis",
    "params": {{
        "code": "import pandas as pd\\nimport numpy as np\\n\\nconn = get_db_connection()\\nquery = 'SELECT * FROM calls LIMIT 10'\\ndf = pd.read_sql(query, conn)\\nresult = {{'labels': df['symbol'].tolist(), 'values': df['roi'].tolist()}}",
        "visualization_type": "bar"
    }}
}}
```

You can call multiple tools in a single response. Each tool call should be in its own JSON block.

## Important Guidelines

1. **Tool Selection**: Choose tools based on what the user is asking for. You have complete freedom to:
   - Use multiple tools to gather comprehensive data
   - Chain tool calls to get deeper insights
   - Combine data from different sources creatively

2. **Parameter Inference**: If the user doesn't specify all parameters:
   - Use sensible defaults (e.g., limit=100 for get_krom_calls)
   - Ask for clarification if critical parameters are missing
   - For optional parameters, omit them to use defaults

3. **Dynamic Tool Creation**: When you need data from an API not covered by existing tools:
   - Use create_tool to build a custom tool for that API
   - Test it with example parameters
   - Then use the new tool to get the data
   - Tools are available for the rest of the session

4. **Response Format**: After calling tools, incorporate the results naturally into your response. Use HTML formatting:
   - <strong> for emphasis
   - <br> for line breaks
   - <ul>/<li> for lists
   - <a href="url"> for links

5. **Error Handling**: If a tool returns an error, acknowledge it and try alternatives if possible.

6. **Be Concise**: Unless asked for analysis or details, keep responses short and to the point.

Remember: You have full autonomy to use these tools creatively to provide the best possible crypto analysis and insights."""
        
        # Add user message to history
        conversation_history[session_id].append({
            "role": "user",
            "content": user_message
        })
        
        
        # First pass - let Claude decide what tools to use
        initial_messages = conversation_history[session_id].copy()
        
        # Debug: Check total message size
        total_chars = len(system_prompt) + sum(len(msg['content']) for msg in initial_messages)
        print(f"System prompt length: {len(system_prompt)} chars")
        print(f"Conversation history messages: {len(initial_messages)}")
        print(f"Total prompt length: {total_chars} chars (~{total_chars//4} tokens)")
        
        initial_response = client.messages.create(
            model="claude-3-haiku-20240307",  # Using cheaper model to save costs
            max_tokens=1500,
            temperature=0.7,
            system=system_prompt,
            messages=initial_messages
        )
        
        response_text = initial_response.content[0].text
        
        # Parse tool calls from response
        tool_calls = parse_tool_calls(response_text)
        logger.info(f"Parsed {len(tool_calls)} tool calls from response")
        for call in tool_calls:
            logger.info(f"Tool call: {call['tool']} with params keys: {list(call.get('params', {}).keys())}")
        
        # Execute tool calls
        tool_results = {}
        for call in tool_calls:
            tool_name = call['tool']
            params = call['params']
            
            logger.info(f"Executing tool: {tool_name}")
            logger.debug(f"Tool params: {json.dumps(params, indent=2)}")
            
            result = execute_tool(tool_name, params)
            
            # Log result size and content
            result_str = json.dumps(result) if isinstance(result, dict) else str(result)
            logger.info(f"Tool {tool_name} returned {len(result_str)} chars")
            
            # Special logging for execute_analysis
            if tool_name == "execute_analysis" and isinstance(result, dict):
                logger.info(f"Execute analysis result keys: {list(result.keys())}")
                logger.info(f"Execute analysis success: {result.get('success')}")
                if 'visualization' in result:
                    logger.info(f"Visualization found in execute_analysis result: {result['visualization']}")
            
            if len(result_str) > 1000:
                logger.warning(f"Large result from {tool_name}: {len(result_str)} chars")
            
            tool_results[f"{tool_name}_{len(tool_results)}"] = result
        
        # If tools were called, make a second pass with the results
        if tool_results:
            # Create enhanced message with tool results
            # Truncate large results to prevent token overflow
            tool_results_str = json.dumps(tool_results, indent=2)
            if len(tool_results_str) > 50000:  # ~12k tokens
                tool_results_str = tool_results_str[:50000] + "\n... [truncated]"
            
            # Check if any tool failed and needs error reporting
            error_messages = []
            for tool_id, result in tool_results.items():
                if isinstance(result, dict) and result.get('success') == False:
                    tool_name = tool_id.split('_')[0]
                    error = result.get('error', 'Unknown error')
                    error_messages.append(f"{tool_name}: {error}")
            
            if error_messages:
                logger.warning(f"Tool errors found: {error_messages}")
                enhanced_message = f"""Tool execution errors occurred:

{chr(10).join(error_messages)}

Tool results:
{tool_results_str}

Please explain these errors to the user clearly and suggest how to fix them. If it's a Python syntax error, show the correct syntax. Be specific about what went wrong."""
            else:
                enhanced_message = f"""Tool results:

{tool_results_str}

Please answer the user's original question using this data. Be concise."""
            
            # Add tool results to conversation
            conversation_history[session_id].append({
                "role": "assistant",
                "content": response_text
            })
            conversation_history[session_id].append({
                "role": "user", 
                "content": enhanced_message
            })
            
            # Get final response with tool results
            final_response = client.messages.create(
                model="claude-3-haiku-20240307",  # Using cheaper model to save costs
                max_tokens=2000,
                temperature=0.7,
                system=system_prompt + "\n\nIMPORTANT: The user has provided tool results. Use this data to answer the user's question CONCISELY. Do NOT call tools again - just use the provided data. Remember: Be brief unless asked for details.",
                messages=conversation_history[session_id]
            )
            
            final_text = final_response.content[0].text
            
            # Update conversation history with final response
            conversation_history[session_id][-1] = {
                "role": "assistant",
                "content": final_text
            }
            
            # Check for visualization data in tool results
            visualization = None
            logger.info(f"Checking tool results for visualization data...")
            logger.info(f"Tool results keys: {list(tool_results.keys())}")
            for key, result in tool_results.items():
                logger.info(f"Tool result {key}: type={type(result)}, keys={result.keys() if isinstance(result, dict) else 'N/A'}")
                if isinstance(result, dict):
                    logger.info(f"Tool result {key} success: {result.get('success', 'N/A')}")
                    if 'visualization' in result:
                        logger.info(f"Found visualization data in {key}")
                        visualization = result['visualization']
                        if 'data' in result:
                            visualization['data'] = result['data']
                        break
                    else:
                        logger.info(f"No visualization key in {key}, available keys: {list(result.keys())}")
            
            if visualization:
                logger.info(f"Visualization will be sent to frontend: {visualization}")
            else:
                logger.warning("No visualization data found in tool results")
            
            response_data = {
                "response": final_text,
                "tools_used": [call['tool'] for call in tool_calls]
            }
            
            if visualization:
                response_data['visualization'] = visualization
            
            return response_data
        else:
            # No tools were called, use the initial response
            conversation_history[session_id].append({
                "role": "assistant",
                "content": response_text
            })
            
            return {
                "response": response_text,
                "tools_used": []
            }
        
    except Exception as e:
        logger.error(f"MCP Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": f"I encountered an error: {str(e)}. Please try again.",
            "error": True
        }
    finally:
        logger.info(f"=== MCP Analysis Complete ===\n")

# API Endpoints
@app.route('/api/chat', methods=['POST'])
def chat():
    """MCP-powered chat endpoint"""
    try:
        data = request.json
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        print(f"\n=== New Message ===")
        print(f"Session: {session_id}")
        print(f"Message: {user_message}")
        
        # Use MCP implementation
        result = analyze_with_mcp(user_message, session_id)
        
        if 'tools_used' in result:
            print(f"Tools used: {result['tools_used']}")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        return jsonify({
            "response": f"Sorry, I encountered an error: {str(e)}. Please try again.",
            "error": True
        }), 500

@app.route('/api/visualization/<viz_type>', methods=['GET'])
def get_visualization_data(viz_type):
    """Get data for various visualizations"""
    try:
        if viz_type == 'overview':
            # Get overview statistics
            result = analyze_krom_stats('overview')
            return jsonify(result)
            
        elif viz_type == 'roi_distribution':
            # Get ROI distribution data
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN roi < 0.5 THEN '0-0.5x'
                        WHEN roi < 1 THEN '0.5-1x'
                        WHEN roi < 2 THEN '1-2x'
                        WHEN roi < 3 THEN '2-3x'
                        WHEN roi < 5 THEN '3-5x'
                        ELSE '5x+'
                    END as roi_range,
                    COUNT(*) as count
                FROM calls
                GROUP BY roi_range
                ORDER BY 
                    CASE roi_range
                        WHEN '0-0.5x' THEN 1
                        WHEN '0.5-1x' THEN 2
                        WHEN '1-2x' THEN 3
                        WHEN '2-3x' THEN 4
                        WHEN '3-5x' THEN 5
                        ELSE 6
                    END
            """)
            data = [{'range': row[0], 'count': row[1]} for row in cursor.fetchall()]
            conn.close()
            return jsonify({"success": True, "data": data})
            
        elif viz_type == 'daily_performance':
            # Get daily performance data
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    date(call_timestamp) as date,
                    COUNT(*) as calls,
                    COUNT(CASE WHEN status = 'profit' THEN 1 END) as wins,
                    ROUND(AVG(roi), 2) as avg_roi
                FROM calls
                WHERE call_timestamp IS NOT NULL
                GROUP BY date(call_timestamp)
                ORDER BY date DESC
                LIMIT 30
            """)
            data = [{'date': row[0], 'calls': row[1], 'wins': row[2], 'avg_roi': row[3]} 
                   for row in cursor.fetchall()]
            conn.close()
            return jsonify({"success": True, "data": data})
            
        elif viz_type == 'network_distribution':
            # Get network distribution
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT network, COUNT(*) as count
                FROM calls
                GROUP BY network
                ORDER BY count DESC
            """)
            data = [{'network': row[0], 'count': row[1]} for row in cursor.fetchall()]
            conn.close()
            return jsonify({"success": True, "data": data})
            
        elif viz_type == 'top_groups':
            # Get top performing groups
            result = analyze_krom_stats('groups')
            return jsonify(result)
            
        else:
            return jsonify({"success": False, "error": "Unknown visualization type"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/calls', methods=['GET'])
def get_calls_paginated():
    """Get paginated KROM calls from database"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        sort_by = request.args.get('sort_by', 'call_timestamp')
        sort_order = request.args.get('sort_order', 'DESC')
        
        # Validate inputs
        if page < 1:
            page = 1
        if per_page > 100:
            per_page = 100
            
        offset = (page - 1) * per_page
        
        # Allowed sort columns
        allowed_sorts = ['buy_timestamp', 'roi', 'symbol', 'network']
        if sort_by not in allowed_sorts:
            sort_by = 'buy_timestamp'
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'DESC'
            
        conn = sqlite3.connect('krom_calls.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM calls")
        total_count = cursor.fetchone()['total']
        
        # Get paginated data
        query = f"""
            SELECT *
            FROM calls
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, (per_page, offset))
        
        calls = []
        for row in cursor.fetchall():
            call = dict(row)
            # Format timestamps
            if call.get('buy_timestamp'):
                try:
                    from datetime import datetime
                    # buy_timestamp is in milliseconds
                    dt = datetime.fromtimestamp(call['buy_timestamp'] / 1000)
                    call['formatted_date'] = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    call['formatted_date'] = str(call['buy_timestamp'])
            calls.append(call)
            
        conn.close()
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return jsonify({
            "success": True,
            "data": calls,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tools', methods=['GET'])
def get_tools():
    """Get list of available tools"""
    return jsonify({
        "tools": AVAILABLE_TOOLS,
        "total": len(AVAILABLE_TOOLS)
    })

# ================== DASHBOARD ENDPOINTS ==================
# Database configuration for dashboard
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
    logger.info(f"GET /api/calls - page={request.args.get('page')}, per_page={request.args.get('per_page')}")
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        search = request.args.get('search', '')
        
        logger.info(f"Parsed params: page={page}, per_page={per_page}, search='{search}'")
        
        offset = (page - 1) * per_page
        
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        # Log table structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Available tables: {[t['name'] for t in tables]}")
        
        # Build query with search
        where_clause = ""
        params = []
        if search:
            where_clause = """
                WHERE token_symbol LIKE ? 
                OR group_name LIKE ? 
                OR text LIKE ?
                OR contract_address LIKE ?
            """
            search_param = f'%{search}%'
            params = [search_param, search_param, search_param, search_param]
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM calls {where_clause}"
        logger.info(f"Count query: {count_query}, params: {params}")
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']
        logger.info(f"Total count: {total_count}")
        
        # Get paginated results
        query = f"""
            SELECT * FROM calls 
            {where_clause}
            ORDER BY buy_timestamp DESC 
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])
        logger.info(f"Main query: {query}, params: {params}")
        cursor.execute(query, params)
        calls = cursor.fetchall()
        logger.info(f"Retrieved {len(calls)} calls")
        
        # Process calls for display
        for call in calls:
            # Format timestamps
            if call.get('buy_timestamp'):
                call['buy_timestamp_formatted'] = datetime.fromtimestamp(
                    call['buy_timestamp'] / 1000
                ).strftime('%Y-%m-%d %H:%M:%S')
            
            # Round ROI
            if call.get('roi'):
                call['roi'] = round(call['roi'], 2)
        
        conn.close()
        
        return jsonify({
            'calls': calls,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        })
        
    except Exception as e:
        logger.error(f"Calls error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/call/<call_id>/raw')
def get_call_raw_data(call_id):
    """Get raw data for a specific call"""
    try:
        conn = get_db_connection()
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        
        cursor.execute("SELECT raw_data FROM calls WHERE id = ?", (call_id,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result and result['raw_data']:
            raw_data = json.loads(result['raw_data'])
            return jsonify({
                'raw_data': raw_data,
                'formatted': json.dumps(raw_data, indent=2)
            })
        else:
            return jsonify({'error': 'Raw data not found'}), 404
            
    except Exception as e:
        logger.error(f"Raw data error: {e}")
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
                COUNT(*) as call_count,
                AVG(roi) as avg_roi,
                MAX(roi) as max_roi,
                MIN(buy_timestamp) as first_call,
                MAX(buy_timestamp) as last_call
            FROM calls
            WHERE group_name IS NOT NULL
            GROUP BY group_name
            ORDER BY call_count DESC
            LIMIT 100
        """)
        groups = cursor.fetchall()
        
        conn.close()
        
        return jsonify({'groups': groups})
        
    except Exception as e:
        logger.error(f"Groups error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    """Serve the main dashboard with integrated chat"""
    return send_file('krom-analysis-viz.html')

@app.route('/dashboard')
def dashboard():
    """Serve the dashboard HTML"""
    return send_file('krom-analysis-viz.html')

@app.route('/api/admin/system-prompt', methods=['GET', 'POST'])
def admin_system_prompt():
    """Get or update the system prompt"""
    global system_prompt_template
    
    if request.method == 'GET':
        # Return current system prompt
        try:
            # Get the template without the dynamic tool descriptions
            prompt = system_prompt_template if 'system_prompt_template' in globals() else """You are KROM Crypto Assistant, an AI with sophisticated analytical capabilities.

## Core Capabilities

I have direct access to:
- **Python Code Execution**: I can write and run Python code with pandas, numpy, and full database access
- **Dynamic Visualizations**: I can create charts, graphs, and tables from any data analysis
- **Cryptocurrency APIs**: Real-time prices, news, whale tracking, market sentiment
- **KROM Database**: 98,000+ crypto calls with detailed performance metrics
- **Tool Creation**: I can create new tools on-the-fly for specific tasks
- **Background Monitoring**: I can run continuous analysis and alert on discoveries

## My Approach

I think like a data scientist and crypto analyst. When you ask me to analyze something, I:
1. Understand what insights would be most valuable
2. Choose the best tools and data sources
3. Execute analysis and create visualizations
4. Present findings concisely

I prefer action over explanation - I'll show you results rather than describe what I could do.

## Database Schema
The KROM calls database has ~100,000 calls in the 'calls' table with these key columns:
- symbol (not ticker or token_symbol)
- buy_price, top_price, roi
- buy_timestamp, top_timestamp
- network, contract_address
- group_name, message_id
- hidden, trade_error

## CRITICAL: Efficient Data Extraction
When querying the database or analyzing data:
1. **ALWAYS limit results** - Never return more than 100 rows unless specifically asked
2. **Aggregate by default** - Use COUNT, AVG, SUM, GROUP BY to extract insights
3. **Sample intelligently** - If you need examples, use LIMIT with ORDER BY
4. **Return insights, not dumps** - Transform data into meaningful summaries
5. **Think like a data scientist** - Extract patterns and statistics, not raw records

Example good query: "SELECT group_name, COUNT(*) as calls, AVG(roi) as avg_roi FROM calls GROUP BY group_name ORDER BY avg_roi DESC LIMIT 20"
Example bad query: "SELECT * FROM calls"

## Creating Visualizations
When using execute_analysis to create charts:
1. Query data directly in your Python code using get_db_connection()
2. Set 'result' variable to a structure compatible with Chart.js
3. For scatter plots: result = {'x': [1,2,3], 'y': [4,5,6], 'labels': ['A','B','C']}
4. For bar charts: result = {'labels': ['Group A', 'Group B'], 'values': [10, 20]}
5. Don't use matplotlib/seaborn - return data for frontend charts

Example execute_analysis code:
```python
conn = get_db_connection()
df = pd.read_sql("SELECT group_name, AVG(roi) as avg_roi FROM calls GROUP BY group_name LIMIT 20", conn)
result = {'labels': df['group_name'].tolist(), 'values': df['avg_roi'].tolist()}
# Don't use 'return' - just set the 'result' variable
```

IMPORTANT: In execute_analysis, set the 'result' variable, don't use 'return' statements!

Remember: The goal is to extract insights that fit in visualizations, not to dump entire datasets."""
            
            return jsonify({"success": True, "prompt": prompt})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    
    else:  # POST
        try:
            data = request.json
            new_prompt = data.get('prompt', '')
            if new_prompt:
                system_prompt_template = new_prompt
                return jsonify({"success": True, "message": "System prompt updated"})
            else:
                return jsonify({"success": False, "error": "No prompt provided"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "KROM MCP Server",
        "version": "2.0",
        "tools_available": len(AVAILABLE_TOOLS)
    })

# New endpoints for standalone dashboard
@app.route('/api/stats/overview', methods=['GET'])
def get_stats_overview():
    """Get overview statistics for header"""
    try:
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            # Get total calls and win rate
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN roi > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
                    COUNT(DISTINCT group_name) as active_groups
                FROM calls
                WHERE roi IS NOT NULL
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            return jsonify({
                'total_calls': result[0],
                'win_rate': round(result[1], 1) if result[1] else 0,
                'active_groups': result[2]
            })
    except Exception as e:
        logger.error(f"Error in stats overview: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/key-metrics', methods=['GET'])
def get_key_metrics():
    """Get key performance metrics with filtering"""
    try:
        period = request.args.get('period', '7d')
        network = request.args.get('network', 'all')
        min_roi = float(request.args.get('min_roi', '2'))
        
        # Calculate time filter
        time_filter = ""
        if period == '24h':
            time_filter = "AND buy_timestamp > strftime('%s', 'now', '-1 day')"
        elif period == '7d':
            time_filter = "AND buy_timestamp > strftime('%s', 'now', '-7 days')"
        elif period == '30d':
            time_filter = "AND buy_timestamp > strftime('%s', 'now', '-30 days')"
        
        network_filter = "" if network == 'all' else f"AND network = '{network}'"
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            # Get total profit and moonshots
            cursor.execute(f'''
                SELECT 
                    AVG(roi) as total_profit,
                    COUNT(CASE WHEN roi >= 10 THEN 1 END) as moonshot_count,
                    COUNT(*) as total_calls,
                    AVG(CASE WHEN top_timestamp > buy_timestamp 
                        THEN (top_timestamp - buy_timestamp) / 60.0 
                        ELSE NULL END) as avg_time_to_peak
                FROM calls
                WHERE roi IS NOT NULL {time_filter} {network_filter}
            ''')
            
            metrics = cursor.fetchone()
            
            # Get best performing group
            cursor.execute(f'''
                SELECT group_name, AVG(roi) as avg_roi
                FROM calls
                WHERE roi IS NOT NULL {time_filter} {network_filter}
                GROUP BY group_name
                HAVING COUNT(*) >= 5
                ORDER BY avg_roi DESC
                LIMIT 1
            ''')
            
            best_group = cursor.fetchone()
            
            conn.close()
            
            return jsonify({
                'total_profit': metrics[0] or 0,
                'profit_change': 0,  # Coming soon
                'best_group': {
                    'name': best_group[0] if best_group else 'N/A',
                    'avg_roi': best_group[1] if best_group else 0
                },
                'moonshot_count': metrics[1] or 0,
                'moonshot_rate': (metrics[1] / metrics[2] * 100) if metrics[2] > 0 else 0,
                'avg_time_to_peak': int(metrics[3]) if metrics[3] else 0,
                'speed_trend': 0  # Coming soon
            })
    except Exception as e:
        logger.error(f"Error in key metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/pump-timeline', methods=['GET'])
def get_pump_timeline():
    """Get pump timeline analysis data"""
    try:
        period = request.args.get('period', '7d')
        network = request.args.get('network', 'all')
        filter_type = request.args.get('filter', 'all')
        groups = request.args.get('groups', '')
        
        # Build filters
        roi_filter = ""
        if filter_type == 'winners':
            roi_filter = "AND roi > 2"
        elif filter_type == 'moonshots':
            roi_filter = "AND roi > 10"
        
        network_filter = "" if network == 'all' else f"AND network = '{network}'"
        
        # Group filter
        group_filter = ""
        if groups:
            group_list = groups.split(',')
            group_placeholders = ','.join(['?' for _ in group_list])
            group_filter = f"AND group_name IN ({group_placeholders})"
        
        # Time period filter
        time_filter = ""
        if period == '24h':
            time_filter = "AND buy_timestamp > strftime('%s', 'now', '-1 day')"
        elif period == '7d':
            time_filter = "AND buy_timestamp > strftime('%s', 'now', '-7 days')"
        elif period == '30d':
            time_filter = "AND buy_timestamp > strftime('%s', 'now', '-30 days')"
        elif period == '180d':
            time_filter = "AND buy_timestamp > strftime('%s', 'now', '-180 days')"
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            # Time checkpoints in minutes - adjust based on timeframe
            if period == '24h':
                # For 24h: more granular early points
                time_points = [1, 5, 10, 15, 30, 60, 120, 240]
                time_labels = ['1m', '5m', '10m', '15m', '30m', '1h', '2h', '4h']
            elif period == '7d':
                # For 7d: standard progression
                time_points = [5, 15, 30, 60, 120, 240, 480, 1440]
                time_labels = ['5m', '15m', '30m', '1h', '2h', '4h', '8h', '1d']
            elif period == '30d':
                # For 30d: longer intervals
                time_points = [15, 30, 60, 120, 240, 480, 1440, 2880]
                time_labels = ['15m', '30m', '1h', '2h', '4h', '8h', '1d', '2d']
            elif period == '180d':
                # For 6 months: even longer intervals  
                time_points = [30, 60, 120, 240, 480, 1440, 2880, 4320]
                time_labels = ['30m', '1h', '2h', '4h', '8h', '1d', '2d', '3d']
            else:  # 'all'
                # For all time: longest intervals
                time_points = [60, 120, 240, 480, 1440, 2880, 4320, 10080]
                time_labels = ['1h', '2h', '4h', '8h', '1d', '2d', '3d', '7d']
            
            datasets = []
            
            # Calculate average ROI for calls that peaked at or before each time point
            if filter_type in ['all', 'moonshots']:
                moonshot_data = []
                for minutes in time_points:
                    query = f'''
                        SELECT AVG(roi) as avg_roi, COUNT(*) as count
                        FROM calls
                        WHERE top_timestamp > buy_timestamp 
                        AND (top_timestamp - buy_timestamp) / 60 <= ?
                        AND roi >= 10
                        {network_filter} {time_filter} {group_filter}
                    '''
                    params = [minutes]
                    if groups:
                        params.extend(group_list)
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    # Only add data if we have enough samples
                    if result[1] and result[1] > 0:
                        moonshot_data.append(result[0])
                    else:
                        moonshot_data.append(None)
                
                datasets.append({
                    'label': '10x+ Calls',
                    'data': moonshot_data
                })
            
            if filter_type in ['all', 'winners']:
                # 5-10x calls
                high_data = []
                for minutes in time_points:
                    query = f'''
                        SELECT AVG(roi) as avg_roi, COUNT(*) as count
                        FROM calls
                        WHERE top_timestamp > buy_timestamp 
                        AND (top_timestamp - buy_timestamp) / 60 <= ?
                        AND roi >= 5 AND roi < 10
                        {network_filter} {time_filter} {group_filter}
                    '''
                    params = [minutes]
                    if groups:
                        params.extend(group_list)
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    if result[1] and result[1] > 0:
                        high_data.append(result[0])
                    else:
                        high_data.append(None)
                
                datasets.append({
                    'label': '5-10x Calls',
                    'data': high_data
                })
                
                # 2-5x calls
                medium_data = []
                for minutes in time_points:
                    query = f'''
                        SELECT AVG(roi) as avg_roi, COUNT(*) as count
                        FROM calls
                        WHERE top_timestamp > buy_timestamp 
                        AND (top_timestamp - buy_timestamp) / 60 <= ?
                        AND roi >= 2 AND roi < 5
                        {network_filter} {time_filter} {group_filter}
                    '''
                    params = [minutes]
                    if groups:
                        params.extend(group_list)
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    if result[1] and result[1] > 0:
                        medium_data.append(result[0])
                    else:
                        medium_data.append(None)
                
                datasets.append({
                    'label': '2-5x Calls',
                    'data': medium_data
                })
            
            if filter_type == 'all':
                # <2x calls
                low_data = []
                for minutes in time_points:
                    query = f'''
                        SELECT AVG(roi) as avg_roi, COUNT(*) as count
                        FROM calls
                        WHERE top_timestamp > buy_timestamp 
                        AND (top_timestamp - buy_timestamp) / 60 <= ?
                        AND roi < 2
                        {network_filter} {time_filter} {group_filter}
                    '''
                    params = [minutes]
                    if groups:
                        params.extend(group_list)
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    if result[1] and result[1] > 0:
                        low_data.append(result[0])
                    else:
                        low_data.append(None)
                
                datasets.append({
                    'label': '<2x Calls',
                    'data': low_data
                })
            
            conn.close()
            
            return jsonify({
                'labels': time_labels,
                'datasets': datasets
            })
        
    except Exception as e:
        logger.error(f"Error in pump timeline: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/group-matrix', methods=['GET'])
def get_group_matrix():
    """Get group performance matrix data"""
    try:
        period = request.args.get('period', '7d')
        network = request.args.get('network', 'all')
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            network_filter = "" if network == 'all' else f"AND network = '{network}'"
            
            cursor.execute(f'''
                SELECT 
                    group_name,
                    COUNT(*) as call_count,
                    AVG(roi) as avg_roi,
                    SUM(CASE WHEN roi > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
                FROM calls
                WHERE roi IS NOT NULL {network_filter}
                GROUP BY group_name
                HAVING COUNT(*) >= 5
                ORDER BY avg_roi DESC
                LIMIT 50
            ''')
            
            groups = []
            for row in cursor.fetchall():
                groups.append({
                    'name': row[0],
                    'call_count': row[1],
                    'avg_roi': round(row[2], 2),
                    'win_rate': round(row[3], 1)
                })
            
            conn.close()
            
            return jsonify({'groups': groups})
    except Exception as e:
        logger.error(f"Error in group matrix: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/network-performance', methods=['GET'])
def get_network_performance():
    """Get network performance comparison"""
    try:
        period = request.args.get('period', '7d')
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    network,
                    COUNT(*) as call_count,
                    AVG(roi) as avg_roi,
                    SUM(CASE WHEN roi > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
                FROM calls
                WHERE roi IS NOT NULL AND network IS NOT NULL
                GROUP BY network
                ORDER BY call_count DESC
                LIMIT 10
            ''')
            
            networks = []
            for row in cursor.fetchall():
                networks.append({
                    'name': row[0],
                    'call_count': row[1],
                    'avg_roi': round(row[2], 2),
                    'win_rate': round(row[3], 1)
                })
            
            conn.close()
            
            return jsonify({'networks': networks})
    except Exception as e:
        logger.error(f"Error in network performance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/hourly-heatmap', methods=['GET'])
def get_hourly_heatmap():
    """Get hourly performance heatmap data"""
    try:
        period = request.args.get('period', '7d')
        network = request.args.get('network', 'all')
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            network_filter = "" if network == 'all' else f"AND network = '{network}'"
            
            # Get hourly averages by day of week
            cursor.execute(f'''
                SELECT 
                    CAST(strftime('%w', datetime(buy_timestamp, 'unixepoch')) AS INTEGER) as day_of_week,
                    CAST(strftime('%H', datetime(buy_timestamp, 'unixepoch')) AS INTEGER) as hour,
                    AVG(roi) as avg_roi
                FROM calls
                WHERE roi IS NOT NULL {network_filter}
                GROUP BY day_of_week, hour
            ''')
            
            # Initialize heatmap grid
            heatmap = [[0 for _ in range(24)] for _ in range(7)]
            
            for row in cursor.fetchall():
                if row[0] is not None and row[1] is not None:
                    heatmap[row[0]][row[1]] = round(row[2], 2)
            
            conn.close()
            
            return jsonify({'heatmap': heatmap})
    except Exception as e:
        logger.error(f"Error in hourly heatmap: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/top-groups', methods=['GET'])
def get_top_groups_analysis():
    """Get top performing groups with detailed metrics"""
    try:
        period = request.args.get('period', '7d')
        network = request.args.get('network', 'all')
        limit = int(request.args.get('limit', '10'))
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            network_filter = "" if network == 'all' else f"AND network = '{network}'"
            
            # Calculate composite score (win_rate * avg_roi * sqrt(call_count))
            cursor.execute(f'''
                SELECT 
                    group_name,
                    COUNT(*) as call_count,
                    AVG(roi) as avg_roi,
                    SUM(CASE WHEN roi > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
                    (SUM(CASE WHEN roi > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 
                    AVG(roi) * 
                    SQRT(COUNT(*)) as score
                FROM calls
                WHERE roi IS NOT NULL {network_filter}
                GROUP BY group_name
                HAVING COUNT(*) >= 5
                ORDER BY score DESC
                LIMIT ?
            ''', (limit,))
            
            groups = []
            for row in cursor.fetchall():
                groups.append({
                    'name': row[0],
                    'call_count': row[1],
                    'avg_roi': round(row[2], 2),
                    'win_rate': round(row[3], 1),
                    'score': round(row[4], 0)
                })
            
            conn.close()
            
            return jsonify({'groups': groups})
    except Exception as e:
        logger.error(f"Error in top groups: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/recent-moonshots', methods=['GET'])
def get_recent_moonshots():
    """Get recent high-performing calls"""
    try:
        network = request.args.get('network', 'all')
        limit = int(request.args.get('limit', '10'))
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            network_filter = "" if network == 'all' else f"AND network = '{network}'"
            
            cursor.execute(f'''
                SELECT 
                    symbol as ticker,
                    group_name,
                    network,
                    roi,
                    buy_timestamp,
                    CASE WHEN top_timestamp > buy_timestamp 
                        THEN (top_timestamp - buy_timestamp) / 60 
                        ELSE 0 END as time_to_peak
                FROM calls
                WHERE roi >= 10 {network_filter}
                ORDER BY buy_timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            moonshots = []
            for row in cursor.fetchall():
                moonshots.append({
                    'ticker': row[0],
                    'group_name': row[1],
                    'network': row[2],
                    'roi': row[3],
                    'timestamp': row[4] * 1000,  # Convert to milliseconds for JS
                    'time_to_peak': int(row[5])
                })
            
            conn.close()
            
            return jsonify({'moonshots': moonshots})
    except Exception as e:
        logger.error(f"Error in recent moonshots: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/moonshot-timeline', methods=['GET'])
def get_moonshot_timeline():
    """Get all tokens that reached 10X+ since November"""
    try:
        # November 1st, 2024 timestamp
        november_timestamp = 1730419200  # November 1, 2024 00:00:00 UTC
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    symbol,
                    group_name,
                    contract_address,
                    roi,
                    buy_timestamp,
                    top_timestamp,
                    CASE WHEN top_timestamp > buy_timestamp 
                        THEN (top_timestamp - buy_timestamp) / 60.0 
                        ELSE 0 END as time_to_reach_minutes
                FROM calls
                WHERE roi >= 10 
                    AND top_timestamp >= ?
                    AND top_timestamp > 0
                ORDER BY top_timestamp
            ''', (november_timestamp,))
            
            moonshots = []
            for row in cursor.fetchall():
                moonshots.append({
                    'symbol': row[0],
                    'group_name': row[1],
                    'contract_address': row[2],
                    'roi': row[3],
                    'buy_timestamp': row[4],
                    'top_timestamp': row[5],
                    'time_to_reach_minutes': round(row[6], 1)
                })
            
            conn.close()
            
            return jsonify({'moonshots': moonshots})
    except Exception as e:
        logger.error(f"Error in moonshot timeline: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/group-list', methods=['GET'])
def get_group_list():
    """Get list of all groups with call counts"""
    try:
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT group_name, COUNT(*) as call_count
                FROM calls
                WHERE group_name IS NOT NULL
                GROUP BY group_name
                ORDER BY call_count DESC
            ''')
            
            groups = []
            for row in cursor.fetchall():
                groups.append({
                    'name': row[0],
                    'call_count': row[1]
                })
            
            conn.close()
            
            return jsonify({'groups': groups})
    except Exception as e:
        logger.error(f"Error getting group list: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/live-feed', methods=['GET'])
def get_live_feed():
    """Get live feed of tokens based on filter criteria"""
    try:
        filter_type = request.args.get('filter', 'hot')
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            # Build query based on filter
            if filter_type == 'hot':
                # Tokens that did >5x in last 24h
                query = '''
                    SELECT krom_id, symbol, roi, buy_timestamp, group_name, network
                    FROM calls
                    WHERE roi > 5
                    AND buy_timestamp > strftime('%s', 'now', '-1 day')
                    ORDER BY buy_timestamp DESC
                    LIMIT 20
                '''
            elif filter_type == 'rising':
                # Tokens that did >2x in last hour
                query = '''
                    SELECT krom_id, symbol, roi, buy_timestamp, group_name, network
                    FROM calls
                    WHERE roi > 2
                    AND buy_timestamp > strftime('%s', 'now', '-1 hour')
                    ORDER BY buy_timestamp DESC
                    LIMIT 20
                '''
            elif filter_type == 'new':
                # Newest calls from last 30 minutes
                query = '''
                    SELECT krom_id, symbol, roi, buy_timestamp, group_name, network
                    FROM calls
                    WHERE buy_timestamp > strftime('%s', 'now', '-30 minutes')
                    ORDER BY buy_timestamp DESC
                    LIMIT 20
                '''
            else:  # moonshots
                # All-time 10x+ performers
                query = '''
                    SELECT krom_id, symbol, roi, buy_timestamp, group_name, network
                    FROM calls
                    WHERE roi >= 10
                    ORDER BY buy_timestamp DESC
                    LIMIT 20
                '''
            
            cursor.execute(query)
            
            calls = []
            for row in cursor.fetchall():
                calls.append({
                    'krom_id': row[0],
                    'symbol': row[1],
                    'roi': row[2],
                    'buy_timestamp': row[3],
                    'group_name': row[4],
                    'network': row[5] or 'SOL'
                })
            
            conn.close()
            
            return jsonify({'calls': calls})
    except Exception as e:
        logger.error(f"Error getting live feed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis/token-search', methods=['GET'])
def token_search():
    """Search tokens by symbol or contract address"""
    try:
        query = request.args.get('q', '').upper()
        
        if not query or len(query) < 2:
            return jsonify({'tokens': []})
        
        with db_lock:
            conn = sqlite3.connect('krom_calls.db')
            cursor = conn.cursor()
            
            # Search by symbol or contract (partial match)
            cursor.execute('''
                SELECT 
                    symbol,
                    COUNT(*) as call_count,
                    AVG(roi) as avg_roi,
                    MAX(roi) as best_roi,
                    SUM(CASE WHEN roi > 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
                    MIN(buy_timestamp) as first_call,
                    MAX(buy_timestamp) as last_call
                FROM calls
                WHERE symbol LIKE ? OR contract_address LIKE ?
                GROUP BY symbol
                ORDER BY call_count DESC
                LIMIT 10
            ''', (f'%{query}%', f'%{query}%'))
            
            tokens = []
            for row in cursor.fetchall():
                tokens.append({
                    'symbol': row[0],
                    'call_count': row[1],
                    'avg_roi': row[2],
                    'best_roi': row[3],
                    'win_rate': row[4],
                    'first_call': row[5],
                    'last_call': row[6]
                })
            
            conn.close()
            
            return jsonify({'tokens': tokens})
    except Exception as e:
        logger.error(f"Error searching tokens: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dexscreener/signals', methods=['GET'])
def get_dexscreener_signals():
    """Get comprehensive DexScreener signals for tokens worth researching"""
    try:
        import time
        from datetime import datetime, timedelta
        
        signals = {
            'trending': [],
            'new_launches': [],
            'volume_spikes': [],
            'top_gainers': [],
            'boosted_tokens': [],
            'high_activity': []
        }
        
        all_tokens = {}  # Use dict to track unique tokens
        
        # 1. Get boosted tokens (both latest and top)
        logger.info("Fetching boosted tokens...")
        try:
            # Latest boosted
            response = requests.get("https://api.dexscreener.com/token-boosts/latest/v1")
            if response.status_code == 200:
                boosts = response.json()[:30]  # Get more boosted tokens
                for boost in boosts:
                    token_address = boost.get('tokenAddress')
                    if token_address and token_address not in all_tokens:
                        all_tokens[token_address] = {'boost': boost, 'source': 'boosted_latest'}
            
            # Top boosted
            response = requests.get("https://api.dexscreener.com/token-boosts/top/v1")
            if response.status_code == 200:
                boosts = response.json()[:30]
                for boost in boosts:
                    token_address = boost.get('tokenAddress')
                    if token_address and token_address not in all_tokens:
                        all_tokens[token_address] = {'boost': boost, 'source': 'boosted_top'}
                        
        except Exception as e:
            logger.error(f"Error fetching boosted tokens: {e}")
        
        # 2. Get token profiles (often has newer tokens)
        logger.info("Fetching token profiles...")
        try:
            response = requests.get("https://api.dexscreener.com/token-profiles/latest/v1")
            if response.status_code == 200:
                profiles = response.json()[:50]
                for profile in profiles:
                    token_address = profile.get('tokenAddress')
                    if token_address and token_address not in all_tokens:
                        all_tokens[token_address] = {'profile': profile, 'source': 'profiles'}
        except Exception as e:
            logger.error(f"Error fetching profiles: {e}")
        
        # 3. Search for various token categories - REDUCED for faster performance
        logger.info("Searching for tokens by category...")
        search_terms = [
            # Focus on most popular categories for speed
            'MEME', 'AI', 'PEPE', 'NEW', 'PUMP',
            'MOON', 'ROCKET', 'BASE', 'SOL', 'ETH'
        ]
        
        for term in search_terms:
            try:
                response = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={term}")
                if response.status_code == 200:
                    data = response.json()
                    pairs = data.get('pairs', [])[:30]  # Get more from each search
                    
                    for pair in pairs:
                        token_address = pair.get('baseToken', {}).get('address')
                        if token_address and token_address not in all_tokens:
                            all_tokens[token_address] = {'pair': pair, 'source': f'search_{term}'}
                    
                    logger.info(f"Found {len(pairs)} pairs for {term}")
                time.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.error(f"Error searching {term}: {e}")
        
        # 4. Process tokens we already have data for (much faster!)
        logger.info(f"Processing {len(all_tokens)} unique tokens...")
        tokens_with_data = []
        
        # First, process all tokens that already have pair data (no extra API calls needed)
        for token_address, token_info in all_tokens.items():
            try:
                pair = None
                
                # If we already have pair data from search, use it
                if 'pair' in token_info:
                    pair = token_info['pair']
                elif 'boost' in token_info:
                    # For boosted tokens, we need to fetch the pair data
                    # But only fetch for the first 20 boosted tokens to save time
                    if len([t for t in tokens_with_data if t.get('boost_amount', 0) > 0]) < 20:
                        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token_address}")
                        if response.status_code == 200:
                            pairs = response.json().get('pairs', [])
                            if pairs:
                                pair = pairs[0]
                                time.sleep(0.05)  # Small rate limit
                
                if not pair:
                    continue
                
                # Extract key metrics
                created_at = pair.get('pairCreatedAt')
                if created_at:
                    age_hours = (time.time() * 1000 - created_at) / (1000 * 3600)
                else:
                    age_hours = 9999  # Unknown age
                
                liquidity_usd = pair.get('liquidity', {}).get('usd', 0)
                volume_24h = pair.get('volume', {}).get('h24', 0)
                volume_6h = pair.get('volume', {}).get('h6', 0)
                volume_1h = pair.get('volume', {}).get('h1', 0)
                price_change_24h = pair.get('priceChange', {}).get('h24', 0)
                price_change_6h = pair.get('priceChange', {}).get('h6', 0)
                price_change_1h = pair.get('priceChange', {}).get('h1', 0)
                txns_24h = pair.get('txns', {}).get('h24', {})
                total_txns = txns_24h.get('buys', 0) + txns_24h.get('sells', 0)
                
                # Store token data
                token_data = {
                    'symbol': pair.get('baseToken', {}).get('symbol', 'N/A'),
                    'name': pair.get('baseToken', {}).get('name', ''),
                    'chain': pair.get('chainId', 'N/A'),
                    'address': token_address,
                    'age_hours': round(age_hours, 1),
                    'liquidity_usd': round(liquidity_usd),
                    'volume_24h': round(volume_24h),
                    'volume_6h': round(volume_6h),
                    'volume_1h': round(volume_1h),
                    'price_change_24h': price_change_24h,
                    'price_change_6h': price_change_6h,
                    'price_change_1h': price_change_1h,
                    'total_txns_24h': total_txns,
                    'url': pair.get('url', ''),
                    'source': token_info.get('source', 'unknown'),
                    'boost_amount': token_info.get('boost', {}).get('totalAmount', 0) if 'boost' in token_info else 0
                }
                
                tokens_with_data.append(token_data)
                
            except Exception as e:
                logger.error(f"Error processing token {token_address}: {e}")
        
        # 5. Categorize tokens
        logger.info(f"Categorizing {len(tokens_with_data)} tokens...")
        
        for token in tokens_with_data:
            # Skip tokens with very low liquidity (likely scams)
            if token['liquidity_usd'] < 1000:
                continue
                
            # New launches (< 24 hours, with decent liquidity)
            if token['age_hours'] < 24 and token['liquidity_usd'] > 2000:
                signals['new_launches'].append(token)
            
            # Trending (high volume relative to liquidity)
            if token['volume_24h'] > 0 and token['liquidity_usd'] > 0:
                volume_to_liq_ratio = token['volume_24h'] / token['liquidity_usd']
                if volume_to_liq_ratio > 0.5 and token['liquidity_usd'] > 5000:  # 50% daily volume
                    signals['trending'].append(token)
            
            # Volume spikes
            if token['volume_6h'] > 0 and token['volume_24h'] > 0:
                projected_24h = token['volume_6h'] * 4
                spike_ratio = projected_24h / token['volume_24h']
                if spike_ratio > 1.5 and token['volume_6h'] > 5000:  # 50% spike
                    token['volume_spike_ratio'] = round(spike_ratio, 1)
                    signals['volume_spikes'].append(token)
            
            # Top gainers
            if token['price_change_6h'] > 50 and token['liquidity_usd'] > 3000:
                signals['top_gainers'].append(token)
            
            # Boosted tokens (that also have good metrics)
            if token['boost_amount'] > 0 and token['liquidity_usd'] > 10000:
                signals['boosted_tokens'].append(token)
            
            # High activity (lots of transactions)
            if token['total_txns_24h'] > 1000 and token['liquidity_usd'] > 5000:
                signals['high_activity'].append(token)
        
        # 6. Sort and limit results
        signals['new_launches'] = sorted(signals['new_launches'], key=lambda x: x['volume_24h'], reverse=True)[:20]
        signals['trending'] = sorted(signals['trending'], key=lambda x: x['volume_24h'], reverse=True)[:20]
        signals['volume_spikes'] = sorted(signals['volume_spikes'], key=lambda x: x.get('volume_spike_ratio', 0), reverse=True)[:20]
        signals['top_gainers'] = sorted(signals['top_gainers'], key=lambda x: x['price_change_6h'], reverse=True)[:20]
        signals['boosted_tokens'] = sorted(signals['boosted_tokens'], key=lambda x: x['boost_amount'], reverse=True)[:15]
        signals['high_activity'] = sorted(signals['high_activity'], key=lambda x: x['total_txns_24h'], reverse=True)[:15]
        
        # Summary
        total_signals = sum(len(category) for category in signals.values())
        logger.info(f"Total signals generated: {total_signals}")
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'signals': signals,
            'summary': {
                'new_launches': len(signals['new_launches']),
                'trending': len(signals['trending']),
                'volume_spikes': len(signals['volume_spikes']),
                'top_gainers': len(signals['top_gainers']),
                'boosted_tokens': len(signals['boosted_tokens']),
                'high_activity': len(signals['high_activity']),
                'total': total_signals
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting DexScreener signals: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/standalone')
def standalone_dashboard():
    """Serve the standalone dashboard"""
    return send_file('krom-standalone-dashboard.html')

@app.route('/main')
def main_dashboard():
    """Serve the main token-gated dashboard"""
    return send_file('krom-dashboard-main.html')

@app.route('/krom')
def krom_analytics():
    """Serve the KROM styled analytics dashboard"""
    return send_file('krom-analytics.html')

@app.route('/test-wallet')
def test_wallet():
    """Serve the wallet test page"""
    return send_file('test-wallet.html')

@app.route('/wallet-test')
def wallet_test_new():
    """Serve the new wallet test page"""
    return send_file('wallet-test.html')

@app.route('/dexscreener')
def dexscreener_signals():
    """Serve the DexScreener signals page"""
    return send_file('dexscreener-signals.html')

if __name__ == '__main__':
    print("\n🚀 KROM All-in-One Server (MCP + Dashboard)")
    print("=" * 50)
    print("🌐 Server running at: http://localhost:5001")
    print("\n📍 Access Points:")
    print("  💬 AI Chat: http://localhost:5001/")
    print("  📊 Dashboard: http://localhost:5001/dashboard")
    print("  🚀 Standalone Analytics: http://localhost:5001/standalone")
    print("  🔗 API Base: http://localhost:5001/api/")
    print("\n✨ Features:")
    print("  - True Model Context Protocol (MCP) implementation")
    print("  - AI has full control over tool selection and usage")
    print("  - Database visualization dashboard")
    print("  - Support for tool chaining and complex workflows")
    print("  - Enhanced Etherscan integration with token support")
    print(f"\n🔧 Available Tools: {len(AVAILABLE_TOOLS)}")
    for tool in AVAILABLE_TOOLS:
        print(f"  - {tool}")
    print("\n📝 API Endpoints:")
    print("  - POST /api/chat - MCP-powered chat")
    print("  - GET /api/tools - List available tools")
    print("  - GET /api/health - Health check")
    
    # Check for required API keys
    print("\n🔑 API Key Status:")
    keys_to_check = [
        ("ANTHROPIC_API_KEY", "Claude AI"),
        ("KROM_API_TOKEN", "KROM API"),
        ("ETHERSCAN_API_KEY", "Etherscan"),
        ("COINMARKETCAP_API_KEY", "CoinMarketCap"),
        ("NEWS_API_KEY", "NewsAPI")
    ]
    
    for key_name, service_name in keys_to_check:
        if os.getenv(key_name):
            print(f"  ✅ {service_name}")
        else:
            print(f"  ❌ {service_name} (optional)")
    
    print("\nPress Ctrl+C to stop\n")
    
    app.run(debug=False, host='127.0.0.1', port=5001)
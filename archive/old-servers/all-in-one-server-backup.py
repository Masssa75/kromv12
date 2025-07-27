#!/usr/bin/env python3
"""
True MCP Implementation - AI-Powered Chat API Server for KROM Crypto Analysis
This version gives Claude full control over tool selection and execution
"""

from flask import Flask, jsonify, request
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

# Load environment variables
load_dotenv()

# Database lock for thread safety
db_lock = threading.Lock()

app = Flask(__name__)
CORS(app)

# In-memory conversation history (in production, use a database)
conversation_history = {}

# Session-based dynamic tools (created on-the-fly)
dynamic_tools = {}

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
                    cursor.execute("SELECT id FROM krom_calls WHERE id = ?", (call_id,))
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
                        UPDATE krom_calls SET 
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
                        INSERT INTO krom_calls (
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
                        
                        # Link call to group
                        cursor.execute("SELECT id FROM groups WHERE name = ?", (group_data['name'],))
                        group_id = cursor.fetchone()[0]
                        cursor.execute('''
                            INSERT OR IGNORE INTO call_groups (call_id, group_id) 
                            VALUES (?, ?)
                        ''', (call['id'], group_id))
            
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
                    FROM krom_calls
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
                        g.name,
                        COUNT(c.id) as calls_count,
                        ROUND(AVG(c.roi), 2) as avg_roi,
                        COUNT(CASE WHEN c.status = 'profit' THEN 1 END) as wins,
                        ROUND(g.win_rate_30d, 2) as reported_win_rate,
                        ROUND(g.profit_30d, 2) as reported_profit
                    FROM groups g
                    JOIN call_groups cg ON g.id = cg.group_id
                    JOIN krom_calls c ON cg.call_id = c.id
                    WHERE 1=1 {timeframe_filter} {group_filter}
                    GROUP BY g.name
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
                    FROM krom_calls
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
                    FROM krom_calls
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
                        c.ticker,
                        c.name,
                        c.roi,
                        c.profit_percent,
                        c.buy_price,
                        c.top_price,
                        c.call_timestamp,
                        g.name as group_name
                    FROM krom_calls c
                    JOIN call_groups cg ON c.id = cg.call_id
                    JOIN groups g ON cg.group_id = g.id
                    WHERE c.roi > 2 {timeframe_filter} {group_filter}
                    ORDER BY c.roi DESC
                    LIMIT 50
                ''')
                top_performers = [dict(row) for row in cursor.fetchall()]
                
                return {"success": True, "data": top_performers}
            
            else:
                return {"success": False, "error": f"Unknown analysis type: {analysis_type}"}
            
            conn.close()
            
    except Exception as e:
        return {"success": False, "error": f"Analysis failed: {str(e)}"}

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
        "analyze_krom_stats": analyze_krom_stats
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

def parse_tool_calls(response_text: str) -> List[Dict[str, Any]]:
    """Parse tool calls from Claude's response"""
    tool_calls = []
    
    # Look for tool call patterns in the response
    # Pattern 1: JSON blocks with tool calls
    json_pattern = r'```json\s*(\{[^`]+\})\s*```'
    json_matches = re.findall(json_pattern, response_text, re.DOTALL)
    
    for match in json_matches:
        try:
            call_data = json.loads(match)
            if 'tool' in call_data:
                tool_calls.append({
                    'tool': call_data['tool'],
                    'params': call_data.get('params', {})
                })
        except json.JSONDecodeError:
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

def analyze_with_mcp(user_message: str, session_id: str = "default") -> Dict[str, Any]:
    """True MCP implementation - AI has full control over tool usage"""
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
        
        # System prompt explaining MCP capabilities
        system_prompt = f"""You are KROM Crypto Assistant, an AI with access to powerful crypto analysis tools through the Model Context Protocol (MCP).

## CRITICAL: Response Style & Understanding Questions
**ALWAYS provide concise, short responses unless the user explicitly asks for details.**

**IMPORTANT: Understand what the user is asking before using tools:**
- "How many X can you retrieve?" → Answer about your capabilities, not fetch data
- "What kind of data can you get from Y?" → List the types of data available, don't fetch examples
- "What's the latest X?" → Fetch and show only that specific item
- For capability questions, explain what you CAN do, don't demonstrate it

**Response Guidelines:**
- For specific data requests (like "what's the price of X"), give just the requested data
- For lists, show only what was asked for
- Avoid lengthy explanations unless requested
- If asked for "latest ETH call", show only the most recent ETH-related call
- If asked "how many calls", respond with just the number

## Available Tools

{create_tool_descriptions()}

## How to Use Tools

**BEFORE USING ANY TOOL, ASK YOURSELF:**
1. Is the user asking about my capabilities or asking me to DO something?
2. If they're asking what I CAN do, don't call tools - just explain
3. Only call tools when the user wants actual data or actions

When you need to use a tool, include a JSON code block in your response like this:
```json
{{"tool": "tool_name", "params": {{"param1": "value1", "param2": value2}}}}
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
        
        # Keep conversation history manageable
        if len(conversation_history[session_id]) > 20:
            conversation_history[session_id] = conversation_history[session_id][-20:]
        
        # First pass - let Claude decide what tools to use
        initial_messages = conversation_history[session_id].copy()
        
        initial_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.7,
            system=system_prompt,
            messages=initial_messages
        )
        
        response_text = initial_response.content[0].text
        
        # Parse tool calls from response
        tool_calls = parse_tool_calls(response_text)
        
        # Execute tool calls
        tool_results = {}
        for call in tool_calls:
            tool_name = call['tool']
            params = call['params']
            
            print(f"Executing tool: {tool_name} with params: {params}")
            result = execute_tool(tool_name, params)
            tool_results[f"{tool_name}_{len(tool_results)}"] = result
        
        # If tools were called, make a second pass with the results
        if tool_results:
            # Create enhanced message with tool results
            enhanced_message = f"""Tool results:

{json.dumps(tool_results, indent=2)}

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
                model="claude-3-5-sonnet-20241022",
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
            
            return {
                "response": final_text,
                "tools_used": [call['tool'] for call in tool_calls]
            }
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
        print(f"MCP Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "response": f"I encountered an error: {str(e)}. Please try again.",
            "error": True
        }

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
                FROM krom_calls
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
                FROM krom_calls
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
                FROM krom_calls
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
        allowed_sorts = ['call_timestamp', 'roi', 'profit_percent', 'ticker', 'network']
        if sort_by not in allowed_sorts:
            sort_by = 'call_timestamp'
        if sort_order not in ['ASC', 'DESC']:
            sort_order = 'DESC'
            
        conn = sqlite3.connect('krom_calls.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM krom_calls")
        total_count = cursor.fetchone()['total']
        
        # Get paginated data
        query = f"""
            SELECT 
                k.*, 
                g.name as group_name
            FROM krom_calls k
            LEFT JOIN call_groups cg ON k.id = cg.call_id
            LEFT JOIN groups g ON cg.group_id = g.id
            ORDER BY {sort_by} {sort_order}
            LIMIT ? OFFSET ?
        """
        cursor.execute(query, (per_page, offset))
        
        calls = []
        for row in cursor.fetchall():
            call = dict(row)
            # Format timestamps
            if call.get('call_timestamp'):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(call['call_timestamp'].replace('Z', '+00:00'))
                    call['formatted_date'] = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    call['formatted_date'] = call['call_timestamp']
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

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "KROM MCP Server",
        "version": "2.0",
        "tools_available": len(AVAILABLE_TOOLS)
    })

if __name__ == '__main__':
    print("\n🚀 KROM True MCP Implementation Server")
    print("=" * 50)
    print("🌐 Server running at: http://localhost:5001")
    print("\n✨ Features:")
    print("  - True Model Context Protocol (MCP) implementation")
    print("  - AI has full control over tool selection and usage")
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
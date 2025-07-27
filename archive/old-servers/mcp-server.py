#!/usr/bin/env python3
"""
MCP Server for Cryptocurrency Analysis
Integrates with Claude to provide intelligent crypto market analysis
"""

import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv
import logging
from collections import deque
import time

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Portfolio tracking (in-memory for now)
portfolio: Dict[str, Dict[str, Any]] = {}

# Activity tracking for the web interface
activity_log = deque(maxlen=100)  # Keep last 100 activities
api_stats = {
    "total_calls": 0,
    "calls_by_tool": {},
    "start_time": datetime.now()
}

class CryptoMCPServer:
    def __init__(self):
        self.server = Server("crypto-analyzer")
        self.setup_request_handlers()
        self.session = None
        
    async def __aenter__(self):
        # Create session with SSL verification disabled for macOS certificate issues
        connector = aiohttp.TCPConnector(ssl=False)
        self.session = aiohttp.ClientSession(connector=connector)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    def log_activity(self, tool_name: str, args: dict, result: Any):
        """Log activity for web interface"""
        activity = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "args": args,
            "success": "error" not in str(result).lower(),
            "summary": self.summarize_result(tool_name, result)
        }
        activity_log.append(activity)
        
        # Update stats
        api_stats["total_calls"] += 1
        api_stats["calls_by_tool"][tool_name] = api_stats["calls_by_tool"].get(tool_name, 0) + 1
        
    def summarize_result(self, tool_name: str, result: Any) -> str:
        """Create a brief summary of the result"""
        if isinstance(result, dict):
            if "error" in result:
                return f"Error: {result['error']}"
            elif tool_name == "get_crypto_price" and "symbol" in result:
                return f"{result['symbol']}: ${result.get('price', 'N/A')} ({result.get('24h_change', 0):.2f}%)"
            elif tool_name == "get_market_sentiment" and "classification" in result:
                return f"Market: {result['classification']} ({result.get('value', 'N/A')})"
            elif tool_name == "get_crypto_news" and "articles" in result:
                return f"Found {len(result['articles'])} news articles"
        return "Completed successfully"
        
    def setup_request_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="get_crypto_price",
                    description="Get current price, market cap, and 24h change for a cryptocurrency",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Cryptocurrency symbol (e.g., BTC, ETH)"
                            }
                        },
                        "required": ["symbol"]
                    }
                ),
                Tool(
                    name="get_market_sentiment",
                    description="Get current crypto market sentiment from Fear & Greed Index",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_crypto_news",
                    description="Get recent cryptocurrency news articles",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query for news (e.g., 'Bitcoin', 'Ethereum crash')"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_whale_activity",
                    description="Check recent large transactions for Ethereum",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "min_value_usd": {
                                "type": "number",
                                "description": "Minimum transaction value in USD",
                                "default": 1000000
                            }
                        }
                    }
                ),
                Tool(
                    name="add_to_portfolio",
                    description="Add a cryptocurrency to your portfolio for tracking",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Cryptocurrency symbol"
                            },
                            "quantity": {
                                "type": "number",
                                "description": "Amount purchased"
                            },
                            "entry_price": {
                                "type": "number",
                                "description": "Price per unit at purchase"
                            }
                        },
                        "required": ["symbol", "quantity", "entry_price"]
                    }
                ),
                Tool(
                    name="check_portfolio",
                    description="Check current portfolio value and performance",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="compare_cryptos",
                    description="Compare multiple cryptocurrencies side by side",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbols": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of cryptocurrency symbols to compare"
                            }
                        },
                        "required": ["symbols"]
                    }
                ),
                Tool(
                    name="analyze_krom_call",
                    description="Analyze a specific KROM call with additional market context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "The ticker/symbol from KROM call"
                            },
                            "contract_address": {
                                "type": "string",
                                "description": "Contract address if available"
                            }
                        },
                        "required": ["ticker"]
                    }
                ),
                Tool(
                    name="get_trending_cryptos",
                    description="Get currently trending cryptocurrencies",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="calculate_position_size",
                    description="Calculate optimal position size based on risk management",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "account_size": {
                                "type": "number",
                                "description": "Total account size in USD"
                            },
                            "risk_percentage": {
                                "type": "number",
                                "description": "Risk percentage per trade (e.g., 2 for 2%)"
                            },
                            "entry_price": {
                                "type": "number",
                                "description": "Entry price for the position"
                            },
                            "stop_loss": {
                                "type": "number",
                                "description": "Stop loss price"
                            }
                        },
                        "required": ["account_size", "risk_percentage", "entry_price", "stop_loss"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> List[TextContent]:
            start_time = time.time()
            
            try:
                if name == "get_crypto_price":
                    result = await self.get_crypto_price(arguments["symbol"])
                elif name == "get_market_sentiment":
                    result = await self.get_market_sentiment()
                elif name == "get_crypto_news":
                    result = await self.get_crypto_news(arguments["query"])
                elif name == "get_whale_activity":
                    min_value = arguments.get("min_value_usd", 1000000)
                    result = await self.get_whale_activity(min_value)
                elif name == "add_to_portfolio":
                    result = await self.add_to_portfolio(
                        arguments["symbol"],
                        arguments["quantity"],
                        arguments["entry_price"]
                    )
                elif name == "check_portfolio":
                    result = await self.check_portfolio()
                elif name == "compare_cryptos":
                    result = await self.compare_cryptos(arguments["symbols"])
                elif name == "analyze_krom_call":
                    result = await self.analyze_krom_call(
                        arguments["ticker"],
                        arguments.get("contract_address")
                    )
                elif name == "get_trending_cryptos":
                    result = await self.get_trending_cryptos()
                elif name == "calculate_position_size":
                    result = await self.calculate_position_size(
                        arguments["account_size"],
                        arguments["risk_percentage"],
                        arguments["entry_price"],
                        arguments["stop_loss"]
                    )
                else:
                    result = {"error": f"Unknown tool: {name}"}
                
                # Log the activity
                self.log_activity(name, arguments, result)
                
                # Add execution time
                execution_time = time.time() - start_time
                if isinstance(result, dict):
                    result["_execution_time_ms"] = round(execution_time * 1000, 2)
                
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                error_result = {"error": str(e), "tool": name, "arguments": arguments}
                self.log_activity(name, arguments, error_result)
                return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    async def get_crypto_price(self, symbol: str) -> Dict[str, Any]:
        """Fetch current crypto price - try CoinMarketCap first, fallback to CoinGecko"""
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
                
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
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
                                "price_movement": "🟢" if quote['percent_change_24h'] > 0 else "🔴",
                                "source": "CoinMarketCap"
                            }
            except Exception as e:
                logger.warning(f"CoinMarketCap API error for {symbol}: {e}")
        
        # Fallback to CoinGecko
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": self.symbol_to_id(symbol),
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true"
            }
            
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                crypto_id = self.symbol_to_id(symbol)
                
                if crypto_id in data:
                    return {
                        "symbol": symbol.upper(),
                        "price": data[crypto_id]["usd"],
                        "market_cap": data[crypto_id]["usd_market_cap"],
                        "24h_volume": data[crypto_id]["usd_24h_vol"],
                        "24h_change": round(data[crypto_id]["usd_24h_change"], 2),
                        "last_updated": datetime.fromtimestamp(
                            data[crypto_id]["last_updated_at"]
                        ).isoformat(),
                        "price_movement": "🟢" if data[crypto_id]["usd_24h_change"] > 0 else "🔴",
                        "source": "CoinGecko"
                    }
                else:
                    return {"error": f"Symbol {symbol} not found"}
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            return {"error": str(e)}
    
    async def get_market_sentiment(self) -> Dict[str, Any]:
        """Get Fear & Greed Index"""
        try:
            url = "https://api.alternative.me/fng/"
            async with self.session.get(url) as response:
                data = await response.json()
                current = data["data"][0]
                value = int(current["value"])
                
                # Historical comparison
                history = data["data"][:7]  # Last 7 days
                avg_7d = sum(int(d["value"]) for d in history) / len(history)
                
                return {
                    "value": value,
                    "classification": current["value_classification"],
                    "timestamp": current["timestamp"],
                    "analysis": self.analyze_sentiment(value),
                    "trend": "📈" if value > avg_7d else "📉",
                    "7d_average": round(avg_7d, 1),
                    "emoji": self.get_sentiment_emoji(value)
                }
        except Exception as e:
            logger.error(f"Error fetching sentiment: {e}")
            return {"error": str(e)}
    
    async def get_crypto_news(self, query: str) -> Dict[str, Any]:
        """Fetch crypto news from multiple sources"""
        articles = []
        
        # Try NewsAPI first
        api_key = os.getenv("NEWS_API_KEY")
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
                async with self.session.get(url, params=params) as response:
                    data = await response.json()
                    if data.get("status") == "ok":
                        for article in data["articles"][:5]:
                            articles.append({
                                "title": article["title"],
                                "source": article["source"]["name"],
                                "published": article["publishedAt"],
                                "url": article["url"],
                                "description": (article.get("description") or "")[:200],
                                "sentiment": self.analyze_news_sentiment(article["title"])
                            })
            except Exception as e:
                logger.error(f"NewsAPI error: {e}")
        
        # Fallback or supplement with CryptoPanic
        if len(articles) < 3:
            articles.extend(await self.get_cryptopanic_news(query))
        
        return {
            "query": query,
            "articles": articles[:5],
            "total_found": len(articles),
            "sources": ["NewsAPI", "CryptoPanic"] if articles else []
        }
    
    async def get_cryptopanic_news(self, query: str) -> List[Dict[str, Any]]:
        """Fallback to CryptoPanic for crypto news"""
        articles = []
        try:
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                "auth_token": os.getenv("CRYPTOPANIC_API_KEY", ""),
                "filter": query.lower().replace(" ", "_"),
                "public": "true"
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    for result in data.get("results", [])[:3]:
                        articles.append({
                            "title": result["title"],
                            "source": result["source"]["title"],
                            "published": result["published_at"],
                            "url": result["url"],
                            "votes": result.get("votes", {}),
                            "sentiment": self.analyze_news_sentiment(result["title"])
                        })
        except Exception as e:
            logger.error(f"CryptoPanic error: {e}")
        
        return articles
    
    async def get_whale_activity(self, min_value_usd: float) -> Dict[str, Any]:
        """Simulate whale activity tracking"""
        # In a real implementation, this would connect to Etherscan or similar
        return {
            "note": "Whale tracking simulation",
            "min_value_usd": min_value_usd,
            "recent_large_transactions": [
                {
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "type": "transfer",
                    "value_usd": 5_500_000,
                    "from": "Binance Hot Wallet",
                    "to": "Unknown Wallet",
                    "token": "ETH"
                },
                {
                    "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
                    "type": "transfer",
                    "value_usd": 12_300_000,
                    "from": "Unknown Wallet",
                    "to": "Coinbase",
                    "token": "BTC"
                }
            ],
            "analysis": "Moderate whale activity. Mixed signals with both accumulation and distribution."
        }
    
    async def add_to_portfolio(self, symbol: str, quantity: float, entry_price: float) -> Dict[str, Any]:
        """Add crypto to portfolio"""
        symbol = symbol.upper()
        
        if symbol in portfolio:
            # Update existing position
            existing = portfolio[symbol]
            total_quantity = existing["quantity"] + quantity
            total_cost = existing["total_cost"] + (quantity * entry_price)
            avg_price = total_cost / total_quantity
            
            portfolio[symbol] = {
                "quantity": total_quantity,
                "entry_price": avg_price,
                "total_cost": total_cost,
                "added_at": existing["added_at"],
                "last_updated": datetime.now().isoformat()
            }
        else:
            # New position
            portfolio[symbol] = {
                "quantity": quantity,
                "entry_price": entry_price,
                "total_cost": quantity * entry_price,
                "added_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
        
        return {
            "success": True,
            "symbol": symbol,
            "quantity": quantity,
            "entry_price": entry_price,
            "total_cost": quantity * entry_price,
            "portfolio_size": len(portfolio)
        }
    
    async def check_portfolio(self) -> Dict[str, Any]:
        """Check portfolio performance"""
        if not portfolio:
            return {
                "portfolio": [],
                "total_value": 0,
                "total_cost": 0,
                "profit_loss": 0,
                "message": "Portfolio is empty"
            }
        
        portfolio_data = []
        total_value = 0
        total_cost = 0
        
        # Batch price requests
        symbols = list(portfolio.keys())
        prices = {}
        
        for symbol in symbols:
            price_data = await self.get_crypto_price(symbol)
            if "error" not in price_data:
                prices[symbol] = price_data["price"]
        
        for symbol, holding in portfolio.items():
            if symbol in prices:
                current_price = prices[symbol]
                current_value = holding["quantity"] * current_price
                profit_loss = current_value - holding["total_cost"]
                profit_loss_pct = (profit_loss / holding["total_cost"]) * 100
                
                portfolio_data.append({
                    "symbol": symbol,
                    "quantity": round(holding["quantity"], 6),
                    "entry_price": round(holding["entry_price"], 2),
                    "current_price": round(current_price, 2),
                    "current_value": round(current_value, 2),
                    "profit_loss": round(profit_loss, 2),
                    "profit_loss_pct": round(profit_loss_pct, 2),
                    "status": "🟢" if profit_loss > 0 else "🔴"
                })
                
                total_value += current_value
                total_cost += holding["total_cost"]
        
        total_pl = total_value - total_cost
        total_pl_pct = (total_pl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "portfolio": sorted(portfolio_data, key=lambda x: x["current_value"], reverse=True),
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_profit_loss": round(total_pl, 2),
            "total_profit_loss_pct": round(total_pl_pct, 2),
            "status": "🟢 Profit" if total_pl > 0 else "🔴 Loss",
            "best_performer": max(portfolio_data, key=lambda x: x["profit_loss_pct"])["symbol"] if portfolio_data else None,
            "worst_performer": min(portfolio_data, key=lambda x: x["profit_loss_pct"])["symbol"] if portfolio_data else None
        }
    
    async def compare_cryptos(self, symbols: List[str]) -> Dict[str, Any]:
        """Compare multiple cryptocurrencies"""
        comparisons = []
        
        # Fetch all prices concurrently
        tasks = [self.get_crypto_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        
        for i, data in enumerate(results):
            if "error" not in data:
                # Add performance ranking
                data["rank"] = i + 1
                comparisons.append(data)
        
        # Sort by 24h change
        comparisons.sort(key=lambda x: x.get("24h_change", 0), reverse=True)
        
        # Add relative performance
        if comparisons:
            best_performer = comparisons[0]
            worst_performer = comparisons[-1]
            
            return {
                "comparisons": comparisons,
                "best_performer": {
                    "symbol": best_performer["symbol"],
                    "change": best_performer["24h_change"]
                },
                "worst_performer": {
                    "symbol": worst_performer["symbol"],
                    "change": worst_performer["24h_change"]
                },
                "summary": f"Best: {best_performer['symbol']} ({best_performer['24h_change']}%), "
                          f"Worst: {worst_performer['symbol']} ({worst_performer['24h_change']}%)"
            }
        
        return {"comparisons": comparisons, "error": "No valid data found"}
    
    async def analyze_krom_call(self, ticker: str, contract_address: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a KROM call with additional context"""
        analysis = {
            "ticker": ticker.upper(),
            "contract_address": contract_address,
            "timestamp": datetime.now().isoformat()
        }
        
        # Get current price if available
        price_data = await self.get_crypto_price(ticker)
        if "error" not in price_data:
            analysis["current_price"] = price_data
        
        # Get recent news
        news_data = await self.get_crypto_news(ticker)
        if news_data.get("articles"):
            analysis["recent_news"] = news_data["articles"][:3]
        
        # Get market sentiment
        sentiment = await self.get_market_sentiment()
        analysis["market_sentiment"] = sentiment
        
        # Risk assessment
        risk_factors = []
        if sentiment.get("value", 50) > 75:
            risk_factors.append("Market in extreme greed - higher risk of correction")
        if price_data.get("24h_change", 0) > 20:
            risk_factors.append("Significant recent pump - potential FOMO")
        
        analysis["risk_factors"] = risk_factors
        analysis["risk_level"] = "High" if len(risk_factors) > 1 else "Medium" if risk_factors else "Low"
        
        return analysis
    
    async def get_trending_cryptos(self) -> Dict[str, Any]:
        """Get trending cryptocurrencies"""
        try:
            url = "https://api.coingecko.com/api/v3/search/trending"
            async with self.session.get(url) as response:
                data = await response.json()
                
                trending = []
                for coin in data.get("coins", [])[:7]:
                    item = coin["item"]
                    trending.append({
                        "symbol": item["symbol"],
                        "name": item["name"],
                        "rank": item["market_cap_rank"],
                        "price_btc": item["price_btc"],
                        "thumb": item["thumb"],
                        "score": coin["score"]
                    })
                
                return {
                    "trending": trending,
                    "updated_at": datetime.now().isoformat(),
                    "source": "CoinGecko Trending"
                }
        except Exception as e:
            logger.error(f"Error fetching trending: {e}")
            return {"error": str(e)}
    
    async def calculate_position_size(self, account_size: float, risk_percentage: float, 
                                    entry_price: float, stop_loss: float) -> Dict[str, Any]:
        """Calculate optimal position size based on risk management"""
        # Calculate risk per trade
        risk_amount = account_size * (risk_percentage / 100)
        
        # Calculate price difference
        price_diff = abs(entry_price - stop_loss)
        price_diff_pct = (price_diff / entry_price) * 100
        
        # Calculate position size
        position_size = risk_amount / price_diff
        position_value = position_size * entry_price
        
        # Calculate leverage if position is larger than account
        leverage = position_value / account_size if position_value > account_size else 1
        
        return {
            "account_size": account_size,
            "risk_percentage": risk_percentage,
            "risk_amount": round(risk_amount, 2),
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "position_size": round(position_size, 6),
            "position_value": round(position_value, 2),
            "stop_loss_percentage": round(price_diff_pct, 2),
            "leverage_required": round(leverage, 2),
            "max_loss": round(risk_amount, 2),
            "risk_reward_ratios": {
                "1:1": round(entry_price + price_diff, 2),
                "1:2": round(entry_price + (price_diff * 2), 2),
                "1:3": round(entry_price + (price_diff * 3), 2)
            }
        }
    
    def symbol_to_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko ID"""
        mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "SOL": "solana",
            "ADA": "cardano",
            "XRP": "ripple",
            "DOT": "polkadot",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "MATIC": "matic-network",
            "LINK": "chainlink",
            "UNI": "uniswap",
            "ATOM": "cosmos",
            "LTC": "litecoin",
            "ETC": "ethereum-classic",
            "XLM": "stellar",
            "NEAR": "near",
            "ALGO": "algorand",
            "CRO": "crypto-com-chain",
            "VET": "vechain",
            "APE": "apecoin",
            "SAND": "the-sandbox",
            "MANA": "decentraland",
            "AXS": "axie-infinity",
            "THETA": "theta-token",
            "ICP": "internet-computer",
            "FIL": "filecoin",
            "AR": "arweave",
            "OP": "optimism",
            "ARB": "arbitrum",
            "INJ": "injective-protocol"
        }
        return mapping.get(symbol.upper(), symbol.lower())
    
    def analyze_sentiment(self, value: int) -> str:
        """Analyze Fear & Greed value"""
        if value <= 25:
            return "Extreme Fear - Potential buying opportunity, but be cautious of further downside"
        elif value <= 45:
            return "Fear - Market is fearful, might be accumulation phase for long-term investors"
        elif value <= 55:
            return "Neutral - Market is balanced, no strong directional bias"
        elif value <= 75:
            return "Greed - Market is getting greedy, be careful with new entries"
        else:
            return "Extreme Greed - High risk of correction, consider taking profits on positions"
    
    def get_sentiment_emoji(self, value: int) -> str:
        """Get emoji for sentiment value"""
        if value <= 25:
            return "😱"
        elif value <= 45:
            return "😨"
        elif value <= 55:
            return "😐"
        elif value <= 75:
            return "😊"
        else:
            return "🤑"
    
    def analyze_news_sentiment(self, title: str) -> str:
        """Basic sentiment analysis for news titles"""
        positive_words = ["surge", "rally", "bullish", "gain", "rise", "pump", "moon", "ath", "breakout"]
        negative_words = ["crash", "dump", "bearish", "fall", "drop", "plunge", "hack", "scam", "sec"]
        
        title_lower = title.lower()
        
        positive_count = sum(1 for word in positive_words if word in title_lower)
        negative_count = sum(1 for word in negative_words if word in title_lower)
        
        if positive_count > negative_count:
            return "🟢 Positive"
        elif negative_count > positive_count:
            return "🔴 Negative"
        else:
            return "⚪ Neutral"
    
    async def run(self):
        """Run the MCP server"""
        async with self:
            await stdio_server(self.server).run()

def main():
    """Main entry point"""
    server = CryptoMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()
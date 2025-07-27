# KROM MCP Crypto Analysis Server

A powerful Model Context Protocol (MCP) server that provides cryptocurrency analysis tools directly within Claude Desktop.

## 🚀 Quick Start

### 1. Installation

```bash
# Run the setup script
./setup-mcp.sh

# Copy and configure environment variables
cp .env.example .env
# Edit .env and add your API keys
```

### 2. Start the MCP Server

```bash
# Activate virtual environment
source mcp-venv/bin/activate

# Run the server
python mcp-server.py
```

### 3. Configure Claude Desktop

1. Open Claude Desktop settings
2. Go to Developer → MCP Settings
3. Add the configuration from `claude-config.json`
4. Restart Claude Desktop

### 4. Open the Dashboard

Open `mcp-dashboard.html` in your browser to monitor MCP server activity.

## 🛠️ Available Tools

### Price & Market Data
- **get_crypto_price** - Get current price, market cap, and 24h change
- **get_market_sentiment** - Fear & Greed Index with analysis
- **compare_cryptos** - Compare multiple cryptocurrencies
- **get_trending_cryptos** - See what's trending on CoinGecko

### News & Research
- **get_crypto_news** - Latest news from multiple sources
- **get_whale_activity** - Track large transactions
- **analyze_krom_call** - Deep analysis of KROM signals

### Portfolio Management
- **add_to_portfolio** - Track your positions
- **check_portfolio** - View performance and P&L
- **calculate_position_size** - Risk management calculator

## 💬 Example Claude Conversations

### Basic Price Check
```
You: What's the current price of Bitcoin?
Claude: I'll check the current Bitcoin price for you.
[Uses get_crypto_price tool]
Bitcoin (BTC) is currently trading at $45,250, up 2.5% in the last 24 hours...
```

### Complex Analysis
```
You: Why is the crypto market down today?
Claude: Let me analyze the current market conditions.
[Uses get_market_sentiment, get_crypto_news, get_whale_activity]
The market is showing signs of fear (index at 35)...
```

### Portfolio Management
```
You: Add 0.5 BTC at $44,000 to my portfolio
Claude: I'll add that Bitcoin position to your portfolio.
[Uses add_to_portfolio]
Successfully added 0.5 BTC at $44,000...
```

### KROM Integration
```
You: Analyze this KROM call for PEPE
Claude: I'll analyze the PEPE token from the KROM call.
[Uses analyze_krom_call, get_crypto_price, get_crypto_news]
Here's my analysis of the PEPE call...
```

## 🔧 API Configuration

### Required APIs (Free Tiers Available)

1. **NewsAPI** (100 requests/day free)
   - Sign up at: https://newsapi.org
   - Add key to `.env`

2. **CryptoPanic** (Optional, enhanced news)
   - Sign up at: https://cryptopanic.com/developers/api/
   - Add key to `.env`

3. **Etherscan** (Optional, for whale tracking)
   - Sign up at: https://etherscan.io/apis
   - Add key to `.env`

## 📊 Dashboard Features

The web dashboard (`mcp-dashboard.html`) provides:
- Real-time API call statistics
- Activity feed showing recent tool usage
- Portfolio value tracking
- Market sentiment indicator
- Tool usage breakdown

## 🔗 Integration with Existing KROM System

This MCP server complements your existing KROMV12 system:

1. **Your Supabase Functions**: Continue running automatically
2. **MCP Server**: Provides interactive analysis on-demand
3. **Both Systems**: Can share the same Supabase database (optional)

### Optional Database Integration

To connect MCP to your Supabase:
1. Add Supabase credentials to `.env`
2. Uncomment database features in `mcp-server.py`
3. Access your `crypto_calls` data directly

## 🐛 Troubleshooting

### MCP Server Won't Start
- Check Python version (3.8+ required)
- Verify virtual environment is activated
- Check for port conflicts

### Claude Can't Connect
- Ensure MCP server is running
- Verify path in `claude-config.json` is absolute
- Restart Claude Desktop after config changes

### No Data Showing
- Check API keys in `.env`
- Verify internet connection
- Check rate limits on free API tiers

## 🚀 Advanced Usage

### Custom Analysis Workflows
```python
# Example: Multi-step analysis
1. Get trending cryptos
2. Compare top 3 performers
3. Check news sentiment
4. Calculate position sizes
5. Add winning trades to portfolio
```

### Risk Management
```
You: Calculate position size for $10k account, 2% risk, BTC entry at $45k, stop at $43k
Claude: [Calculates optimal position size with leverage requirements]
```

### Market Timing
```
You: Is this a good time to buy crypto?
Claude: [Checks sentiment, news, whale activity, and provides comprehensive analysis]
```

## 📈 Future Enhancements

- WebSocket support for real-time updates
- Integration with more exchanges
- Advanced charting in dashboard
- Automated trading signals
- Discord/Telegram bot integration

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation
3. Ensure all dependencies are installed

---

**Version**: 1.0
**Last Updated**: May 2025
**Compatible with**: Claude Desktop 1.0+
#!/usr/bin/env python3
"""
Test script for KROM MCP Server
Tests all available tools and generates sample data for the dashboard
"""

import asyncio
import json
from datetime import datetime
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the MCP server components
# Since the file is mcp-server.py (with hyphen), we need to import it differently
import importlib.util
spec = importlib.util.spec_from_file_location("mcp_server", "mcp-server.py")
mcp_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_server)
CryptoMCPServer = mcp_server.CryptoMCPServer

async def test_all_tools():
    """Test all available MCP tools"""
    print("🧪 KROM MCP Server Test Suite")
    print("=" * 50)
    
    # Create server instance
    async with CryptoMCPServer() as server:
        tests = [
            {
                "name": "get_crypto_price",
                "args": {"symbol": "BTC"},
                "description": "Testing Bitcoin price fetch"
            },
            {
                "name": "get_crypto_price",
                "args": {"symbol": "ETH"},
                "description": "Testing Ethereum price fetch"
            },
            {
                "name": "get_market_sentiment",
                "args": {},
                "description": "Testing Fear & Greed Index"
            },
            {
                "name": "get_crypto_news",
                "args": {"query": "Bitcoin"},
                "description": "Testing crypto news fetch"
            },
            {
                "name": "get_trending_cryptos",
                "args": {},
                "description": "Testing trending cryptocurrencies"
            },
            {
                "name": "add_to_portfolio",
                "args": {"symbol": "BTC", "quantity": 0.1, "entry_price": 45000},
                "description": "Testing portfolio addition"
            },
            {
                "name": "add_to_portfolio",
                "args": {"symbol": "ETH", "quantity": 2, "entry_price": 2500},
                "description": "Adding ETH to portfolio"
            },
            {
                "name": "check_portfolio",
                "args": {},
                "description": "Testing portfolio check"
            },
            {
                "name": "compare_cryptos",
                "args": {"symbols": ["BTC", "ETH", "SOL"]},
                "description": "Testing crypto comparison"
            },
            {
                "name": "calculate_position_size",
                "args": {
                    "account_size": 10000,
                    "risk_percentage": 2,
                    "entry_price": 45000,
                    "stop_loss": 43000
                },
                "description": "Testing position size calculator"
            },
            {
                "name": "analyze_krom_call",
                "args": {"ticker": "PEPE"},
                "description": "Testing KROM call analysis"
            },
            {
                "name": "get_whale_activity",
                "args": {"min_value_usd": 1000000},
                "description": "Testing whale activity tracker"
            }
        ]
        
        results = []
        failed_tests = []
        
        for test in tests:
            print(f"\n📍 {test['description']}...")
            print(f"   Tool: {test['name']}")
            print(f"   Args: {test['args']}")
            
            try:
                # Call the tool method directly
                method = getattr(server, test['name'])
                result = await method(**test['args'])
                
                if "error" in result:
                    print(f"   ⚠️  Warning: {result['error']}")
                    failed_tests.append(test['name'])
                else:
                    print(f"   ✅ Success!")
                    if isinstance(result, dict):
                        # Print key results
                        if "price" in result:
                            print(f"   💰 Price: ${result['price']}")
                        if "value" in result and "classification" in result:
                            print(f"   😊 Sentiment: {result['classification']} ({result['value']})")
                        if "articles" in result:
                            print(f"   📰 Found {len(result['articles'])} articles")
                        if "portfolio" in result:
                            print(f"   💼 Portfolio items: {len(result['portfolio'])}")
                
                results.append({
                    "test": test['name'],
                    "status": "pass" if "error" not in result else "warning",
                    "result": result
                })
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                failed_tests.append(test['name'])
                results.append({
                    "test": test['name'],
                    "status": "fail",
                    "error": str(e)
                })
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total tests: {len(tests)}")
        print(f"Passed: {len([r for r in results if r['status'] == 'pass'])}")
        print(f"Warnings: {len([r for r in results if r['status'] == 'warning'])}")
        print(f"Failed: {len([r for r in results if r['status'] == 'fail'])}")
        
        if failed_tests:
            print(f"\n⚠️  Tests with issues: {', '.join(set(failed_tests))}")
            print("   This might be due to missing API keys in .env")
        
        # Save results
        print("\n💾 Saving test results to test-results.json...")
        with open("test-results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": len(tests),
                    "passed": len([r for r in results if r['status'] == 'pass']),
                    "warnings": len([r for r in results if r['status'] == 'warning']),
                    "failed": len([r for r in results if r['status'] == 'fail'])
                },
                "results": results
            }, f, indent=2)
        
        print("\n✅ Test suite completed!")
        print("\n💡 Next steps:")
        print("1. If you see warnings about missing API keys, add them to .env")
        print("2. Run 'python mcp-server.py' to start the MCP server")
        print("3. Open mcp-dashboard.html to view the dashboard")
        print("4. Configure Claude Desktop with claude-config.json")

async def test_dashboard_data():
    """Generate sample data for dashboard testing"""
    print("\n\n📊 Generating Dashboard Sample Data...")
    print("=" * 50)
    
    # Simulate activity log entries
    activities = []
    tools = ["get_crypto_price", "get_market_sentiment", "check_portfolio", "get_crypto_news"]
    
    for i in range(20):
        activity = {
            "timestamp": datetime.now().isoformat(),
            "tool": tools[i % len(tools)],
            "args": {"symbol": "BTC"} if i % 2 == 0 else {},
            "success": True,
            "summary": f"Test activity {i+1}"
        }
        activities.append(activity)
    
    # Save dashboard data
    dashboard_data = {
        "activities": activities,
        "stats": {
            "total_calls": 100,
            "calls_by_tool": {
                "get_crypto_price": 45,
                "get_market_sentiment": 23,
                "get_crypto_news": 20,
                "check_portfolio": 12
            },
            "start_time": datetime.now().isoformat()
        }
    }
    
    with open("dashboard-sample-data.json", "w") as f:
        json.dump(dashboard_data, f, indent=2)
    
    print("✅ Sample dashboard data saved to dashboard-sample-data.json")

def main():
    """Main test runner"""
    print("🚀 Starting KROM MCP Server Tests\n")
    
    # Check for .env file
    if not os.path.exists(".env"):
        print("⚠️  Warning: .env file not found!")
        print("   Copy .env.example to .env and add your API keys")
        print("   Some tests may fail without API keys\n")
    
    # Run tests
    asyncio.run(test_all_tools())
    asyncio.run(test_dashboard_data())
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    main()
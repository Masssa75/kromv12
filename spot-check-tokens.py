import random

# Random tokens from the last batch with their reported prices and ROI
tokens = [
    {'ticker': 'TAIKI', 'price': 0.0000003566, 'roi': -58.4, 'source': 'DexScreener'},
    {'ticker': 'GARY CLOWNSLER', 'price': 0.0000058713, 'roi': -96.7, 'source': 'GeckoTerminal'},
    {'ticker': 'BUDDY', 'price': 0.0000281500, 'roi': -94.0, 'source': 'DexScreener'},
    {'ticker': 'UNEMPLOYED', 'price': 0.0000445500, 'roi': -92.5, 'source': 'DexScreener'},
    {'ticker': 'TORCH ', 'price': 0.0000091266, 'roi': -40.2, 'source': 'GeckoTerminal'},
    {'ticker': 'RYS', 'price': 0.0014460000, 'roi': 986.7, 'source': 'DexScreener'},
    {'ticker': 'PECTRA', 'price': 0.0000342712, 'roi': -86.7, 'source': 'GeckoTerminal'},
    {'ticker': 'BITCHAT', 'price': 0.0000710300, 'roi': -31.4, 'source': 'DexScreener'},
]

print('=== 5 RANDOM TOKENS TO SPOT CHECK ===\n')
for token in random.sample(tokens, 5):
    print(f"{token['ticker']}:")
    print(f"  Reported price: ${token['price']:.10f}")
    print(f"  Reported ROI: {token['roi']:.1f}%")
    print(f"  Source: {token['source']}")
    print()
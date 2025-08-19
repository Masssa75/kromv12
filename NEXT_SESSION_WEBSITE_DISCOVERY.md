# CRITICAL INVESTIGATION IN PROGRESS - Website Discovery Problem

## Context
We discovered a massive discrepancy in token website discovery. The user correctly identified that we should be finding ~1000+ legitimate projects with websites per day, but we're only finding ~150 out of 18,000+ tokens.

## Key Findings So Far

### The Numbers Don't Add Up
- **Token Discovery Database**: 19,291 tokens total
  - Only **156 have websites (0.85%)**
  - 18,415 tokens have been checked
  - 88.5% are Solana tokens (mostly pump.fun garbage)
  
- **KROM crypto_calls Table**: 6,855 tokens
  - **3,576 have websites (52%)**
  - KROM finds ~30 legitimate projects/day from just a few KOLs
  - Many KROM tokens aren't even in our discovery table

### The Core Problem
The user's logic is irrefutable:
1. KROM (following only a handful of KOLs) finds ~30 real projects per day
2. This means the entire crypto market must create hundreds of real projects daily
3. We're capturing 17,000+ tokens per day but finding only 150 websites
4. **This means we're either missing tokens OR DexScreener doesn't have the data**

### What We've Verified
1. ✅ Token discovery is working (capturing 17k+ tokens/day from GeckoTerminal new_pools)
2. ✅ DexScreener API works when tokens have data (we tested with known tokens)
3. ✅ Website checking function works (found 156 websites)
4. ✅ We're checking tokens in batches of 30 (efficient use of DexScreener API)
5. ❌ We're NOT finding the expected ~1000+ websites per day

### Current Setup
- **Token Discovery**: `token-discovery-rapid` edge function runs every minute
  - Source: GeckoTerminal `/networks/{network}/new_pools` endpoint
  - Networks: solana, eth, base, bsc, arbitrum, polygon
  - Stores in `token_discovery` table

- **Website Checking**: `token-website-monitor` edge function runs every 10 minutes
  - Checks 50 unchecked tokens per run
  - Uses DexScreener batch API (30 tokens per call)
  - Updates `website_url`, `twitter_url`, `telegram_url`, `discord_url`

### Hypotheses to Test

1. **DexScreener Coverage Issue**
   - DexScreener might not have data for most tokens even after 24h
   - Need to manually verify some high-liquidity tokens
   
2. **Wrong Token Source**
   - GeckoTerminal new_pools might show mostly garbage
   - Real projects might not appear in new_pools immediately
   - Need to also check trending/active tokens, not just new

3. **Timing Issue** 
   - Projects add websites hours/days after launch
   - We only check each token ONCE
   - Need to implement re-checking strategy

4. **Data Quality Issue**
   - 88.5% are Solana tokens (mostly memecoins)
   - Even high liquidity tokens ($100k+) don't have websites
   - Something fundamentally wrong with either our capture or DexScreener's data

## IMMEDIATE NEXT STEPS

1. **Manual Verification**: Pick 10 high-liquidity tokens without websites and:
   - Check them manually on DexScreener.com website
   - Check them via API
   - Search for them on Google/Twitter to see if they have websites
   - This will tell us if it's a data problem or API problem

2. **Check Alternative Sources**:
   - Try DexScreener's trending tokens endpoint
   - Try GeckoTerminal's trending tokens endpoint
   - See if these have better website coverage

3. **Analyze KROM Tokens**: 
   - Take 50 KROM tokens with websites
   - Check if they exist in token_discovery
   - If not, figure out why we're not capturing them
   - If yes, check why we're not finding their websites

4. **Re-checking Strategy**:
   - Implement checking tokens multiple times (1h, 6h, 24h, 3d after launch)
   - Many projects likely add websites after initial launch

## Code Context

### Key Files
- `/supabase/functions/token-discovery-rapid/` - Token discovery function
- `/supabase/functions/token-website-monitor/` - Website checking function
- `/temp-website-analysis/token_viewer.py` - Dashboard at localhost:5020
- Database: Supabase `token_discovery` table

### Environment
- All credentials in `.env`
- Supabase project: eucfoommxxvqmmwdbkdv
- Dashboard: http://localhost:5020 (shows all discovered tokens)

## The User's Core Question
"If we're capturing all new tokens (17k/day) and checking them after 24h, why are we only finding 150 websites instead of the expected 1000+? Either we're missing tokens OR DexScreener doesn't have the website data - which is it?"

This is the critical question to answer. The user knows something is fundamentally wrong with our discovery/checking process.
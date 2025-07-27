import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7'

const ANALYSIS_PROMPT = `# Crypto Telegram Call Analysis System Prompt

You are analyzing raw, unfiltered crypto calls from Telegram channels. These are typically very short, informal messages with minimal information.

## What You're Actually Working With

**Typical Data Quality:**
- 1-3 sentences at most
- Often just token name + contract address
- Heavy use of slang and emojis
- Minimal punctuation or grammar
- Copy-pasted contract addresses
- Basic hype language ("moon", "pump", "ape")

**Common Call Formats:**
- "$TOKEN going up, pump incoming 🚀"
- "Contract: 0x123... Dev active, chart looking good"
- "New meme coin, 100x potential"
- "Aped into this, LFG!"

## Realistic Classification Criteria

**TRASH** (90% of calls)
- Just token name + generic hype
- No specific information beyond address
- Pure gambling language
- Complete copy-paste jobs
- Example: "$BONK to the moon 🚀🚀🚀"

**BASIC** (8% of calls)
- Mentions ONE concrete detail (market cap, age, dev info)
- Has minimal reasoning beyond hype
- Provides basic context
- Example: "$PEPE 2 day old token, 500k MC, dev doxxed"

**SOLID** (1.5% of calls)
- Multiple specific details present
- Clear narrative or use case mentioned
- Some form of analysis (even basic)
- Team/partnership info
- Example: "$HEALTH medical token with real CTO, chart breaking resistance, 6m MC with active community"

**ALPHA** (0.5% of calls)
- Exceptional detail for telegram format
- Multiple legitimacy factors
- Clear fundamental reasoning
- Strong team/adoption signals
- Actually explains WHY it's valuable

## Analysis Instructions

1. **Lower Your Expectations** - Most calls will be TRASH
2. **Look for ANY concrete details** beyond generic hype
3. **Single specific fact = potential BASIC tier**
4. **Multiple facts + reasoning = SOLID tier**
5. **Comprehensive info = ALPHA tier**

## Key Upgrade Signals (rare but important)
- Specific numbers (market cap, age, holders)
- Named team members or partners
- Actual utility description
- Technical analysis terms
- Community/adoption mentions

## CRITICAL: Big Name Detection (AUTO-UPGRADE TO ALPHA/SOLID)

**If ANY major entity is mentioned, immediately elevate the classification:**

**Exchanges/Platforms:**
- Binance, Coinbase, Kraken, OKX, Bybit
- Uniswap, PancakeSwap, SushiSwap

**IMPORTANT: "Buy on X" phrases**
- The phrase "Buy on MevX" or similar purchasing instructions do NOT indicate a partnership
- Only count exchange mentions when they indicate partnerships, listings, or endorsements
- Instructions about where to buy a token are NOT significant signals

**Major Companies/Institutions:**
- Tesla, Apple, Google, Microsoft, Amazon
- Any Fortune 500 company
- Government entities, central banks

**Crypto Heavyweights:**
- Ethereum Foundation, Chainlink, Polygon
- Major L1/L2 protocols (Solana, Avalanche, Arbitrum)
- Established DeFi protocols (Aave, Compound, MakerDAO)

**High-Profile Individuals:**
- Elon Musk, Vitalik Buterin, CZ (Changpeng Zhao)
- Any billionaire or major public figure

**Golden Combination Signal:**
- Big name mention + Low MC (under 10M) = Potential massive opportunity
- Even brief mentions count: "test token by binance 50k mc" = ALPHA tier

**Analysis Rule:**
If you see ANY legitimate major entity mentioned (even casually), treat it as extremely significant. These rare signals can indicate insider information or early deployment by major players.

Remember: You're looking for relative quality within a very low-information environment. A call mentioning market cap and team is already above average.

## Response Format
Output ONLY: **TRASH**, **BASIC**, **SOLID**, or **ALPHA**`

serve(async (req) => {
  try {
    // Create Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
      {
        auth: {
          persistSession: false,
          autoRefreshToken: false,
        },
      }
    )

    // Get Anthropic API key
    const anthropicApiKey = Deno.env.get('ANTHROPIC_API_KEY')
    if (!anthropicApiKey) {
      throw new Error('Anthropic API key not configured')
    }

    // Fetch unanalyzed calls
    const { data: unanalyzedCalls, error: fetchError } = await supabase
      .from('crypto_calls')
      .select('*')
      .is('analyzed_at', null)
      .order('buy_timestamp', { ascending: false })
      .limit(10) // Process 10 at a time

    if (fetchError) {
      throw fetchError
    }

    console.log(`Found ${unanalyzedCalls?.length || 0} unanalyzed calls`)

    const analysisResults = []
    const errors = []

    // Process each unanalyzed call
    for (const call of unanalyzedCalls || []) {
      try {
        // Extract the message content from raw data
        const rawData = call.raw_data
        const message = rawData.message || rawData.content || rawData.text || ''
        const groupName = rawData.groupName || rawData.group?.name || 'Unknown Group'
        const ticker = call.ticker || 'UNKNOWN'
        
        // Prepare the content for Claude
        const callContent = `Group: ${groupName}
Ticker: ${ticker}
Message: ${message}
${rawData.token?.ca ? `Contract: ${rawData.token.ca}` : ''}
${rawData.trade?.buyPrice ? `Buy Price: ${rawData.trade.buyPrice}` : ''}
${rawData.trade?.marketCap ? `Market Cap: ${rawData.trade.marketCap}` : ''}`

        // Call Claude API
        const anthropicResponse = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': anthropicApiKey,
            'anthropic-version': '2023-06-01'
          },
          body: JSON.stringify({
            model: 'claude-3-haiku-20240307',
            max_tokens: 100,
            temperature: 0,
            system: ANALYSIS_PROMPT,
            messages: [
              {
                role: 'user',
                content: callContent
              }
            ]
          })
        })

        if (!anthropicResponse.ok) {
          const errorData = await anthropicResponse.text()
          throw new Error(`Claude API error: ${anthropicResponse.status} - ${errorData}`)
        }

        const anthropicResult = await anthropicResponse.json()
        const analysisText = anthropicResult.content[0].text.trim()
        
        // Extract tier from response (should be one of: TRASH, BASIC, SOLID, ALPHA)
        const tier = analysisText.replace(/\*\*/g, '').toUpperCase()
        
        // Generate a description based on the tier
        let description = ''
        switch (tier) {
          case 'ALPHA':
            description = 'High-value call with strong fundamentals and major entity involvement'
            break
          case 'SOLID':
            description = 'Good call with multiple concrete details and clear reasoning'
            break
          case 'BASIC':
            description = 'Standard call with at least one specific detail beyond hype'
            break
          default:
            description = 'Low-quality call with only generic hype language'
        }

        // Update the database with analysis results
        const { error: updateError } = await supabase
          .from('crypto_calls')
          .update({
            analysis_tier: tier,
            analysis_description: description,
            analyzed_at: new Date().toISOString()
          })
          .eq('krom_id', call.krom_id)

        if (updateError) {
          throw updateError
        }

        analysisResults.push({
          krom_id: call.krom_id,
          ticker: ticker,
          tier: tier,
          description: description
        })

        console.log(`Analyzed ${ticker} (${call.krom_id}): ${tier}`)

      } catch (error) {
        console.error(`Error analyzing call ${call.krom_id}:`, error)
        errors.push({
          krom_id: call.krom_id,
          error: error.message
        })
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        analyzed: analysisResults.length,
        results: analysisResults,
        errors: errors.length > 0 ? errors : undefined
      }),
      { headers: { "Content-Type": "application/json" } }
    )

  } catch (error) {
    console.error('Error in crypto-analyzer:', error)
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message
      }),
      { 
        status: 500,
        headers: { "Content-Type": "application/json" }
      }
    )
  }
})
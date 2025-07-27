import { createClient } from 'npm:@supabase/supabase-js@2.39.3'

const supabaseUrl = Deno.env.get('SUPABASE_URL')!
const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

const supabase = createClient(supabaseUrl, supabaseKey)

// Search for MOMO token
const { data, error } = await supabase
  .from('crypto_calls')
  .select('krom_id, token, contract, market_cap_at_call, current_market_cap, price_at_call, current_price, ath_market_cap, fdv_at_call, current_fdv, ath_fdv')
  .eq('token', 'MOMO')
  .limit(5)

if (error) {
  console.error('Error fetching data:', error)
} else {
  console.log('MOMO token data:')
  data?.forEach((row, index) => {
    console.log(`\nRow ${index + 1}:`)
    console.log('- Token:', row.token)
    console.log('- Contract:', row.contract)
    console.log('- Price at call:', row.price_at_call)
    console.log('- Current price:', row.current_price)
    console.log('- Market cap at call:', row.market_cap_at_call)
    console.log('- Current market cap:', row.current_market_cap)
    console.log('- ATH market cap:', row.ath_market_cap)
    console.log('- FDV at call:', row.fdv_at_call)
    console.log('- Current FDV:', row.current_fdv)
    console.log('- ATH FDV:', row.ath_fdv)
  })
}

// Also check one specific contract if we know it
const momoContract = '0x3E80A0fE65beD6bAEdF6919425FDB6FDCD04444'
if (momoContract) {
  console.log('\n\nChecking specific contract:', momoContract)
  const { data: specificData, error: specificError } = await supabase
    .from('crypto_calls')
    .select('*')
    .eq('contract', momoContract)
    .single()
    
  if (specificData) {
    console.log('Raw data:', JSON.stringify(specificData.market_cap_at_call))
    console.log('Type:', typeof specificData.market_cap_at_call)
  }
}
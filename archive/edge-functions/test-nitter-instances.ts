import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const NITTER_INSTANCES = [
  'https://nitter.net',
  'https://nitter.poast.org', 
  'https://nitter.privacydev.net',
  'https://nitter.1d4.us',
  'https://nitter.kavin.rocks',
  'https://nitter.woodland.cafe',
  'https://nitter.mint.lgbt',
  'https://nitter.esmailelbob.xyz',
  'https://nitter.namazso.eu'
]

serve(async (req) => {
  try {
    const testResults = []
    const testCA = "FzNYEEKgRppHbZf9yHLdP9W5j2X6nAvJzd6Lhy7spump" // Example CA to test

    for (const instance of NITTER_INSTANCES) {
      const startTime = Date.now()
      let status = 'failed'
      let error = null
      let responseTime = 0
      let hasResults = false

      try {
        console.log(`Testing ${instance}...`)
        const searchUrl = `${instance}/search?q=${testCA}&f=tweets`
        
        const response = await fetch(searchUrl, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          },
          signal: AbortSignal.timeout(10000) // 10 second timeout
        })

        responseTime = Date.now() - startTime

        if (response.ok) {
          const html = await response.text()
          // Check if we got actual tweet content
          hasResults = html.includes('tweet-content') || html.includes('timeline-item')
          status = hasResults ? 'working' : 'no-results'
        } else {
          status = `error-${response.status}`
        }

      } catch (err) {
        error = err.message
        responseTime = Date.now() - startTime
      }

      testResults.push({
        instance,
        status,
        error,
        responseTime,
        hasResults
      })
    }

    // Sort by working instances first, then by response time
    testResults.sort((a, b) => {
      if (a.status === 'working' && b.status !== 'working') return -1
      if (a.status !== 'working' && b.status === 'working') return 1
      return a.responseTime - b.responseTime
    })

    return new Response(
      JSON.stringify({
        success: true,
        testCA,
        timestamp: new Date().toISOString(),
        results: testResults,
        workingInstances: testResults.filter(r => r.status === 'working').map(r => r.instance)
      }),
      { headers: { "Content-Type": "application/json" } }
    )

  } catch (error) {
    console.error('Error testing Nitter instances:', error)
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
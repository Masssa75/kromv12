# HANDOFF: Create HTML Mockups for Multicall UI

## Context
The KROM crypto monitoring system tracks "calls" - when KROM members post about tokens in their group. Currently, when multiple members call the same token (like YZY/Kanye's token), each call appears as a separate row in the UI, creating visual clutter. We need mockups for a "multicall" view that groups these related calls together.

## Current Problem
- **YZY token** appears 15+ times in the recent calls list
- Each row is a separate call from a different member
- Users see duplicate token entries instead of understanding it's popular
- Takes up too much screen space
- Hard to see variety of tokens being called

## Reference Design
The user provided a screenshot of the old KROM interface showing how multicalls were displayed:
- Single entry for the token (YZY) with ticker, network, contract
- Timeline of individual calls below showing:
  - Timestamp (e.g., "08:55", "08:56", "08:59")
  - Username of caller (e.g., "mewgambles", "kweensjournal", "luigiscalls")
  - ROI/performance metrics (e.g., "+$1277 ◈26% 3/day")
  - Message/comment from the caller
  - Link icon for sharing

## Current Tech Stack
- **Frontend**: Next.js 14 with TypeScript
- **UI Framework**: Tailwind CSS
- **Deployed at**: https://lively-torrone-8199e0.netlify.app/
- **Current UI**: Table-based layout with sortable columns
- **Design aesthetic**: Dark theme, crypto/trading focused

## Data Structure
Each call has:
```typescript
{
  id: string
  krom_id: string  // Unique ID from KROM API
  ticker: string   // e.g., "YZY"
  network: string  // e.g., "solana"
  pool_address: string  // Same for all calls of same token
  contract_address: string
  created_at: timestamp
  raw_data: {
    username: string  // KROM member who made the call
    text: string      // Their message/comment
    groupName: string // Which KROM group
  }
  current_price: number
  roi_percent: number
  current_market_cap: number
  ath_roi_percent: number
  liquidity_usd: number
}
```

## Requirements for Mockups

### Mockup 1: Inline Expansion (Table-Based)
- Keep current table structure
- Single row per unique token
- Show badge with call count (e.g., "15 calls")
- Click to expand and show sub-rows with individual calls
- Sub-rows slightly indented with timeline feel
- Include caller username, timestamp, ROI, message

### Mockup 2: Modal/Overlay View
- Click on token opens modal
- Token header with ticker, contract, current price
- Scrollable timeline of calls
- Each call shows: timestamp, caller, ROI change since their call, message
- Visual distinction between calls (alternating backgrounds or borders)
- Close button or click outside to dismiss

### Mockup 3: Card-Based Layout
- Replace table with card grid
- Each card represents a token
- Card header: Token name, current price, total ROI
- Card body: Mini-timeline of recent calls (last 3-5)
- "View all X calls" link if more than shown
- Responsive grid (3-4 cards per row on desktop, 1 on mobile)

### Mockup 4: Hybrid Approach
- Main table shows unique tokens only
- New column showing caller avatars/usernames (like GitHub contributors)
- Hover to see preview of calls
- Click for full timeline in side panel (not modal)
- Side panel slides in from right
- Can keep side panel open while browsing other tokens

### Mockup 5: Discord-Style Nested View
- Similar to Discord's reply threads
- Main entry for token
- Indented entries below for each call
- Collapsible with arrow icon
- Shows first 2-3 calls when collapsed
- "Show X more calls" button

## Design Guidelines

### Colors (Current Theme)
```css
--background: #0a0a0a
--foreground: #fafafa  
--card: #1a1a1a
--primary: #22c55e (green)
--destructive: #ef4444 (red)
--muted: #737373
--border: #262626
```

### Key Metrics to Display
- **Per Token**: Current price, 24h change, liquidity, market cap
- **Per Call**: Time ago, caller name, ROI since their call, message excerpt
- **Aggregated**: Total calls, first caller, trending indicator

### Interactive Elements
- Expand/collapse animations
- Hover states showing more info
- Copy contract address button
- Link to DexScreener for each token
- Filter to show only multicalls (>1 call)

## HTML/CSS Requirements

Create **standalone HTML files** with:
1. Inline CSS (no external dependencies except Tailwind CDN)
2. Sample data for 5-6 tokens including:
   - YZY with 10+ calls
   - 2-3 tokens with 2-3 calls each
   - 2-3 tokens with single calls
3. Mock JavaScript for interactions (expand/collapse, modal open/close)
4. Mobile responsive design
5. Dark theme matching current site
6. Tailwind CSS classes where appropriate

## File Naming
Create files as:
- `multicall-mockup-1-inline.html`
- `multicall-mockup-2-modal.html`
- `multicall-mockup-3-cards.html`
- `multicall-mockup-4-hybrid.html`
- `multicall-mockup-5-discord.html`

## Bonus Features to Consider
- **Live indicator**: Pulse/glow for calls made in last 5 minutes
- **Sentiment badges**: "🔥 Hot" for many calls, "🚀 Rising" for increasing ROI
- **Caller reputation**: Show caller's historical success rate
- **Time grouping**: Group calls by time periods (Last hour, Today, This week)
- **Search/filter**: Filter by token, caller, or message content

## Success Criteria
- Clean, professional trading interface aesthetic
- Reduces visual clutter from duplicate entries
- Makes it easy to see both token diversity and token popularity
- Maintains quick access to key metrics
- Smooth interactions without page refreshes
- Mobile-friendly design

## Example Data to Use
```javascript
const sampleCalls = [
  // YZY - Multiple calls
  { ticker: "YZY", network: "solana", username: "mewgambles", message: "$YZY YZY real kanye.", roi: 111, timeAgo: "2m" },
  { ticker: "YZY", network: "solana", username: "kweensjournal", message: "another ye play?", roi: 43, timeAgo: "3m" },
  { ticker: "YZY", network: "solana", username: "luigiscalls", message: "wtf", roi: 46, timeAgo: "3m" },
  { ticker: "YZY", network: "solana", username: "VeniseGems", message: "Official kanye coin?", roi: 40, timeAgo: "5m" },
  // ... more YZY calls
  
  // BONK - Few calls
  { ticker: "BONK", network: "solana", username: "cryptowhale", message: "bonk is back", roi: 25, timeAgo: "10m" },
  { ticker: "BONK", network: "solana", username: "degen123", message: "aping bonk", roi: 22, timeAgo: "15m" },
  
  // PEPE - Single call
  { ticker: "PEPE", network: "ethereum", username: "memecollector", message: "pepe szn", roi: 15, timeAgo: "1h" }
]
```

## Note on Current Implementation
The backend already sends all individual calls. The grouping/deduplication should happen in the frontend for maximum flexibility. The mockups should demonstrate different ways to present this grouped data visually.

---

**IMPORTANT**: Focus on creating visually appealing, functional mockups that solve the duplicate display problem while maintaining the ability to see individual caller details. The chosen design will be implemented in the production Next.js app.
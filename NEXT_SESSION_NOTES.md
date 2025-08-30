# Next Session Notes - Stage 2 Column Settings Fix

## Current Issue
The "Stage 2 (Contract) Analysis" checkbox option is not visible in the Column Settings modal, despite being implemented in the code.

## What's Working
- Stage 2 data (S2 score and W2: badge) displays correctly when:
  - "Show Scores" is enabled
  - "Include Rugs" is checked (for UIUI token)
- API returns Stage 2 data correctly
- Tooltip works after fixing the closing issue

## Files to Check
1. `/components/ColumnSettings.tsx` - Lines 118-125 contain the Stage 2 checkbox
2. `/components/RecentCalls.tsx` - Properly checks `columnVisibility.stage2Analysis`

## Debugging Steps for Next Session
1. Ask user to run in console: `localStorage.getItem('columnVisibility')`
2. Check if Stage 2 is in the stored settings
3. Verify the checkbox is actually rendering but maybe hidden/scrolled
4. Consider if React isn't re-rendering the modal properly

## Test Tokens
- UIUI: Score 2, HONEYPOT (needs "Include Rugs" checked)
- BIO: Score 7, LEGITIMATE (contract: 0xcb1592591996765Ec0eFc1f92599A19767ee5ffA)
- AINU: Score 4, SUSPICIOUS

## Quick Fix to Try
Have user clear localStorage and refresh:
```javascript
localStorage.clear()
location.reload()
```

This should force default settings including `stage2Analysis: true`
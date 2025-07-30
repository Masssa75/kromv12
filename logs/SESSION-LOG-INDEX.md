# Session Log Index

This index provides a comprehensive overview of all KROMV12 development sessions. For detailed session logs, see the individual SESSION-LOG-YYYY-MM.md files.

## 2025

### July 2025 Sessions

#### [July 30, 2025 - Price Accuracy Fix & Bulk Refresh](SESSION-LOG-2025-07-30.md)
- Fixed critical GeckoTerminal bug selecting wrong pools (highest price vs highest liquidity)
- Corrected 5,266 tokens with missing ROI calculations
- Implemented parallel processing (6x speed improvement) for bulk price refresh
- Successfully updated 3,408 token prices with 91% success rate

#### [July 26, 2025 - UI Improvements & Price Fetching Migration](SESSION-LOG-2025-07-26.md)
- Added date column with Thai timezone tooltips to analyzed calls table  
- Enhanced GeckoTerminal chart - maximized space, added price info grid
- Successfully migrated to Supabase edge function for price fetching
- Fixed .env parsing issues and deployed crypto-price-single with ATH support

### [May 2025 Sessions](SESSION-LOG-2025-05.md)

### [July 2025 Sessions - Complete](SESSION-LOG-2025-07.md)

---
**Note**: Individual session details have been moved to their respective log files to keep this index concise and maintainable.
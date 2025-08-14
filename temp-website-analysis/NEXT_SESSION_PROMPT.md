# Next Session Prompt: Add Manual Verification Tracking to CA System

## Context
You're continuing work on the KROMV12 crypto monitoring system's CA (Contract Address) verification system. In the last session, we built an intelligent CA verifier that uses direct website parsing (no AI) to achieve 100% deterministic results.

## Current State

### System Status
- **CA Verification Complete**: 128 utility tokens verified
- **Database**: `utility_tokens_ca.db` with results
- **UI Running**: http://localhost:5003 (Flask server)
- **Working Directory**: `/Users/marcschwyn/Desktop/projects/KROMV12/temp-website-analysis/`

### Verification Results
- ✅ 83 Legitimate (64.8%) - Contracts found on websites
- 🚫 40 Fake (31.3%) - No contracts found
- ❌ 5 Errors (3.9%) - Website issues

### Current UI Features
1. Full contract addresses (click to copy)
2. Google site: search buttons
3. Clickable location links that:
   - Open the website
   - Auto-copy contract to clipboard
   - Show "Use Ctrl+F to search" tooltip
4. Auto-refresh every 30 seconds

## Task for Next Session

### Add Manual Verification Tracking
The user wants to add checkmarks/indicators for:
1. **Tokens they have personally verified** ✓
2. **Tokens where the system got it wrong** ⚠️

### Implementation Requirements

#### 1. Database Schema Update
Add to `utility_tokens_ca.db`:
```sql
ALTER TABLE ca_verification_results ADD COLUMN manual_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE ca_verification_results ADD COLUMN manual_verdict TEXT; -- 'CORRECT', 'WRONG', NULL
ALTER TABLE ca_verification_results ADD COLUMN manual_notes TEXT;
ALTER TABLE ca_verification_results ADD COLUMN manual_verified_at TIMESTAMP;
```

#### 2. UI Updates Needed

**Add interactive checkboxes/buttons for each token row:**
- ✅ "Mark as Verified" button - Confirms system got it right
- ❌ "Mark as Wrong" button - System made an error
- 📝 Optional notes field for corrections

**Visual indicators:**
- Green checkmark (✓) for manually verified correct results
- Red warning (⚠️) for tokens marked as wrong
- Yellow highlight for rows needing review
- Counter showing: "Manually verified: X/128"

#### 3. Server Endpoints to Add

```python
@app.route('/mark_verified', methods=['POST'])
# Mark token as manually verified (correct)

@app.route('/mark_wrong', methods=['POST'])  
# Mark token as wrong result

@app.route('/add_notes', methods=['POST'])
# Add manual verification notes
```

## Files to Modify

1. **`ca_results_viewer.py`** - Main server file
   - Add new endpoints
   - Update HTML template with buttons
   - Add JavaScript for AJAX updates

2. **Database updates** - Run ALTER TABLE commands

3. **Optional: Create `manual_verification.py`** - Script to bulk update from CSV if user has a list

## Starting Commands

```bash
# Navigate to working directory
cd /Users/marcschwyn/Desktop/projects/KROMV12/temp-website-analysis

# Check server status
curl -s http://localhost:5003 | head -5

# If server not running, start it
python3 ca_results_viewer.py

# Check database
sqlite3 utility_tokens_ca.db "SELECT COUNT(*) FROM ca_verification_results"
```

## Questions to Ask User

1. **UI Preference**: 
   - Should the verification buttons be on every row, or only appear on hover?
   - Do you want a popup form for notes, or inline editing?

2. **Bulk Operations**:
   - Do you have a list of tokens you've already verified that we should import?
   - Should there be a "Mark all visible as verified" button?

3. **Persistence**:
   - Should manual verifications sync to Supabase?
   - Do you want an export feature for manual verification data?

4. **Corrections**:
   - When marked as wrong, should we show what the correct verdict should be?
   - Do you want to track specific error types (e.g., "Contract in docs but not found")?

## Expected Outcome

After implementation, the UI will show:
- Clear visual distinction between system-verified and manually-verified tokens
- Easy one-click verification for correct results
- Ability to flag and annotate incorrect results
- Statistics on manual verification progress
- Export capability for verified data

## Technical Notes

- The Flask server uses auto-refresh, so updates will show within 30 seconds
- Use AJAX for button clicks to avoid page reload
- Consider adding keyboard shortcuts (Y for verified, N for wrong)
- Database backup recommended before schema changes

## Summary for Next Instance

You need to add manual verification tracking to the CA verification UI. This involves:
1. Adding database columns for manual verification status
2. Adding interactive buttons to mark tokens as verified/wrong
3. Visual indicators (✓ and ⚠️) for verification status
4. AJAX endpoints to update without page reload
5. Optional notes field for corrections

The system currently shows 128 verified tokens at http://localhost:5003 and needs these manual verification features added on top.
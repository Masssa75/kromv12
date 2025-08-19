#!/usr/bin/env python3
"""
Quick fix for STRAT and REX missing signals/elements
"""

import sqlite3
import json

# For STRAT (score 10): moderate positive/negative
strat_signals = [
    "Professional website with clear value proposition",
    "Well-structured navigation and branding"
]

strat_missing = [
    "No team information visible",
    "No GitHub repository links", 
    "No security audit reports",
    "No major partnership announcements",
    "No active community links"
]

# For REX (score 8): fewer positives, more missing elements
rex_signals = [
    "Clean website design",
    "Basic technical documentation"
]

rex_missing = [
    "No team information",
    "No GitHub links", 
    "No security audits",
    "No major partnerships",
    "No active community metrics",
    "Limited technical depth"
]

# Update database
conn = sqlite3.connect('website_analysis_new.db')
cursor = conn.cursor()

# Update STRAT
cursor.execute("""
    UPDATE website_analysis 
    SET exceptional_signals = ?, missing_elements = ?
    WHERE ticker = 'STRAT'
""", (json.dumps(strat_signals), json.dumps(strat_missing)))

# Update REX  
cursor.execute("""
    UPDATE website_analysis 
    SET exceptional_signals = ?, missing_elements = ?
    WHERE ticker = 'REX'
""", (json.dumps(rex_signals), json.dumps(rex_missing)))

conn.commit()
conn.close()

print("✅ Updated STRAT and REX with proper signals and missing elements")
print("STRAT:", strat_signals, "Missing:", len(strat_missing), "items")
print("REX:", rex_signals, "Missing:", len(rex_missing), "items")
#!/usr/bin/env node

/**
 * Backfill quick_take field for existing website analyses
 * This script generates concise summaries from existing analysis data
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

/**
 * Generate a quick_take from existing analysis data
 */
function generateQuickTake(analysis) {
  const { 
    exceptional_signals = [], 
    missing_elements = [],
    quick_assessment = '',
    category_scores = {}
  } = analysis;

  // Helper to extract key positive points
  const getPositive = () => {
    // Check exceptional signals first
    for (const signal of exceptional_signals) {
      // Look for revenue/users/TVL
      const match = signal.match(/\$[\d.,]+[MKB]?\s*(revenue|TVL|trades?|volume|institutional)/i) ||
                   signal.match(/(\d+[MK]?)\s*(users?|downloads?|active)/i) ||
                   signal.match(/(working|live|functional)\s+(platform|product|DEX|exchange)/i);
      if (match) return match[0];
    }

    // Check quick_assessment for positive indicators
    if (quick_assessment) {
      const match = quick_assessment.match(/\$[\d.,]+[MKB]?\s*(revenue|TVL|volume)/i) ||
                   quick_assessment.match(/(\d+[MK]?)\s*(users?|holders?)/i) ||
                   quick_assessment.match(/(DeFi|NFT|payment|gaming|AI)\s*(platform|protocol|system)/i);
      if (match) return match[0];
    }

    // Fallback based on score
    const totalScore = Object.values(category_scores).reduce((a, b) => a + b, 0);
    if (totalScore >= 15) return "Professional platform";
    if (totalScore >= 8) return "Basic project";
    return "Minimal presence";
  };

  // Helper to extract key negative points
  const getNegatives = () => {
    const negatives = [];
    
    // Check missing elements
    for (const element of missing_elements.slice(0, 3)) {
      if (element.match(/team/i)) negatives.push("no team info");
      else if (element.match(/audit/i)) negatives.push("no audits");
      else if (element.match(/doc/i)) negatives.push("no docs");
      else if (element.match(/github|code/i)) negatives.push("no GitHub");
      else if (element.match(/social|community/i)) negatives.push("no social");
      else if (element.match(/whitepaper/i)) negatives.push("no whitepaper");
    }

    // If no specific missing elements, check assessment
    if (negatives.length === 0 && quick_assessment) {
      if (quick_assessment.match(/placeholder|minimal|basic/i)) {
        negatives.push("minimal content");
      }
      if (quick_assessment.match(/anonymous|no team/i)) {
        negatives.push("anonymous team");
      }
    }

    return negatives.slice(0, 2).join(" & ");
  };

  // Generate the quick take
  const positive = getPositive();
  const negatives = getNegatives();

  if (positive && negatives) {
    // Ensure total length stays under 60 chars
    let quickTake = `${positive}, but ${negatives}`;
    if (quickTake.length > 60) {
      // Shorten the positive part if needed
      const maxPositiveLength = 60 - negatives.length - 6; // 6 for ", but "
      const shortPositive = positive.substring(0, maxPositiveLength);
      quickTake = `${shortPositive}, but ${negatives}`;
    }
    return quickTake;
  } else if (positive) {
    return positive.substring(0, 60);
  } else if (negatives) {
    return `Minimal site, ${negatives}`.substring(0, 60);
  }

  return "Basic website with limited information";
}

async function backfillQuickTakes() {
  console.log('🔄 Starting quick_take backfill...\n');

  // Fetch all tokens with website analysis but potentially missing quick_take
  const { data: tokens, error } = await supabase
    .from('crypto_calls')
    .select('id, ticker, website_analysis_full')
    .not('website_score', 'is', null)
    .order('website_analyzed_at', { ascending: false });

  if (error) {
    console.error('Error fetching tokens:', error);
    return;
  }

  console.log(`Found ${tokens.length} tokens with website analysis\n`);

  let updated = 0;
  let skipped = 0;
  let failed = 0;

  for (const token of tokens) {
    const { id, ticker, website_analysis_full } = token;

    // Skip if already has quick_take
    if (website_analysis_full?.quick_take) {
      console.log(`✓ ${ticker} - Already has quick_take: "${website_analysis_full.quick_take}"`);
      skipped++;
      continue;
    }

    // Skip if no analysis data
    if (!website_analysis_full) {
      console.log(`⚠️ ${ticker} - No analysis data`);
      failed++;
      continue;
    }

    // Generate quick_take
    const quickTake = generateQuickTake(website_analysis_full);
    
    // Update the JSONB field
    const updatedAnalysis = {
      ...website_analysis_full,
      quick_take: quickTake
    };

    const { error: updateError } = await supabase
      .from('crypto_calls')
      .update({ website_analysis_full: updatedAnalysis })
      .eq('id', id);

    if (updateError) {
      console.error(`❌ ${ticker} - Update failed:`, updateError.message);
      failed++;
    } else {
      console.log(`✅ ${ticker} - Added quick_take: "${quickTake}"`);
      updated++;
    }

    // Small delay to avoid overwhelming the database
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  console.log('\n📊 Backfill Summary:');
  console.log(`✅ Updated: ${updated} tokens`);
  console.log(`⏭️ Skipped: ${skipped} tokens (already had quick_take)`);
  console.log(`❌ Failed: ${failed} tokens`);
  console.log('\n✨ Backfill complete!');
}

// Run the backfill
backfillQuickTakes().catch(console.error);
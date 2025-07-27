#!/bin/bash

# Create archive directory structure
echo "Creating archive directories..."
mkdir -p archive/edge-functions
mkdir -p archive/scripts
mkdir -p archive/sql

# Archive old Edge Functions
echo "Archiving old Edge Functions..."

# The local crypto-x-analyzer-nitter.ts is outdated (online version uses ScraperAPI)
mv edge-functions/crypto-x-analyzer-nitter.ts archive/edge-functions/ 2>/dev/null || echo "crypto-x-analyzer-nitter.ts not found"

# Keep crypto-x-analyzer-scraperapi.ts as it matches the online crypto-x-analyzer-nitter
echo "Keeping crypto-x-analyzer-scraperapi.ts (this is the active version)"

# Old poller versions
mv edge-functions/crypto-poller-final.ts archive/edge-functions/ 2>/dev/null || echo "crypto-poller-final.ts not found"
mv edge-functions/crypto-poller-fixed.ts archive/edge-functions/ 2>/dev/null || echo "crypto-poller-fixed.ts not found"

# Old analyzer versions
mv edge-functions/crypto-x-analyzer.ts archive/edge-functions/ 2>/dev/null || echo "crypto-x-analyzer.ts not found"
mv edge-functions/crypto-x-analyzer-simple.ts archive/edge-functions/ 2>/dev/null || echo "crypto-x-analyzer-simple.ts not found"
mv edge-functions/crypto-x-analyzer-cors.ts archive/edge-functions/ 2>/dev/null || echo "crypto-x-analyzer-cors.ts not found" 
mv edge-functions/crypto-x-analyzer-proxy.ts archive/edge-functions/ 2>/dev/null || echo "crypto-x-analyzer-proxy.ts not found"
mv edge-functions/crypto-x-analyzer-api.ts archive/edge-functions/ 2>/dev/null || echo "crypto-x-analyzer-api.ts not found"

# Old orchestrator versions (keeping crypto-orchestrator-with-x.ts as it's the active one)
mv edge-functions/crypto-orchestrator.ts archive/edge-functions/ 2>/dev/null || echo "crypto-orchestrator.ts not found"
mv edge-functions/crypto-orchestrator-timed.ts archive/edge-functions/ 2>/dev/null || echo "crypto-orchestrator-timed.ts not found"

# Old notifier versions (keeping crypto-notifier-complete.ts as it's the active one)
mv edge-functions/crypto-notifier.ts archive/edge-functions/ 2>/dev/null || echo "crypto-notifier.ts not found"

# Test functions
mv edge-functions/test-nitter-instances.ts archive/edge-functions/ 2>/dev/null || echo "test-nitter-instances.ts not found"

# Archive old scripts from root
echo "Archiving old scripts..."
mv test-*.js archive/scripts/ 2>/dev/null || echo "No test scripts found"
mv setup-*.js archive/scripts/ 2>/dev/null || echo "No setup scripts found"
mv check-*.js archive/scripts/ 2>/dev/null || echo "No check scripts found"
mv debug-*.js archive/scripts/ 2>/dev/null || echo "No debug scripts found"
mv analyze-*.js archive/scripts/ 2>/dev/null || echo "No analyze scripts found"
mv force-*.js archive/scripts/ 2>/dev/null || echo "No force scripts found"
mv manual-*.js archive/scripts/ 2>/dev/null || echo "No manual scripts found"
mv process-*.js archive/scripts/ 2>/dev/null || echo "No process scripts found"
mv monitor-*.js archive/scripts/ 2>/dev/null || echo "No monitor scripts found"
mv view-*.js archive/scripts/ 2>/dev/null || echo "No view scripts found"
mv direct-*.js archive/scripts/ 2>/dev/null || echo "No direct scripts found"
mv reset-*.js archive/scripts/ 2>/dev/null || echo "No reset scripts found"
mv compare-*.js archive/scripts/ 2>/dev/null || echo "No compare scripts found"
mv crypto-*.js archive/scripts/ 2>/dev/null || echo "No crypto scripts found"
mv verify-*.js archive/scripts/ 2>/dev/null || echo "No verify scripts found"
mv simple-*.js archive/scripts/ 2>/dev/null || echo "No simple scripts found"
mv fix-*.js archive/scripts/ 2>/dev/null || echo "No fix scripts found"
mv find-*.js archive/scripts/ 2>/dev/null || echo "No find scripts found"
mv full-*.js archive/scripts/ 2>/dev/null || echo "No full scripts found"
mv inspect-*.js archive/scripts/ 2>/dev/null || echo "No inspect scripts found"
mv investigate-*.js archive/scripts/ 2>/dev/null || echo "No investigate scripts found"
mv diagnose-*.js archive/scripts/ 2>/dev/null || echo "No diagnose scripts found"
mv discover-*.js archive/scripts/ 2>/dev/null || echo "No discover scripts found"

# Archive old SQL files
echo "Archiving old SQL files..."
mv create-notification-*.sql archive/sql/ 2>/dev/null || echo "No old notification SQL files found"
mv setup-*.sql archive/sql/ 2>/dev/null || echo "No setup SQL files found"
mv simple-*.sql archive/sql/ 2>/dev/null || echo "No simple SQL files found"

# Create README in archive
cat > archive/README.md << 'EOF'
# Archived Files

This directory contains old versions and unused files from the KROMV12 project.

## Structure
- `edge-functions/` - Old Edge Function versions
- `scripts/` - Old test and setup scripts  
- `sql/` - Old SQL migration files

## Note
These files are kept for reference but are no longer in use.
Check SYSTEM_DOCUMENTATION.md for current active files.

Archived on: $(date)
EOF

echo "Archive complete! Check the archive/ directory for moved files."
echo ""
echo "IMPORTANT: The following files are ACTIVE and were kept:"
echo "- edge-functions/crypto-orchestrator-with-x.ts (called 'crypto-orchestrator' online)"
echo "- edge-functions/crypto-poller.ts"
echo "- edge-functions/crypto-analyzer.ts"
echo "- edge-functions/crypto-x-analyzer-scraperapi.ts (called 'crypto-x-analyzer-nitter' online)"
echo "- edge-functions/crypto-notifier-complete.ts (called 'crypto-notifier' online)"
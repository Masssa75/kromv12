#!/bin/bash

# Create archive directory structure
echo "Creating archive directories..."
mkdir -p archive/edge-functions
mkdir -p archive/scripts
mkdir -p archive/sql

# Archive old Edge Functions
echo "Archiving old Edge Functions..."
# Old poller versions
mv edge-functions/crypto-poller-final.ts archive/edge-functions/ 2>/dev/null || echo "crypto-poller-final.ts not found"
mv edge-functions/crypto-poller-fixed.ts archive/edge-functions/ 2>/dev/null || echo "crypto-poller-fixed.ts not found"

# Old analyzer versions (if any)
mv edge-functions/crypto-x-analyzer.ts archive/edge-functions/ 2>/dev/null || echo "crypto-x-analyzer.ts not found"
mv edge-functions/crypto-x-analyzer-simple.ts archive/edge-functions/ 2>/dev/null || echo "crypto-x-analyzer-simple.ts not found"
mv edge-functions/crypto-x-analyzer-cors.ts archive/edge-functions/ 2>/dev/null || echo "crypto-x-analyzer-cors.ts not found" 
mv edge-functions/crypto-x-analyzer-proxy.ts archive/edge-functions/ 2>/dev/null || echo "crypto-x-analyzer-proxy.ts not found"
mv edge-functions/crypto-x-analyzer-api.ts archive/edge-functions/ 2>/dev/null || echo "crypto-x-analyzer-api.ts not found"

# Old orchestrator versions
mv edge-functions/crypto-orchestrator.ts archive/edge-functions/ 2>/dev/null || echo "crypto-orchestrator.ts not found"
mv edge-functions/crypto-orchestrator-timed.ts archive/edge-functions/ 2>/dev/null || echo "crypto-orchestrator-timed.ts not found"

# Test functions
mv edge-functions/test-nitter-instances.ts archive/edge-functions/ 2>/dev/null || echo "test-nitter-instances.ts not found"

# Archive old scripts from root
echo "Archiving old scripts..."
mv test-*.js archive/scripts/ 2>/dev/null || echo "No test scripts found"
mv setup-*.js archive/scripts/ 2>/dev/null || echo "No setup scripts found"
mv check-*.js archive/scripts/ 2>/dev/null || echo "No check scripts found"

# Archive old SQL files
echo "Archiving old SQL files..."
mv create-notification-*.sql archive/sql/ 2>/dev/null || echo "No old notification SQL files found"
mv setup-*.sql archive/sql/ 2>/dev/null || echo "No setup SQL files found"

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
echo "Active files remain in their original locations."
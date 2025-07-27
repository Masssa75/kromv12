#!/bin/bash

# Deploy the orchestrator Edge Function
echo "Deploying crypto-orchestrator Edge Function..."
supabase functions deploy crypto-orchestrator

echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Set up a cron job to call the orchestrator endpoint every minute"
echo "2. Disable or update any existing cron jobs for individual functions"
echo ""
echo "Orchestrator endpoint: https://your-project.supabase.co/functions/v1/crypto-orchestrator"
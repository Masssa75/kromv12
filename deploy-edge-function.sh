#!/bin/bash
# Deploy script for crypto-price-fetcher edge function

echo "Deploying crypto-price-fetcher edge function to Supabase..."
echo "Note: This requires Supabase CLI to be installed and authenticated"

# Set environment variables
export SUPABASE_ACCESS_TOKEN=sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7
export SUPABASE_PROJECT_ID=eucfoommxxvqmmwdbkdv

# Navigate to the directory containing edge functions
cd "$(dirname "$0")"

# Deploy the function
npx supabase functions deploy crypto-price-fetcher \
  --project-ref $SUPABASE_PROJECT_ID \
  --no-verify-jwt

echo "Deployment complete!"
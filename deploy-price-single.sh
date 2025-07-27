#!/bin/bash

echo "Deploying crypto-price-single edge function..."

# Export the access token
export SUPABASE_ACCESS_TOKEN="sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"

# Deploy the function
cd /Users/marcschwyn/Desktop/projects/KROMV12
npx supabase functions deploy crypto-price-single --project-ref eucfoommxxvqmmwdbkdv

echo "Deployment complete!"
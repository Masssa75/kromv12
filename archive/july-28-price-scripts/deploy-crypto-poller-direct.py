#!/usr/bin/env python3
import json
import urllib.request
import subprocess
import os

print("=== Deploying Enhanced Crypto-Poller ===")

# Try using supabase CLI if available
try:
    # Check if supabase CLI is available
    result = subprocess.run(['which', 'supabase'], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Supabase CLI found, attempting deployment...")
        
        # Change to the project directory
        os.chdir('/Users/marcschwyn/Desktop/projects/KROMV12')
        
        # Try to deploy
        deploy_result = subprocess.run(
            ['supabase', 'functions', 'deploy', 'crypto-poller'], 
            capture_output=True, 
            text=True,
            timeout=60
        )
        
        if deploy_result.returncode == 0:
            print("🎉 Deployment successful!")
            print("Output:", deploy_result.stdout)
        else:
            print("❌ Deployment failed:")
            print("Error:", deploy_result.stderr)
            print("You'll need to deploy manually via Supabase Dashboard")
    else:
        print("❌ Supabase CLI not found")
        print("Please deploy manually via Supabase Dashboard")
        
except Exception as e:
    print(f"❌ Error during deployment: {e}")
    print("Please deploy manually via Supabase Dashboard")

print(f"\n=== Manual Deployment Instructions ===")
print(f"1. Go to: https://supabase.com/dashboard/project/eucfoommxxvqmmwdbkdv/functions")
print(f"2. Click 'crypto-poller' function")
print(f"3. Replace code with contents of: edge-functions/crypto-poller.ts") 
print(f"4. Click 'Deploy'")

print(f"\n=== Test Command After Deployment ===")
print(f'curl -X POST "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-poller" \\')
print(f'  -H "Authorization: Bearer $(grep SUPABASE_SERVICE_ROLE_KEY .env | cut -d\'=\' -f2)" \\')
print(f'  -H "Content-Type: application/json"')
#!/usr/bin/env python3
"""Get Supabase project information using access token"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

access_token = os.getenv("SUPABASE_ACCESS_TOKEN")
if not access_token:
    print("ERROR: SUPABASE_ACCESS_TOKEN not found in .env file")
    exit(1)

# Supabase Management API endpoint
base_url = "https://api.supabase.com"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

print("Fetching Supabase projects...")
print("=" * 60)

# Get all projects
projects_response = requests.get(f"{base_url}/v1/projects", headers=headers)

if projects_response.status_code != 200:
    print(f"Error fetching projects: {projects_response.status_code}")
    print(projects_response.text)
    exit(1)

projects = projects_response.json()

# Look for KROMV12 project
kromv12_project = None
for project in projects:
    print(f"\nProject: {project['name']}")
    print(f"  ID: {project['id']}")
    print(f"  Organization ID: {project['organization_id']}")
    print(f"  Region: {project['region']}")
    print(f"  Created: {project['created_at']}")
    
    if "KROM" in project['name'].upper() or "V12" in project['name']:
        kromv12_project = project
        print("  ✓ This appears to be the KROMV12 project!")

if kromv12_project:
    project_id = kromv12_project['id']
    
    print(f"\n{'=' * 60}")
    print(f"KROMV12 Project Details:")
    print(f"{'=' * 60}")
    
    # Get project API keys
    print("\nFetching API keys...")
    keys_response = requests.get(f"{base_url}/v1/projects/{project_id}/api-keys", headers=headers)
    
    if keys_response.status_code == 200:
        keys = keys_response.json()
        
        print("\nProject URLs and Keys:")
        print(f"SUPABASE_URL=https://{project_id}.supabase.co")
        
        for key in keys:
            if key['name'] == 'anon':
                print(f"SUPABASE_ANON_KEY={key['api_key']}")
            elif key['name'] == 'service_role':
                print(f"SUPABASE_SERVICE_ROLE_KEY={key['api_key']}")
    
    # Get database connection info
    print("\nFetching database info...")
    db_response = requests.get(f"{base_url}/v1/projects/{project_id}/database", headers=headers)
    
    if db_response.status_code == 200:
        db_info = db_response.json()
        print(f"\nDatabase Host: {db_info.get('host', 'N/A')}")
        print(f"Database Port: {db_info.get('port', 'N/A')}")
        print(f"Database Name: {db_info.get('name', 'postgres')}")
    
    print("\n✓ Copy the SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY above to your .env file")
    
else:
    print("\n⚠️  Could not find KROMV12 project. Available projects listed above.")
    print("Please check the project name or ID.")
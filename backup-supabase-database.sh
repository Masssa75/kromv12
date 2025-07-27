#!/bin/bash

# Supabase Database Backup Script
# Make sure to set these environment variables or replace with actual values

SUPABASE_DB_URL="your-project-ref.supabase.co"
SUPABASE_DB_PASSWORD="your-database-password"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)

echo "🔵 Starting Supabase database backup..."

# Create backup directory
mkdir -p ./supabase-backup

# Backup the database using pg_dump
# You can find your database connection string in Supabase Dashboard > Settings > Database
echo "📥 Downloading database backup..."
pg_dump "postgresql://postgres:${SUPABASE_DB_PASSWORD}@db.${SUPABASE_DB_URL}:5432/postgres" > ./supabase-backup/database_backup_${BACKUP_DATE}.sql

echo "✅ Database backed up to: ./supabase-backup/database_backup_${BACKUP_DATE}.sql"

# Also export as custom format for more options
pg_dump -Fc "postgresql://postgres:${SUPABASE_DB_PASSWORD}@db.${SUPABASE_DB_URL}:5432/postgres" > ./supabase-backup/database_backup_${BACKUP_DATE}.dump

echo "✅ Custom format backup: ./supabase-backup/database_backup_${BACKUP_DATE}.dump"
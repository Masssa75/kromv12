# Supabase Project Backup Guide

## Before Deleting Your Supabase Project

### 1. Database Backup

**Option A: Using Supabase Dashboard (Easiest)**
1. Go to your Supabase Dashboard
2. Navigate to **Settings** → **Database**
3. Click **Backups** tab
4. Click **Download backup** to get the latest backup
5. Save the `.sql` file locally

**Option B: Using pg_dump (More Control)**
1. Get your connection string from: **Settings** → **Database** → **Connection string**
2. Run: `chmod +x backup-supabase-database.sh`
3. Edit the script with your credentials
4. Run: `./backup-supabase-database.sh`

### 2. Edge Functions Backup

Your Edge Functions are already backed up locally in `/edge-functions/`:
- `crypto-orchestrator-with-x.ts`
- `crypto-poller.ts`
- `crypto-analyzer.ts`
- `crypto-x-analyzer-nitter.ts`
- `crypto-notifier-complete.ts`

### 3. Environment Variables Backup

**CRITICAL: Save all your secrets!**

```bash
# Create a .env.backup file with these values from Supabase Dashboard → Settings → Edge Functions → Secrets
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=
KROM_API_TOKEN=
ANTHROPIC_API_KEY=
SCRAPERAPI_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_GROUP_ID=
TELEGRAM_BOT_TOKEN_PREMIUM=
TELEGRAM_GROUP_ID_PREMIUM=
```

### 4. Storage Backup (if using)

If you're using Supabase Storage:
1. Go to **Storage** in dashboard
2. Download any files/buckets you have

### 5. Auth Users Export (if applicable)

1. Go to **Authentication** → **Users**
2. Click **Export users** button
3. Save the CSV file

## Complete Backup Checklist

- [ ] Database backup downloaded (.sql file)
- [ ] Edge Functions code (already in `/edge-functions/`)
- [ ] Environment variables saved to `.env.backup`
- [ ] Storage files downloaded (if any)
- [ ] Auth users exported (if any)
- [ ] SQL migrations saved (in your `.sql` files)

## After Backup

Once you have all backups:
1. Create a zip archive: `zip -r supabase-backup-$(date +%Y%m%d).zip supabase-backup/ edge-functions/ *.sql .env.backup`
2. Store the backup in a safe location (cloud storage, external drive)
3. Then you can safely delete the Supabase project

## To Delete Project

1. Go to Supabase Dashboard
2. Select your project
3. Go to **Settings** → **General**
4. Scroll to bottom → **Delete project**
5. Type your project name to confirm
6. Click **Delete project**

## Important Notes

- **Cron Jobs**: Remember you have a cron job at cron-job.org pointing to your Edge Functions. Disable it first!
- **Telegram Bots**: Your Telegram bots will stop working once the project is deleted
- **API Keys**: Some API keys (like KROM_API_TOKEN) might be tied to this specific deployment
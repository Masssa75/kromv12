# Supabase Cron Jobs Setup Guide

## Overview
This guide explains how to set up Supabase cron jobs to replace the external cron-job.org setup for crypto monitoring.

## Edge Functions to Schedule

1. **crypto-orchestrator** - Main pipeline that coordinates all monitoring tasks
   - Runs: Every minute
   - Purpose: Polls KROM API, analyzes calls, performs X research, sends notifications

2. **crypto-ath-update** - ATH tracking and notification system
   - Runs: Every minute
   - Purpose: Monitors tokens for new all-time highs and sends alerts

## Setup Instructions

### Step 1: Enable Cron in Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to **Database** → **Extensions**
3. Enable these extensions:
   - `pg_cron` - For scheduling jobs
   - `pg_net` - For making HTTP requests to edge functions

OR run this SQL:
```sql
create extension if not exists pg_net;
create extension if not exists pg_cron;
```

### Step 2: Get Your Anon Key

1. Find your anon key in `.env` file (SUPABASE_ANON_KEY)
2. Or get it from: Dashboard → Settings → API → Project API keys → anon public

### Step 3: Create the Cron Jobs

1. Go to **SQL Editor** in your Supabase dashboard
2. Copy the contents of `setup-supabase-cron-jobs-with-key.sql`
3. Replace `YOUR_ANON_KEY` with your actual anon key
4. Run the SQL script

### Step 4: Verify the Setup

Check that jobs are created:
```sql
select jobid, jobname, schedule, active from cron.job;
```

### Step 5: Monitor Job Execution

View recent job runs:
```sql
select 
  jobname,
  status,
  start_time,
  end_time,
  return_message
from cron.job_run_details 
order by start_time desc 
limit 20;
```

## Managing Cron Jobs

### Disable a job temporarily:
```sql
update cron.job set active = false where jobname = 'crypto-orchestrator-every-minute';
```

### Re-enable a job:
```sql
update cron.job set active = true where jobname = 'crypto-orchestrator-every-minute';
```

### Delete a job:
```sql
select cron.unschedule('crypto-orchestrator-every-minute');
```

### Change schedule (e.g., to every 5 minutes):
```sql
select cron.alter_job(
  job_id => (select jobid from cron.job where jobname = 'crypto-orchestrator-every-minute'),
  schedule => '*/5 * * * *'
);
```

## Troubleshooting

### Check if pg_cron is running:
```sql
select * from cron.job_run_details limit 1;
```

### View edge function logs:
1. Go to Dashboard → Edge Functions
2. Click on the function name
3. View logs to see if it's being invoked

### Common Issues:

1. **Jobs not running**: Make sure pg_cron extension is enabled
2. **HTTP requests failing**: Verify your anon key is correct
3. **Edge functions not found**: Ensure functions are deployed
4. **Rate limits**: Monitor edge function invocations in dashboard

## Monitoring Best Practices

1. **Set up alerts**: Create database triggers to alert on job failures
2. **Regular checks**: Review job_run_details weekly
3. **Performance**: Keep execution time under 5 minutes per job
4. **Concurrency**: Limit to 8 concurrent jobs maximum

## Disable External Cron Jobs

Once Supabase cron is working:
1. Log into cron-job.org
2. Disable or delete the crypto monitoring jobs
3. Monitor Supabase cron for 24 hours to ensure stability

## Additional Resources

- [Supabase Cron Documentation](https://supabase.com/docs/guides/database/extensions/pg_cron)
- [Edge Functions Documentation](https://supabase.com/docs/guides/functions)
- [pg_net Documentation](https://supabase.com/docs/guides/database/extensions/pg_net)
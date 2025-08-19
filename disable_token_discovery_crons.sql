-- DISABLE TOKEN DISCOVERY CRON JOBS TO STOP API USAGE
-- Run this against Supabase to pause the GeckoTerminal API calls

-- Disable token discovery (runs every minute)
SELECT cron.unschedule('token-discovery-rapid-every-minute');

-- Disable website monitoring (runs every 10 minutes)  
SELECT cron.unschedule('token-website-monitor-every-10-minutes');

-- Verify they are disabled
SELECT jobname, schedule, active, command 
FROM cron.job 
WHERE jobname LIKE '%token%'
ORDER BY jobname;
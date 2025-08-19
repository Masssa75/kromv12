-- First check if the cron job exists
SELECT jobname, schedule, active FROM cron.job WHERE jobname LIKE '%ultra%' OR jobname LIKE '%ath%';

-- Create or update the ultra tracker cron job to run every 5 minutes
-- Using smaller batch size to avoid resource limits
SELECT cron.schedule(
  'crypto-ultra-tracker-every-5-min',
  '*/5 * * * *', -- Every 5 minutes  
  $$SELECT net.http_post(
    url:='https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ultra-tracker',
    headers:=jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs'
    ),
    body:=jsonb_build_object('maxTokens', 500)
  ) as request_id$$
);

-- Also ensure crypto-ath-update is running
SELECT cron.schedule(
  'crypto-ath-update-every-min',
  '* * * * *', -- Every minute
  $$SELECT net.http_post(
    url:='https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ath-update',
    headers:=jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs'
    ),
    body:='{}'::jsonb
  ) as request_id$$
);

-- Check what cron jobs are now active
SELECT jobid, jobname, schedule, active FROM cron.job ORDER BY jobname;
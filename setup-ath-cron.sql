-- Enable required extensions if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_cron WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;

-- Grant permissions
GRANT USAGE ON SCHEMA cron TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cron TO postgres;

-- Create the cron job for ATH updates
SELECT cron.schedule(
  'ath-continuous-update',  -- job name
  '* * * * *',             -- every minute
  $$
  SELECT net.http_post(
    url:='https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ath-update',
    headers:='{"Content-Type": "application/json", "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs"}'::jsonb,
    body:='{"limit": 25}'::jsonb
  ) as request_id;
  $$
);

-- Verify the job was created
SELECT * FROM cron.job WHERE jobname = 'ath-continuous-update';
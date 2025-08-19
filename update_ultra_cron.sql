-- Delete existing ultra tracker cron job
SELECT cron.unschedule('crypto-ultra-tracker-every-minute');

-- Create new ultra tracker cron job with proper parameters
SELECT cron.schedule(
  'crypto-ultra-tracker-every-5-min',
  '*/5 * * * *',  -- Every 5 minutes instead of every minute
  $$SELECT net.http_post(
    url:='https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ultra-tracker',
    headers:=jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs'
    ),
    body:=jsonb_build_object('maxTokens', 500)
  ) as request_id$$
);
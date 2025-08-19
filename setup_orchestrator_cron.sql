-- Create orchestrator cron job that runs every minute
SELECT cron.schedule(
  'crypto-orchestrator-every-minute',
  '* * * * *',
  $$SELECT net.http_post(
    url:='https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-orchestrator-with-x',
    headers:=jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs'
    ),
    body:='{}'::jsonb
  ) as request_id$$
);

-- Check if it was created
SELECT jobid, jobname, schedule, active 
FROM cron.job 
WHERE jobname = 'crypto-orchestrator-every-minute';

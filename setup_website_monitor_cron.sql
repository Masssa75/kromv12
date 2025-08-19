-- Setup cron job for token website monitoring
-- Runs every 10 minutes to check for websites

SELECT cron.schedule(
  'token-website-monitor-every-10-min',
  '*/10 * * * *',
  $$
  SELECT net.http_post(
    url:='https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/token-website-monitor',
    headers:='{"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4"}'::jsonb
  ) AS request_id;
  $$
);
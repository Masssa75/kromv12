-- Remove existing broken cron job
SELECT cron.unschedule('token-discovery-every-10-min');

-- Create correct cron job for rapid token discovery (every minute)
SELECT cron.schedule(
  'token-discovery-rapid-every-minute',
  '* * * * *',
  $$
  SELECT net.http_post(
    url:='https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/token-discovery-rapid',
    headers:=jsonb_build_object(
      'Authorization', 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4',
      'Content-Type', 'application/json'
    ),
    body:='{}'::jsonb
  ) AS request_id;
  $$
);

-- Create cron job for website monitoring (every 10 minutes)
SELECT cron.schedule(
  'token-website-monitor-every-10-min',
  '*/10 * * * *',
  $$
  SELECT net.http_post(
    url:='https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/token-website-monitor',
    headers:=jsonb_build_object(
      'Authorization', 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4',
      'Content-Type', 'application/json'
    ),
    body:='{}'::jsonb
  ) AS request_id;
  $$
);
-- Create cron job for token discovery (every 10 minutes)
SELECT cron.schedule(
  'token-discovery-every-10-min',
  '*/10 * * * *',
  $$
  SELECT net.http_post(
    url:='https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/token-discovery-poller',
    headers:=jsonb_build_object(
      'Authorization', 'Bearer YOUR_ANON_KEY',
      'Content-Type', 'application/json'
    ),
    body:='{}'::jsonb
  ) AS request_id;
  $$
);
-- Update the ultra-tracker cron job to use smaller batch size
SELECT cron.alter(
  'crypto-ultra-tracker-every-minute',
  '* * * * *',
  $$SELECT net.http_post(
    url:='https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ultra-tracker',
    headers:=jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.settings.supabase_anon_key')
    ),
    body:=jsonb_build_object('batchSize', 5, 'delayMs', 100, 'maxTokens', 1000)
  ) as request_id$$
);
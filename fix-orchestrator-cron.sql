-- Update the orchestrator cron job to use the correct endpoint and service role key
UPDATE cron.job 
SET command = $CMD$
select net.http_post(
    url:='https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-orchestrator-with-x',
    headers:=jsonb_build_object(
        'Content-Type', 'application/json',
        'Authorization', 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4'
    ),
    body:=jsonb_build_object('trigger', 'pg_cron')
) as request_id;
$CMD$
WHERE jobname = 'crypto-orchestrator-every-minute';

-- Verify the update
SELECT jobname, schedule, active, 
       CASE 
           WHEN command LIKE '%crypto-orchestrator-with-x%' THEN 'Uses NEW endpoint ✓'
           WHEN command LIKE '%crypto-orchestrator%' THEN 'Uses OLD endpoint ✗'
           ELSE 'Unknown'
       END as endpoint_status,
       CASE
           WHEN command LIKE '%service_role%' THEN 'Service Role ✓'
           WHEN command LIKE '%anon%' THEN 'Anon Key ✗'
           ELSE 'Unknown'
       END as key_type
FROM cron.job 
WHERE jobname = 'crypto-orchestrator-every-minute';
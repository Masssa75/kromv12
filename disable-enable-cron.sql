-- To DISABLE the cron jobs:
UPDATE cron.job 
SET active = false 
WHERE jobname IN ('krom-call-analysis-every-minute', 'krom-x-analysis-every-minute');

-- To ENABLE the cron jobs:
UPDATE cron.job 
SET active = true 
WHERE jobname IN ('krom-call-analysis-every-minute', 'krom-x-analysis-every-minute');

-- To check status:
SELECT jobname, schedule, active 
FROM cron.job 
WHERE jobname LIKE '%krom%' OR jobname LIKE '%analysis%' 
ORDER BY jobname;
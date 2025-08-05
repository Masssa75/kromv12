-- Check cron job configuration
SELECT 
    jobid,
    jobname,
    schedule,
    active,
    command,
    database,
    username,
    nodename
FROM cron.job
WHERE command LIKE '%crypto-ath%'
ORDER BY jobid;

-- Check recent job runs
SELECT 
    jobid,
    runid,
    job_pid,
    database,
    username,
    command,
    status,
    return_message,
    start_time,
    end_time
FROM cron.job_run_details
WHERE command LIKE '%crypto-ath%'
ORDER BY start_time DESC
LIMIT 10;
-- Create trigger function to invoke analyzer after new calls are inserted
CREATE OR REPLACE FUNCTION trigger_analyze_new_calls()
RETURNS TRIGGER AS $$
BEGIN
  -- Only trigger if this is a new row without analysis
  IF NEW.analyzed_at IS NULL THEN
    -- Use Supabase's HTTP extension to call the Edge Function
    PERFORM
      net.http_post(
        url := current_setting('app.settings.supabase_url') || '/functions/v1/crypto-analyzer',
        headers := jsonb_build_object(
          'Content-Type', 'application/json',
          'Authorization', 'Bearer ' || current_setting('app.settings.supabase_service_role_key')
        ),
        body := jsonb_build_object('krom_id', NEW.krom_id)
      );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for new calls
DROP TRIGGER IF EXISTS analyze_new_calls_trigger ON crypto_calls;
CREATE TRIGGER analyze_new_calls_trigger
  AFTER INSERT ON crypto_calls
  FOR EACH ROW
  EXECUTE FUNCTION trigger_analyze_new_calls();

-- Create trigger function to invoke notifier after calls are analyzed
CREATE OR REPLACE FUNCTION trigger_notify_analyzed_calls()
RETURNS TRIGGER AS $$
BEGIN
  -- Only trigger if this row was just analyzed and not yet notified
  IF OLD.analyzed_at IS NULL AND NEW.analyzed_at IS NOT NULL AND NEW.notified = false THEN
    -- Use Supabase's HTTP extension to call the Edge Function
    PERFORM
      net.http_post(
        url := current_setting('app.settings.supabase_url') || '/functions/v1/crypto-notifier',
        headers := jsonb_build_object(
          'Content-Type', 'application/json',
          'Authorization', 'Bearer ' || current_setting('app.settings.supabase_service_role_key')
        ),
        body := jsonb_build_object('krom_id', NEW.krom_id)
      );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for analyzed calls
DROP TRIGGER IF EXISTS notify_analyzed_calls_trigger ON crypto_calls;
CREATE TRIGGER notify_analyzed_calls_trigger
  AFTER UPDATE ON crypto_calls
  FOR EACH ROW
  EXECUTE FUNCTION trigger_notify_analyzed_calls();

-- Enable HTTP extension if not already enabled
CREATE EXTENSION IF NOT EXISTS http;

-- Set the required configuration variables
-- You'll need to run these with your actual values:
-- ALTER DATABASE your_database_name SET app.settings.supabase_url = 'https://your-project.supabase.co';
-- ALTER DATABASE your_database_name SET app.settings.supabase_service_role_key = 'your-service-role-key';
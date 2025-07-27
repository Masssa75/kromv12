-- Option 1: Create a simple trigger that uses pg_notify
-- This can be picked up by a listener service or Edge Function

-- Create notification function for new calls
CREATE OR REPLACE FUNCTION notify_new_call()
RETURNS TRIGGER AS $$
BEGIN
  -- Send notification with the krom_id
  PERFORM pg_notify('new_crypto_call', json_build_object(
    'krom_id', NEW.krom_id,
    'ticker', NEW.ticker
  )::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for new calls
DROP TRIGGER IF EXISTS new_call_notify_trigger ON crypto_calls;
CREATE TRIGGER new_call_notify_trigger
  AFTER INSERT ON crypto_calls
  FOR EACH ROW
  EXECUTE FUNCTION notify_new_call();

-- Create notification function for analyzed calls
CREATE OR REPLACE FUNCTION notify_analyzed_call()
RETURNS TRIGGER AS $$
BEGIN
  -- Only notify if the call was just analyzed
  IF OLD.analyzed_at IS NULL AND NEW.analyzed_at IS NOT NULL THEN
    PERFORM pg_notify('analyzed_crypto_call', json_build_object(
      'krom_id', NEW.krom_id,
      'ticker', NEW.ticker,
      'analysis_tier', NEW.analysis_tier
    )::text);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for analyzed calls
DROP TRIGGER IF EXISTS analyzed_call_notify_trigger ON crypto_calls;
CREATE TRIGGER analyzed_call_notify_trigger
  AFTER UPDATE ON crypto_calls
  FOR EACH ROW
  EXECUTE FUNCTION notify_analyzed_call();
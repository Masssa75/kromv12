-- Fix BADGER token with contract 0xdee1c5753C9643E43E9D9EeeAB6238231E365E07
-- Current ATH: $105.9 -> Should be around $0.0007245
UPDATE crypto_calls
SET 
  ath_price = 0.0007245,
  ath_roi_percent = CASE 
    WHEN price_at_call > 0 THEN ((0.0007245 - price_at_call) / price_at_call) * 100
    ELSE 0
  END
WHERE contract_address = '0xdee1c5753C9643E43E9D9EeeAB6238231E365E07'
  AND ath_price > 1;

-- Fix NEKO token with contract 84tiYdMUTAjH1N3hUZ5E2S2SMZjxaeVVnoQJwzR4pump
-- Current ATH: $0.356 -> Should be around $0.0004185
UPDATE crypto_calls
SET 
  ath_price = 0.0004185,
  ath_roi_percent = CASE 
    WHEN price_at_call > 0 THEN ((0.0004185 - price_at_call) / price_at_call) * 100
    ELSE 0
  END
WHERE contract_address = '84tiYdMUTAjH1N3hUZ5E2S2SMZjxaeVVnoQJwzR4pump'
  AND ath_price > 0.01;

-- Fix USAI token with contract EcbRfg1r9DYK9JqTkCABFe8KVKXdXe2KAgrVhURQpump
-- Current ATH: $0.3679 -> Should be around $0.003679 (divide by 100)
UPDATE crypto_calls
SET 
  ath_price = 0.003679,
  ath_roi_percent = CASE 
    WHEN price_at_call > 0 THEN ((0.003679 - price_at_call) / price_at_call) * 100
    ELSE 0
  END
WHERE contract_address = 'EcbRfg1r9DYK9JqTkCABFe8KVKXdXe2KAgrVhURQpump'
  AND ath_price > 0.1;

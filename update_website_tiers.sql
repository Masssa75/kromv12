-- Update website_tier values from old system to new system
-- LOW -> TRASH (0-7 points)
-- MEDIUM -> BASIC (8-14 points)  
-- HIGH -> SOLID (15-20 points)

UPDATE crypto_calls
SET website_tier = CASE 
    WHEN website_tier = 'LOW' THEN 'TRASH'
    WHEN website_tier = 'MEDIUM' THEN 'BASIC'
    WHEN website_tier = 'HIGH' THEN 'SOLID'
    ELSE website_tier
END
WHERE website_tier IN ('LOW', 'MEDIUM', 'HIGH');
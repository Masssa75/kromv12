import requests
import json
from datetime import datetime

# Check TCM result
url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"
headers = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4"
}

# Edge function results from earlier
edge_results = {
    "TCM": {"ath_price": 0.0001138782972558933, "ath_timestamp": 1747581120, "ath_roi_percent": 19.72507110321901},
    "BIP177": {"ath_price": 0.0010343781417436555, "ath_timestamp": 1747581900, "ath_roi_percent": 246.07735304906996}
}

for ticker in ["TCM", "BIP177"]:
    edge_result = edge_results[ticker]
    print(f"\n=== {ticker} Verification ===")
    print(f"Edge Function Results:")
    print(f"  ATH Price: ${edge_result['ath_price']:.12f}")
    print(f"  ATH Date: {datetime.fromtimestamp(edge_result['ath_timestamp']).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"  ATH ROI: {edge_result['ath_roi_percent']:.2f}%")

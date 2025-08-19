#!/bin/bash

# Test OpenRouter API with curl
API_KEY="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"

echo "Testing OpenRouter API with curl..."
echo "API Key: ${API_KEY:0:20}..."
echo ""

curl -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "moonshotai/kimi-k2",
    "messages": [
      {
        "role": "user",
        "content": "Say hello"
      }
    ]
  }' 2>/dev/null | python3 -m json.tool
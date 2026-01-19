#!/bin/bash
  BASE_URL="http://localhost:3570/api"

  # Login with wrong password
  # echo "=== Login ==="
  # RESP=$(curl -s -X POST $BASE_URL/auth/login \
  #   -H "Content-Type: application/json" \
  #   -d '{"username":"ABC","password":"xuuuuuuu"}')
  # TOKEN=$(echo $RESP | jq -r '.access_token')
  # echo "With wrong password Token: $TOKEN"

  # Login
  # echo "=== Login ==="
  # RESP=$(curl -s -X POST $BASE_URL/auth/login \
  #   -H "Content-Type: application/json" \
  #   -d '{"username":"ABC","password":"uuuuuuuu"}')
  # TOKEN=$(echo $RESP | jq -r '.access_token')
  # echo "Token: $TOKEN"

  TOKEN="8tIlFDaYmLJH2_oF3WDeuFTuw9luohQFR7g8py4EpeyE7AKLPP4WaqqCd3HSHlxw"

  # Send SMS
  echo ""
  echo "=== Send SMS ==="
  curl -s -X POST $BASE_URL/sms \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"recipient":"8524 5678","content":"Test message"}' | jq

  # Send Error SMS
  echo ""
  echo "=== Send Error SMS ==="
  curl -s -X POST $BASE_URL/sms \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"recipient":"87654321","content":"Test error message"}' | jq

  # Send Bulk SMS
  echo ""
  echo "=== Send Bulk SMS ==="
  curl -X POST http://localhost:3570/api/sms/send-bulk \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{
      "recipients": ["1234-5678", "85287654321"],
      "content": "Hello everyone!"
    }'

  # List messages
  echo ""
  echo "=== List Messages ==="
  curl -s $BASE_URL/sms \
    -H "Authorization: Bearer $TOKEN" | jq


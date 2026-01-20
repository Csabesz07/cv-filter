#!/bin/bash
# Test audit API endpoint

# Get token (replace with your credentials)
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

echo "Token: ${TOKEN:0:20}..."

# Test audit endpoint
echo -e "\n=== Testing /api/audit/ranking/ ==="
curl -s http://localhost:8000/api/audit/ranking/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool

echo -e "\n=== Testing with limit=5 ==="
curl -s "http://localhost:8000/api/audit/ranking/?limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool

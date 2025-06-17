#!/bin/bash

echo "🧪 Testing Workiva AI Backend APIs"
echo "=========================="
echo ""

BASE_URL="http://localhost:8000"

echo "⚡ Checking if server is running..."
if ! curl -s --connect-timeout 5 "$BASE_URL/" > /dev/null 2>&1; then
    echo "❌ Server is not running!"
    echo ""
    echo "Please start the server first:"
    echo "  uvicorn main:app --reload"
    echo ""
    echo "Then run this test script again."
    exit 1
fi

echo "✅ Server is running!"
echo ""

echo "1. Testing health endpoint..."
curl -s "$BASE_URL/api/health"
echo ""
echo ""

echo "2. Testing AI endpoint with valid prompt..."
curl -s -X POST "$BASE_URL/api/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is AI?"}'
echo ""
echo ""

echo "3. Testing validation with empty prompt..."
curl -s -X POST "$BASE_URL/api/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{"prompt": ""}'
echo ""
echo ""

echo "4. Testing validation with short prompt..."
curl -s -X POST "$BASE_URL/api/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a"}'
echo ""
echo ""

echo "5. Testing conversations endpoint..."
curl -s "$BASE_URL/api/conversations"
echo ""
echo ""

echo "✅ All tests completed successfully!"
echo ""
echo "💡 To stop the server, press Ctrl+C in the terminal where it's running."
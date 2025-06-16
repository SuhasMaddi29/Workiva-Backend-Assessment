#!/bin/bash

# Enhanced AI API Integration - Test Suite
echo "🧪 Testing Enhanced AI API"
echo "=========================="
echo ""

BASE_URL="http://localhost:8000"

echo "1. Testing health endpoint..."
curl -s "$BASE_URL/api/health" | head -c 200
echo ""
echo ""

echo "2. Testing AI endpoint with valid prompt..."
curl -s -X POST "$BASE_URL/api/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is AI?"}' | head -c 200
echo ""
echo ""

echo "3. Testing validation with empty prompt..."
curl -s -X POST "$BASE_URL/api/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{"prompt": ""}' | head -c 200
echo ""
echo ""

echo "4. Testing validation with short prompt..."
curl -s -X POST "$BASE_URL/api/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "a"}' | head -c 200
echo ""
echo ""

echo "5. Testing conversations endpoint..."
curl -s "$BASE_URL/api/conversations" | head -c 200
echo ""
echo ""

echo "✅ Basic tests complete!"
echo "For full testing, ensure your server is running with: uvicorn main:app --reload" 
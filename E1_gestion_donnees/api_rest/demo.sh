#!/bin/bash
# Demo de l'API REST Simple

echo "🚀 Démonstration API REST Coach IA (Version Simple)"
echo "=================================================="

API_URL="http://localhost:8001"

echo "1. Test de santé de l'API..."
curl -s "$API_URL/health" | python3 -m json.tool
echo ""

echo "2. Login pour obtenir le token JWT..."
TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$TOKEN" ]; then
  echo "❌ Impossible d'obtenir le token. L'API est-elle démarrée ?"
  echo "   Lancez : python3 main.py"
  exit 1
fi

echo "✅ Token JWT obtenu : ${TOKEN:0:50}..."
echo ""

echo "3. Liste des utilisateurs (avec authentification)..."
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/users" | python3 -m json.tool
echo ""

echo "4. Liste des activités (avec pagination)..."
curl -s -H "Authorization: Bearer $TOKEN" \
  "$API_URL/api/v1/activities?page=1&per_page=3" | python3 -m json.tool
echo ""

echo "5. Création d'une nouvelle activité..."
NEW_ACTIVITY='{
  "user_id": 1,
  "activity_name": "Course de démonstration API",
  "activity_type": "running",
  "start_time": "2025-01-08T08:00:00",
  "duration_seconds": 2100,
  "distance_meters": 4500,
  "average_hr": 145,
  "calories": 280
}'

curl -s -X POST "$API_URL/api/v1/activities" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$NEW_ACTIVITY" | python3 -m json.tool

echo ""
echo "✅ Démonstration terminée !"
echo "📚 Documentation complète : $API_URL/docs"
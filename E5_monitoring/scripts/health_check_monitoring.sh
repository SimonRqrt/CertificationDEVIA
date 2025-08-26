#!/bin/bash

# Script de vérification santé monitoring - Coach IA
# Conformité C20/C21 - Validation stack complète

set -e

echo "🏥 === HEALTH CHECK MONITORING COACH AI ==="
echo "📅 Date: $(date)"
echo "🔧 Version: 1.0"
echo ""

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction utilitaire
check_service() {
    local service_name=$1
    local url=$2
    local expected_code=${3:-200}
    
    echo -n "🔍 Testing $service_name... "
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
        if [ "$response" = "$expected_code" ]; then
            echo -e "${GREEN}✅ OK ($response)${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  Unexpected code: $response${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# Fonction test métriques
check_metrics() {
    local service=$1
    local query=$2
    
    echo -n "📊 Checking $service metrics... "
    
    if result=$(curl -s "http://localhost:9090/api/v1/query?query=$query" 2>/dev/null); then
        if echo "$result" | grep -q '"status":"success"'; then
            echo -e "${GREEN}✅ Metrics OK${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️  No data${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Query failed${NC}"
        return 1
    fi
}

echo "🐳 === VERIFICATION CONTAINERS DOCKER ==="

# Vérifier si docker-compose est démarré
if ! docker compose -f ../deployment/docker-compose-monitoring.yml ps --format table | grep -q "Up"; then
    echo -e "${RED}❌ Stack monitoring non démarrée${NC}"
    echo "💡 Démarrage automatique..."
    docker compose -f ../deployment/docker-compose-monitoring.yml up -d
    echo "⏳ Attente 30 secondes pour initialisation..."
    sleep 30
fi

# Status containers
echo "📦 Status containers:"
docker compose -f ../deployment/docker-compose-monitoring.yml ps

echo ""
echo "🌐 === TESTS CONNECTIVITY SERVICES ==="

# Tests de connectivité
SERVICES_OK=0
SERVICES_TOTAL=0

# Prometheus
((SERVICES_TOTAL++))
if check_service "Prometheus" "http://localhost:9090/-/healthy"; then
    ((SERVICES_OK++))
fi

# Grafana
((SERVICES_TOTAL++))
if check_service "Grafana" "http://localhost:3000/api/health"; then
    ((SERVICES_OK++))
fi

# AlertManager
((SERVICES_TOTAL++))
if check_service "AlertManager" "http://localhost:9093/-/healthy"; then
    ((SERVICES_OK++))
fi

# Node Exporter
((SERVICES_TOTAL++))
if check_service "Node Exporter" "http://localhost:9100/metrics" "200"; then
    ((SERVICES_OK++))
fi

echo ""
echo "📈 === TESTS METRIQUES COACH AI ==="

METRICS_OK=0
METRICS_TOTAL=0

# Test services Coach AI
((METRICS_TOTAL++))
if check_metrics "Coach Services" "up{job=~\"coach-.*\"}"; then
    ((METRICS_OK++))
fi

# Test métriques système
((METRICS_TOTAL++))
if check_metrics "System Metrics" "node_memory_MemTotal_bytes"; then
    ((METRICS_OK++))
fi

# Test métriques applicatives
((METRICS_TOTAL++))
if check_metrics "HTTP Requests" "prometheus_http_requests_total"; then
    ((METRICS_OK++))
fi

echo ""
echo "🔔 === TESTS ALERTES ==="

ALERTS_OK=0
ALERTS_TOTAL=0

# Test règles d'alerte chargées
((ALERTS_TOTAL++))
echo -n "📏 Checking alert rules... "
if rules=$(curl -s "http://localhost:9090/api/v1/rules" 2>/dev/null); then
    if echo "$rules" | grep -q "coach_ai_specific_alerts"; then
        echo -e "${GREEN}✅ Rules loaded${NC}"
        ((ALERTS_OK++))
    else
        echo -e "${YELLOW}⚠️  No Coach AI rules${NC}"
    fi
else
    echo -e "${RED}❌ Rules query failed${NC}"
fi

# Test AlertManager
((ALERTS_TOTAL++))
echo -n "🚨 Checking AlertManager config... "
if config=$(curl -s "http://localhost:9093/api/v1/status" 2>/dev/null); then
    if echo "$config" | grep -q '"status":"success"'; then
        echo -e "${GREEN}✅ Config OK${NC}"
        ((ALERTS_OK++))
    else
        echo -e "${YELLOW}⚠️  Config issue${NC}"
    fi
else
    echo -e "${RED}❌ AlertManager unreachable${NC}"
fi

echo ""
echo "📊 === TESTS DASHBOARDS GRAFANA ==="

DASHBOARDS_OK=0
DASHBOARDS_TOTAL=0

# Test authentification Grafana
((DASHBOARDS_TOTAL++))
echo -n "🔐 Testing Grafana auth... "
if auth=$(curl -s -u admin:admin123 "http://localhost:3000/api/user" 2>/dev/null); then
    if echo "$auth" | grep -q '"login":"admin"'; then
        echo -e "${GREEN}✅ Auth OK${NC}"
        ((DASHBOARDS_OK++))
    else
        echo -e "${RED}❌ Auth failed${NC}"
    fi
else
    echo -e "${RED}❌ Connection failed${NC}"
fi

# Test dashboards Coach AI
((DASHBOARDS_TOTAL++))
echo -n "📈 Checking Coach AI dashboards... "
if dashboards=$(curl -s -u admin:admin123 "http://localhost:3000/api/search?tag=coach-ai" 2>/dev/null); then
    dashboard_count=$(echo "$dashboards" | jq length 2>/dev/null || echo "0")
    if [ "$dashboard_count" -gt "0" ]; then
        echo -e "${GREEN}✅ $dashboard_count dashboards found${NC}"
        ((DASHBOARDS_OK++))
    else
        echo -e "${YELLOW}⚠️  No Coach AI dashboards${NC}"
    fi
else
    echo -e "${RED}❌ Dashboard query failed${NC}"
fi

echo ""
echo "🎯 === TESTS INTEGRATION COACH AI ==="

INTEGRATION_OK=0
INTEGRATION_TOTAL=0

# Test collecte métriques applications
applications=("coach-api-fastapi:8000" "coach-django:8002" "coach-streamlit:8502")

for app in "${applications[@]}"; do
    ((INTEGRATION_TOTAL++))
    service_name=$(echo "$app" | cut -d: -f1)
    port=$(echo "$app" | cut -d: -f2)
    
    echo -n "🔌 Testing $service_name metrics collection... "
    
    # Tester si Prometheus collecte des métriques de ce service
    if result=$(curl -s "http://localhost:9090/api/v1/query?query=up{job=\"$service_name\"}" 2>/dev/null); then
        if echo "$result" | grep -q '"value":\[.*,"1"\]'; then
            echo -e "${GREEN}✅ Collecting metrics${NC}"
            ((INTEGRATION_OK++))
        elif echo "$result" | grep -q '"value":\[.*,"0"\]'; then
            echo -e "${YELLOW}⚠️  Service down${NC}"
        else
            echo -e "${YELLOW}⚠️  No metrics${NC}"
        fi
    else
        echo -e "${RED}❌ Query failed${NC}"
    fi
done

echo ""
echo "🏥 === RÉSUMÉ HEALTH CHECK ==="

total_tests=$((SERVICES_TOTAL + METRICS_TOTAL + ALERTS_TOTAL + DASHBOARDS_TOTAL + INTEGRATION_TOTAL))
total_ok=$((SERVICES_OK + METRICS_OK + ALERTS_OK + DASHBOARDS_OK + INTEGRATION_OK))

echo "📊 Services Monitoring: $SERVICES_OK/$SERVICES_TOTAL"
echo "📈 Métriques: $METRICS_OK/$METRICS_TOTAL"  
echo "🔔 Alertes: $ALERTS_OK/$ALERTS_TOTAL"
echo "📊 Dashboards: $DASHBOARDS_OK/$DASHBOARDS_TOTAL"
echo "🎯 Intégration: $INTEGRATION_OK/$INTEGRATION_TOTAL"
echo ""

percentage=$((total_ok * 100 / total_tests))

if [ $percentage -ge 90 ]; then
    echo -e "${GREEN}🎉 HEALTH CHECK PASSED ($total_ok/$total_tests - $percentage%)${NC}"
    echo -e "${GREEN}✅ Stack monitoring opérationnelle${NC}"
    exit_code=0
elif [ $percentage -ge 70 ]; then
    echo -e "${YELLOW}⚠️  HEALTH CHECK WARNING ($total_ok/$total_tests - $percentage%)${NC}"
    echo -e "${YELLOW}🔧 Quelques problèmes détectés${NC}"
    exit_code=1
else
    echo -e "${RED}❌ HEALTH CHECK FAILED ($total_ok/$total_tests - $percentage%)${NC}"
    echo -e "${RED}🆘 Stack monitoring dégradée${NC}"
    exit_code=2
fi

echo ""
echo "🔗 === LIENS UTILES ==="
echo "📊 Prometheus: http://localhost:9090"
echo "📈 Grafana: http://localhost:3000 (admin/admin123)"
echo "🚨 AlertManager: http://localhost:9093"
echo "📋 Documentation: /E5_monitoring/README_MONITORING.md"
echo "🐛 Debugging: /E5_monitoring/documentation_debugging_c21.md"

echo ""
echo "✅ Health check terminé à $(date)"

exit $exit_code
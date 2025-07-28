#!/bin/bash
# 🧪 Script de validation monitoring intégré
# Valide que tous les services de monitoring fonctionnent correctement

set -e

echo "🔍 VALIDATION MONITORING E5 - COACHING IA"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local url=$1
    local name=$2
    local expected_pattern=$3
    
    echo -n "📊 Checking $name... "
    
    if curl -s --max-time 5 "$url" > /dev/null 2>&1; then
        if [ -n "$expected_pattern" ]; then
            if curl -s "$url" | grep -q "$expected_pattern"; then
                echo -e "${GREEN}✅ OK${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠️  UP but missing pattern${NC}"
                return 1
            fi
        else
            echo -e "${GREEN}✅ UP${NC}"
            return 0
        fi
    else
        echo -e "${RED}❌ DOWN${NC}"
        return 1
    fi
}

# Check main application services
echo "🏠 APPLICATION SERVICES"
echo "----------------------"
check_service "http://localhost:8002/admin/" "Django Admin"
check_service "http://localhost:8000/docs" "FastAPI Docs"
check_service "http://localhost:8501/" "Streamlit UI"

echo ""

# Check monitoring services  
echo "📈 MONITORING SERVICES"
echo "---------------------"
check_service "http://localhost:9090/" "Prometheus"
check_service "http://localhost:3000/" "Grafana"
check_service "http://localhost:3100/ready" "Loki"
check_service "http://localhost:9093/" "AlertManager"
check_service "http://localhost:9100/metrics" "Node Exporter" "node_"

echo ""

# Check metrics endpoints
echo "🎯 METRICS ENDPOINTS"
echo "-------------------"
check_service "http://localhost:8002/metrics" "Django Metrics" "django_"
check_service "http://localhost:8000/metrics" "FastAPI Metrics" "fastapi_"

echo ""

# Check Prometheus targets
echo "🎯 PROMETHEUS TARGETS"
echo "--------------------"
if command -v jq > /dev/null 2>&1; then
    echo "Checking Prometheus targets..."
    targets=$(curl -s "http://localhost:9090/api/v1/targets" | jq -r '.data.activeTargets[] | "\(.labels.job): \(.health)"' 2>/dev/null)
    
    if [ -n "$targets" ]; then
        echo "$targets" | while IFS= read -r line; do
            job=$(echo "$line" | cut -d: -f1)
            health=$(echo "$line" | cut -d: -f2 | tr -d ' ')
            
            if [ "$health" = "up" ]; then
                echo -e "  ${GREEN}✅${NC} $job: $health"
            else
                echo -e "  ${RED}❌${NC} $job: $health"
            fi
        done
    else
        echo -e "${YELLOW}⚠️  No target data available${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  jq not available, skipping target details${NC}"
fi

echo ""

# Check Docker containers health
echo "🐳 DOCKER CONTAINERS"
echo "-------------------"
if command -v docker-compose > /dev/null 2>&1; then
    echo "Container status:"
    docker-compose -f docker-compose-full.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | tail -n +2 | while IFS= read -r line; do
        if echo "$line" | grep -q "Up"; then
            echo -e "${GREEN}✅${NC} $line"
        else
            echo -e "${RED}❌${NC} $line"
        fi
    done
else
    echo -e "${YELLOW}⚠️  docker-compose not available${NC}"
fi

echo ""

# Check available metrics
echo "📊 SAMPLE METRICS"
echo "----------------"
echo "Django metrics sample:"
curl -s "http://localhost:8002/metrics" 2>/dev/null | grep "django_" | head -3 || echo "  No Django metrics found"

echo ""
echo "FastAPI metrics sample:"
curl -s "http://localhost:8000/metrics" 2>/dev/null | grep "fastapi_" | head -3 || echo "  No FastAPI metrics found"

echo ""

# Check logs
echo "📝 LOG VERIFICATION"
echo "------------------"
echo "Recent Django logs:"
docker-compose -f docker-compose-full.yml logs --tail=3 django 2>/dev/null | grep -v "^$" || echo "  No Django logs"

echo ""
echo "Recent FastAPI logs:"
docker-compose -f docker-compose-full.yml logs --tail=3 fastapi 2>/dev/null | grep -v "^$" || echo "  No FastAPI logs"

echo ""

# Summary
echo "🎯 VALIDATION SUMMARY"
echo "======================"

# Count successful checks
total_checks=0
passed_checks=0

services=(
    "http://localhost:8002/admin/"
    "http://localhost:8000/docs" 
    "http://localhost:8501/"
    "http://localhost:9090/"
    "http://localhost:3000/"
    "http://localhost:3100/ready"
    "http://localhost:9093/"
    "http://localhost:9100/metrics"
    "http://localhost:8002/metrics"
    "http://localhost:8000/metrics"
)

for service in "${services[@]}"; do
    total_checks=$((total_checks + 1))
    if curl -s --max-time 3 "$service" > /dev/null 2>&1; then
        passed_checks=$((passed_checks + 1))
    fi
done

echo "Services: $passed_checks/$total_checks passed"

if [ $passed_checks -eq $total_checks ]; then
    echo -e "${GREEN}🎉 ALL SYSTEMS GO! Monitoring E5 is fully operational.${NC}"
    exit 0
elif [ $passed_checks -gt $((total_checks / 2)) ]; then
    echo -e "${YELLOW}⚠️  Partial success. Check failing services above.${NC}"
    exit 1
else
    echo -e "${RED}❌ Multiple failures detected. Review configuration.${NC}"
    exit 2
fi
#!/bin/bash
# Deployment Health Check Script
# Verifies all services are healthy and responding

GATEWAY_URL="${GATEWAY_URL:-https://gateway.railway.app}"
RAG_URL="${RAG_URL:-https://rag-service.railway.app}"
PLANNER_URL="${PLANNER_URL:-https://planner-service.railway.app}"
QUIZ_URL="${QUIZ_URL:-https://quiz-service.railway.app}"
FRONTEND_URL="${FRONTEND_URL:-https://your-app.vercel.app}"

echo "=== Deployment Health Check ==="
echo ""

all_healthy=true

check_service() {
    local name=$1
    local url=$2
    
    echo -n "Checking $name... "
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url/health" --max-time 10)
    
    if [ "$status_code" -eq 200 ]; then
        echo "✓ Healthy"
        return 0
    else
        echo "✗ Unhealthy (Status: $status_code)"
        return 1
    fi
}

check_frontend() {
    local url=$1
    
    echo -n "Checking Frontend... "
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 10)
    
    if [ "$status_code" -eq 200 ]; then
        echo "✓ Accessible"
        return 0
    else
        echo "✗ Inaccessible (Status: $status_code)"
        return 1
    fi
}

# Check all services
echo "Backend Services:"
check_service "Gateway" "$GATEWAY_URL" || all_healthy=false
check_service "RAG Service" "$RAG_URL" || all_healthy=false
check_service "Planner Service" "$PLANNER_URL" || all_healthy=false
check_service "Quiz Service" "$QUIZ_URL" || all_healthy=false

echo ""
echo "Frontend:"
check_frontend "$FRONTEND_URL" || all_healthy=false

echo ""
echo "=== Summary ==="

if [ "$all_healthy" = true ]; then
    echo "All services are healthy! ✓"
    exit 0
else
    echo "Some services are unhealthy! ✗"
    exit 1
fi

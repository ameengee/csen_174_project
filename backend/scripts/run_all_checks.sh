#!/usr/bin/env bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Backend - CI Checks${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker/compose/docker-compose.test.yml"

echo -e "${YELLOW}Step 1/5: Building Docker image...${NC}"
$COMPOSE build
echo -e "${GREEN}✓ Build complete${NC}"
echo ""

step=2
for check in format lint type unit; do
    echo -e "${YELLOW}Step ${step}/5: Running ${check}...${NC}"
    if $COMPOSE run --rm api /app/scripts/ci/${check}.sh; then
        echo -e "${GREEN}✓ ${check} passed${NC}"
    else
        echo -e "${RED}✗ ${check} failed${NC}"
        exit 1
    fi
    echo ""
    step=$((step + 1))
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All checks passed! ✓${NC}"
echo -e "${GREEN}========================================${NC}"

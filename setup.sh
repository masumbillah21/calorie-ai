#!/bin/bash
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "\n${GREEN}CalorieAI Setup${NC}"
echo "--------------------------------"

command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker not found${NC}"; exit 1; }
docker info >/dev/null 2>&1 || { echo -e "${RED}Docker not running${NC}"; exit 1; }
echo -e "${GREEN}Docker ready${NC}"

[ ! -f .env ] && cp .env.example .env && echo -e "${GREEN}.env created${NC}"

echo -e "\n${CYAN}Building and starting containers...${NC}\n"
docker compose -f docker-compose.yml up -d --build

echo -e "\n${GREEN}CalorieAI is live!${NC}"
echo -e "   ${CYAN}App  ->${NC} http://localhost"
echo -e "   ${CYAN}API  ->${NC} http://localhost/api"
echo -e "   ${CYAN}Docs ->${NC} http://localhost/api/docs\n"
echo -e "Install as PWA: open http://localhost on mobile -> Add to Home Screen\n"

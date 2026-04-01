@echo off
echo.
echo  CalorieAI - Setup
echo  --------------------------------
docker --version >nul 2>&1 || (echo ERROR: Docker not found && pause && exit /b 1)
docker compose version >nul 2>&1 || (echo ERROR: Docker Compose not found && pause && exit /b 1)
if not exist .env copy .env.example .env
echo Building and starting containers...
docker compose -f docker-compose.yml up -d --build
echo.
echo  CalorieAI is live!
echo    App  -^> http://localhost
echo    API  -^> http://localhost/api
echo    Docs -^> http://localhost/api/docs
echo.
pause

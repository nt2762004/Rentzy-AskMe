@echo off
echo [1/3] Starting Docker containers (PostgreSQL and Redis)...
docker compose up -d

echo.
echo [2/3] Waiting for Docker services to be ready...
timeout /t 3 /nobreak > nul

echo.
echo [3/3] Starting FastAPI Server...
echo Swagger UI: http://localhost:8000/docs
echo.

.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

pause

# Roti Boti Assistant API (FastAPI)

Endpoints:
- POST /hooks/reservation
- POST /hooks/notify

## Local run
pip install -r requirements.txt
uvicorn app:app --reload --port 8080

## Test
curl -X POST http://localhost:8080/hooks/reservation -H "Content-Type: application/json" -d '{"name":"Basit","party_size":4,"date":"2025-11-01","time":"19:30","phone":"4168267609"}'

curl -X POST http://localhost:8080/hooks/notify -H "Content-Type: application/json" -d '{"subject":"Test","message":"Hello"}'

## Render start command
uvicorn app:app --host 0.0.0.0 --port 10000

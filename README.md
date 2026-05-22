# SovereignStack Reference Pack (OASA 2026.1)

Runnable reference implementation for the OASA SovereignStack standard.

## Quickstart
```bash
cp .env.example .env
docker-compose up --build
```

## Validate Compliance
```bash
python tools/oasa_validator.py validate sovereign-stack.yaml
```

## Test OpenAI-Compatible Gateway
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sovereign-llama3",
    "messages": [{"role":"user","content":"Hello from OASA"}],
    "use_rag": false
  }'
```

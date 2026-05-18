curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "model": "sovereign-llama3-70b-turboquant",
    "messages": [{"role": "user", "content": "Analyze confidential audit report."}],
    "oasa_compliance_lock": true
  }'

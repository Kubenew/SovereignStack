curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sovereign-llama3",
    "messages": [{"role":"user","content":"Analyze confidential audit report."}],
    "oasa_compliance_lock": true,
    "use_rag": true
  }'

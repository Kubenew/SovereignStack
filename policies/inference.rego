package oasa.inference

# Default deny
default allow = false

# Allow if there are no security violations
allow {
    count(violations) == 0
}

# Rule 1: Block Social Security Numbers (SSN)
violations[msg] {
    re_match(`\d{3}-\d{2}-\d{4}`, input.prompt)
    msg := "PII-Block-SSN: Prompt contains sensitive Social Security Number format"
}

# Rule 2: Block Credit Card numbers
violations[msg] {
    re_match(`\d{4}-\d{4}-\d{4}-\d{4}`, input.prompt)
    msg := "PII-Block-CreditCard: Prompt contains credit card number format"
}

# Rule 3: Detect and block basic prompt injection attempts
violations[msg] {
    lower_prompt := lower(input.prompt)
    # Match phrases like "ignore previous instructions", "bypass system prompts", etc.
    re_match(`(ignore|bypass|override|forget)\s+(previous|system|prior|initial)\s+(instruction|rule|prompt|setting)`, lower_prompt)
    msg := "Safety-Prompt-Injection: Prompt contains system instructions override attempts"
}

# Rule 4: Role-Based Model Access Control
violations[msg] {
    # If using a high-parameter production model, check if user has the inference:write role
    input.model == "sovereign-llama3"
    not user_has_role("inference:write")
    msg := "RBAC-Model-Access: Requesting sovereign-llama3 requires 'inference:write' role"
}

# Helper rule to verify user claims from JWT
user_has_role(role) {
    input.auth.roles[_] == role
}

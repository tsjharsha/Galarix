class GalarixError:
    # Authentication
    AUTH_MISSING_KEY = {"code": "E1001", "message": "API key is required."}
    AUTH_INVALID_KEY = {"code": "E1002", "message": "Invalid API key."}
    AUTH_EXPIRED_KEY = {"code": "E1003", "message": "API key has expired."}
    AUTH_RATE_LIMITED = {"code": "E1004", "message": "Rate limit exceeded."}
    
    # Firewall
    FW_EMPTY_PROMPT = {"code": "E2001", "message": "Prompt cannot be empty."}
    FW_PROMPT_TOO_LONG = {"code": "E2002", "message": "Prompt exceeds 1000 characters."}
    FW_POISON_DETECTED = {"code": "E2003", "message": "Restricted mathematical keyword detected."}
    FW_INJECTION_DETECTED = {"code": "E2004", "message": "Potentially unsafe input detected."}
    
    # Pipeline
    PIPE_NO_ENTITY = {"code": "E3001", "message": "Could not resolve a financial entity."}
    PIPE_GENERATION_FAILED = {"code": "E3002", "message": "Data generation failed."}
    PIPE_TIMEOUT = {"code": "E3003", "message": "Generation timed out."}
    
    # Export
    EXPORT_FAILED = {"code": "E4001", "message": "Failed to export dataset."}

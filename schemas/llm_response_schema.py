LLM_RESPONSE_JSON_SCHEMA = {
    "name": "portfolio_agent_response",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "message": {
                "type": "string"
            },
            "parsed_resume": {
                "anyOf": [
                    {"type": "null"},
                    {
                        "type": "object"
                    }
                ]
            }
        },
        "required": ["message", "parsed_resume"]
    }
}
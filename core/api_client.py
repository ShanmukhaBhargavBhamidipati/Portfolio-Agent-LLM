import os

from core.transport_models import StructuredLLMTransport


class OpenAIChatClient:
    def __init__(self, client, model: str | None = None, timeout: int | None = None):
        self.client = client
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")
        self.timeout = timeout or int(os.getenv("OPENAI_TIMEOUT_SECONDS", "120"))

    def generate_structured_response(self, history: list[dict]):
        latest_user_message = next(
            (m["content"] for m in reversed(history) if m.get("role") == "user"),
            "",
        )

        try:
            completion = self.client.with_options(timeout=self.timeout).chat.completions.parse(
                model=self.model,
                messages=history,
                response_format=StructuredLLMTransport,
                max_completion_tokens=15000,
            )

            msg = completion.choices[0].message

            if getattr(msg, "refusal", None):
                return {
                    "error": f"Model refusal: {msg.refusal}",
                    "user_message": latest_user_message,
                }

            if msg.parsed is None:
                return {
                    "error": "Parsed response was empty",
                    "user_message": latest_user_message,
                }

            parsed = msg.parsed.model_dump(exclude_none=False)
            return {
                "user_message": latest_user_message,
                "message": parsed.get("message", ""),
                "parsed_resume": parsed.get("parsed_resume"),
            }

        except Exception as e:
            return {
                "error": str(e),
                "user_message": latest_user_message,
            }

import json

class ConversationHistory:
    def __init__(self):
        self.messages = []

    def set_developer_prompt(self, prompt: str):
        self.messages = [{"role": "developer", "content": prompt}]

    def append_user(self, content: str):
        self.messages.append({"role": "user", "content": content})

    def append_assistant_json(self, message: str, parsed_resume=None):
        self.messages.append({
            "role": "assistant",
            "content": json.dumps(
                {
                    "message": message,
                    "parsed_resume": parsed_resume,
                },
                ensure_ascii=False,
            ),
        })

    def snapshot_with_user(self, content: str):
        return self.messages + [{"role": "user", "content": content}]
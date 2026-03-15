import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from config import load_config
from core.chat_service import ChatService
from core.history import ConversationHistory
from core.logging_config import setup_logging


BASE_DIR = Path(__file__).resolve().parent


class ChatSession:
    def __init__(self):
        self.service = self._build_service()
        self.messages = []
        self.completed = False

    @staticmethod
    def _build_service():
        client = load_config()
        history = ConversationHistory()
        return ChatService(
            client=client,
            history=history,
            system_prompt_path="prompts/system_prompt.txt",
            resume_schema_path="schemas/resume_schema.json",
            html_retry_prompt_path="prompts/html_retry_prompt.txt",
            revision_prompt_path="prompts/portfolio_revision_prompt.txt",
        )

    def reset(self):
        self._delete_parsed_resume()
        self.service = self._build_service()
        self.messages = []
        self.completed = False

    @staticmethod
    def _delete_parsed_resume():
        resume_path = BASE_DIR / "parsed_resume.json"
        if resume_path.exists():
            resume_path.unlink()

    def _input_mode(self):
        if self.completed:
            return "complete"
        if self.service.state.get("awaiting_rating"):
            return "rating"
        if self.service.state.get("awaiting_revision_feedback"):
            return "revision"
        return "chat"

    def _placeholder(self):
        mode = self._input_mode()
        if mode == "rating":
            return "Rate the portfolio from 1 to 10"
        if mode == "revision":
            return "Describe what to improve and optionally add inspiration URLs"
        if mode == "complete":
            return "Reset the session to start again"
        return "Describe your portfolio, paste your resume, or ask for changes"

    def _current_html(self):
        html_path = self.service.state.get("current_html_path")
        if not html_path:
            return None

        resolved = Path(html_path)
        if not resolved.exists():
            return None

        return resolved.read_text(encoding="utf-8")

    def snapshot(self):
        return {
            "messages": self.messages,
            "input_mode": self._input_mode(),
            "placeholder": self._placeholder(),
            "completed": self.completed,
            "artifacts": {
                "html_path": self.service.state.get("current_html_path"),
                "html_content": self._current_html(),
                "url_summaries": self.service.state.get("latest_url_summaries") or [],
                "awaiting_rating": self.service.state.get("awaiting_rating", False),
                "awaiting_revision_feedback": self.service.state.get(
                    "awaiting_revision_feedback", False
                ),
            },
        }

    @staticmethod
    def _parsed_resume_payload(parsed_resume):
        if parsed_resume is None:
            return None
        if hasattr(parsed_resume, "model_dump"):
            return parsed_resume.model_dump(exclude_none=True)
        if hasattr(parsed_resume, "dict"):
            return parsed_resume.dict(exclude_none=True)
        return parsed_resume

    def submit(self, user_input: str):
        cleaned = (user_input or "").strip()
        if not cleaned:
            return False, "Enter a valid message."

        if self.completed:
            return False, "This session is complete. Reset it to start a new one."

        self.messages.append({"role": "user", "content": cleaned})

        outcome = self.service.handle_turn(cleaned)
        if not outcome.ok:
            self.messages.append({"role": "system", "content": str(outcome.response), "error": True})
            return False, str(outcome.response)

        result = outcome.response
        payload = {
            "role": "assistant",
            "content": result.message,
            "is_html": self.service.is_html(result.message),
            "parsed_resume": self._parsed_resume_payload(result.parsed_resume),
        }
        self.messages.append(payload)

        if outcome.should_exit:
            self._delete_parsed_resume()
            self.completed = True

        return True, payload


def create_app():
    setup_logging()

    app = Flask(__name__, template_folder="templates", static_folder="static")
    session = ChatSession()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/state")
    def get_state():
        return jsonify(session.snapshot())

    @app.post("/api/chat")
    def chat():
        data = request.get_json(silent=True) or {}
        ok, response = session.submit(data.get("message", ""))
        return jsonify({"ok": ok, "response": response, "state": session.snapshot()})

    @app.post("/api/reset")
    def reset():
        session.reset()
        return jsonify(session.snapshot())

    @app.get("/api/history")
    def history():
        return jsonify(session.snapshot()["messages"])

    @app.get("/api/parsed-resume")
    def parsed_resume():
        resume_path = BASE_DIR / "parsed_resume.json"
        if not resume_path.exists():
            return jsonify({"exists": False, "content": None})

        return jsonify(
            {
                "exists": True,
                "content": json.loads(resume_path.read_text(encoding="utf-8")),
                "path": str(resume_path),
            }
        )

    return app

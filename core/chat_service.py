import logging
from pathlib import Path

from load_files import load_final_prompt, load_prompt
from core.api_client import OpenAIChatClient
from core.models import TurnResult, TurnOutcome
from core.storage import save_html, save_json
from core.validators import (
    validate_against_json_schema,
    validate_response,
    validate_response_html,
)
from core.dom_analyzer import analyze_html
from core.prompt_builders import build_inspiration_summary_block
from core.url_utils import extract_urls

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        client,
        history,
        system_prompt_path,
        resume_schema_path,
        html_retry_prompt_path,
        revision_prompt_path,
    ):
        self.history = history
        self.resume_schema_path = resume_schema_path
        self.html_retry_prompt_path = html_retry_prompt_path
        self.revision_prompt_path = revision_prompt_path

        developer_prompt = load_final_prompt(system_prompt_path, resume_schema_path)
        self.history.set_developer_prompt(developer_prompt)

        self.api = OpenAIChatClient(client=client)

        self.state = {
            "last_valid_html": None,
            "current_html_path": None,
            "awaiting_rating": False,
            "awaiting_revision_feedback": False,
            "revision_count": 0,
            "max_revision_count": 5,
            "latest_url_summaries": [],
        }

    @staticmethod
    def summarize_analysis_text(text: str, max_len: int = 500) -> str:
        if not text:
            return "No summary available."

        cleaned = " ".join(str(text).split())
        if len(cleaned) <= max_len:
            return cleaned
        return cleaned[: max_len - 3].rstrip() + "..."

    def build_inspiration_block(self, user_feedback: str, max_urls: int = 3) -> str:
        urls = extract_urls(user_feedback)
        self.state["latest_url_summaries"] = []

        if not urls:
            return ""

        summaries = []
        for url in urls[:max_urls]:
            try:
                logger.info("Analyzing inspiration URL: %s", url)
                analysis = analyze_html(url)
                summaries.append(analysis)
                self.state["latest_url_summaries"].append(
                    {
                        "url": url,
                        "summary": self.summarize_analysis_text(analysis),
                    }
                )
            except Exception as e:
                logger.warning("Failed to analyze inspiration URL %s | error=%s", url, e)
                self.state["latest_url_summaries"].append(
                    {
                        "url": url,
                        "summary": f"Failed to analyze this URL: {e}",
                    }
                )

        usable_summaries = [s for s in summaries if s]
        if not usable_summaries:
            return ""

        return build_inspiration_summary_block(usable_summaries)

    @staticmethod
    def is_html(text):
        if not isinstance(text, str):
            return False

        text = text.strip().lower()
        return text.startswith("<!doctype html") or text.startswith("<html")

    def reset_html_state(self):
        self.state["last_valid_html"] = None
        self.state["current_html_path"] = None
        self.state["awaiting_rating"] = False
        self.state["awaiting_revision_feedback"] = False
        self.state["revision_count"] = 0
        self.state["latest_url_summaries"] = []

    def activate_html_rating_state(self, html):
        output_path = save_html(html, "portfolio.html")
        file_exists = Path(output_path).exists()

        logger.info("Valid HTML saved to %s | exists=%s", output_path, file_exists)

        self.state["last_valid_html"] = html
        self.state["current_html_path"] = output_path
        self.state["awaiting_rating"] = True
        self.state["awaiting_revision_feedback"] = False
        self.state["revision_count"] = 0

        return output_path

    def process_response(self, user_input):
        temp_history = self.history.snapshot_with_user(user_input)
        raw_response = self.api.generate_structured_response(temp_history)

        if "error" in raw_response:
            return False, f"API call failed: {raw_response['error']}"

        is_valid, llm_obj_or_err = validate_response(raw_response)
        if not is_valid:
            return False, f"LLM response validation failed: {llm_obj_or_err}"

        return True, llm_obj_or_err

    def handle_parsed_resume(self, llm_response):
        if llm_response.parsed_resume is None:
            return True, "No parsed resume present."

        parsed_resume = llm_response.parsed_resume
        parsed_resume_dict = (
            parsed_resume.model_dump(exclude_none=True)
            if hasattr(parsed_resume, "model_dump")
            else parsed_resume.dict(exclude_none=True)
        )

        is_valid, err = validate_against_json_schema(parsed_resume_dict, self.resume_schema_path)
        if not is_valid:
            return False, f"JSON schema validation failed: {err}"

        output_path = save_json(parsed_resume_dict, "parsed_resume.json")
        logger.info("Parsed resume saved to %s", output_path)
        return True, output_path

    def handle_generated_html(self, response):
        html = response.message
        if not self.is_html(html):
            return True, "No HTML present."

        is_valid, err = validate_response_html(html)
        if not is_valid:
            return False, f"HTML validation failed: {err}"

        return True, "HTML is valid."

    def append_turn(self, user_input, result):
        parsed_resume = None
        if result.parsed_resume is not None:
            parsed_resume = (
                result.parsed_resume.model_dump(exclude_none=True)
                if hasattr(result.parsed_resume, "model_dump")
                else result.parsed_resume.dict(exclude_none=True)
            )

        self.history.append_user(user_input)
        self.history.append_assistant_json(
            message=result.message,
            parsed_resume=parsed_resume,
        )

    def retry_generate_valid_html(self, failed_response, initial_error=None, max_retries=3):
        last_html = failed_response.message
        last_error = initial_error or "Initial HTML failed validation."

        retry_system_prompt = load_prompt(self.html_retry_prompt_path)
        retry_history = [{"role": "developer", "content": retry_system_prompt}]

        for attempt in range(1, max_retries + 1):
            retry_user_prompt = f"""
The previously generated HTML is invalid.

Validation error:
{last_error}

Previously generated HTML:
{last_html}

Repair the HTML and return only the required JSON object.
"""
            retry_history.append({"role": "user", "content": retry_user_prompt})

            response = self.api.generate_structured_response(retry_history)
            if "error" in response:
                last_error = f"API call failed during retry attempt {attempt}: {response['error']}"
                logger.warning(last_error)
                continue

            is_valid, llm_obj_or_err = validate_response(response)
            if not is_valid:
                last_error = f"Retry response validation failed on attempt {attempt}: {llm_obj_or_err}"
                logger.warning(last_error)
                continue

            corrected_response = llm_obj_or_err
            html_ok, html_msg = self.handle_generated_html(corrected_response)
            if html_ok and self.is_html(corrected_response.message):
                logger.info("HTML repair succeeded on attempt %d", attempt)
                return True, corrected_response

            last_html = corrected_response.message
            last_error = html_msg

        return False, f"HTML remained invalid after {max_retries} retries. Last error: {last_error}"

    def generate_revised_html(self, current_html, user_feedback, max_iterations=5):
        revision_prompt = load_prompt(self.revision_prompt_path)
        revision_history = [{"role": "developer", "content": revision_prompt}]

        last_html = current_html
        last_error = None
        inspiration_block = self.build_inspiration_block(user_feedback)

        for attempt in range(1, max_iterations + 1):
            extra_context = f"\n\nInspiration analysis:\n{inspiration_block}" if inspiration_block else ""
            revision_user_prompt = f"""
Current valid HTML:
{last_html}

User feedback:
{user_feedback}{extra_context}

Previous validation error:
{last_error if last_error else 'None'}

Revise the portfolio and return only the required JSON object.
"""
            revision_history.append({"role": "user", "content": revision_user_prompt})

            response = self.api.generate_structured_response(revision_history)
            if "error" in response:
                last_error = f"API call failed on revision attempt {attempt}: {response['error']}"
                logger.warning(last_error)
                continue

            is_valid, llm_obj_or_err = validate_response(response)
            if not is_valid:
                last_error = f"Revision response validation failed on attempt {attempt}: {llm_obj_or_err}"
                logger.warning(last_error)
                continue

            revised_response = llm_obj_or_err
            html_ok, html_msg = self.handle_generated_html(revised_response)
            if html_ok and self.is_html(revised_response.message):
                logger.info("Revision produced valid HTML on attempt %d", attempt)
                return True, revised_response

            retry_ok, retry_result = self.retry_generate_valid_html(
                revised_response,
                initial_error=html_msg,
                max_retries=3,
            )
            if retry_ok:
                return True, retry_result

            last_html = revised_response.message
            last_error = retry_result if isinstance(retry_result, str) else html_msg

        return False, (
            f"Failed to generate a valid revised HTML after {max_iterations} attempts. "
            f"Last error: {last_error}"
        )

    def handle_turn(self, user_input):
        if self.state.get("awaiting_rating") and self.state.get("last_valid_html"):
            try:
                score = int(user_input.strip())
            except ValueError:
                return TurnOutcome(False, "Please enter a valid integer rating from 1 to 10.", False)

            if score < 1 or score > 10:
                return TurnOutcome(False, "Rating must be between 1 and 10.", False)

            if score > 7:
                output_path = self.state.get("current_html_path") or save_html(
                    self.state["last_valid_html"], "portfolio.html"
                )
                logger.info("Accepted HTML confirmed at %s", output_path)
                return TurnOutcome(
                    True,
                    TurnResult(
                        f"Portfolio accepted. The latest HTML is saved at {output_path}. Exiting application."
                    ),
                    True,
                )

            self.state["awaiting_rating"] = False
            self.state["awaiting_revision_feedback"] = True
            return TurnOutcome(
                True,
                TurnResult(
                    "Got it — rating "
                    f"{score}/10. Please describe what you want improved. "
                    "You can also add 1-3 portfolio URLs for inspiration. "
                    "Please share only public inspiration URLs that load as standard HTML/CSS/JS websites."
                ),
                False,
            )

        if self.state.get("awaiting_revision_feedback") and self.state.get("last_valid_html"):
            if self.state["revision_count"] >= self.state["max_revision_count"]:
                output_path = save_html(self.state["last_valid_html"], "portfolio.html")
                logger.info("Max revisions reached. Last valid HTML saved to %s", output_path)
                return TurnOutcome(
                    True,
                    TurnResult(
                        f"Maximum revision attempts reached. Last valid HTML saved to {output_path}. Exiting application."
                    ),
                    True,
                )

            revise_ok, revise_result = self.generate_revised_html(
                self.state["last_valid_html"],
                user_input,
            )
            if not revise_ok:
                return TurnOutcome(False, revise_result, False)

            output_path = save_html(revise_result.message, "portfolio.html")
            logger.info("Revised valid HTML saved to %s", output_path)

            self.state["last_valid_html"] = revise_result.message
            self.state["current_html_path"] = output_path
            self.state["awaiting_revision_feedback"] = False
            self.state["awaiting_rating"] = True
            self.state["revision_count"] += 1

            self.append_turn(user_input, revise_result)
            return TurnOutcome(True, revise_result, False)

        ok, result = self.process_response(user_input)
        if not ok:
            return TurnOutcome(False, result, False)

        if result.parsed_resume is not None:
            resume_ok, resume_msg = self.handle_parsed_resume(result)
            if not resume_ok:
                return TurnOutcome(False, resume_msg, False)

            self.reset_html_state()
            self.append_turn(user_input, result)
            return TurnOutcome(True, result, False)

        html_ok, html_msg = self.handle_generated_html(result)
        if html_ok:
            if self.is_html(result.message):
                self.activate_html_rating_state(result.message)
            else:
                self.reset_html_state()

            self.append_turn(user_input, result)
            return TurnOutcome(True, result, False)

        if self.is_html(result.message):
            retry_ok, retry_result = self.retry_generate_valid_html(
                result,
                initial_error=html_msg,
                max_retries=3,
            )
            if retry_ok:
                self.activate_html_rating_state(retry_result.message)
                self.append_turn(user_input, retry_result)
                return TurnOutcome(True, retry_result, False)

            return TurnOutcome(False, retry_result, False)

        return TurnOutcome(False, html_msg, False)
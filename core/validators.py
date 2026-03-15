import json
import os
import re
import shutil
import subprocess
import tempfile

import tinycss2
from bs4 import BeautifulSoup
from jsonschema import validate
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError

from pydantic_checker import LLMResponse, Resume


def validate_response(response):
    try:
        message = response["message"]
        parsed_resume_raw = response.get("parsed_resume")

        if isinstance(parsed_resume_raw, Resume):
            parsed_resume = parsed_resume_raw
        elif parsed_resume_raw is not None:
            parsed_resume = Resume(**parsed_resume_raw)
        else:
            parsed_resume = None

        llm_resp_obj = LLMResponse(
            message=message,
            parsed_resume=parsed_resume,
        )
        return True, llm_resp_obj

    except (KeyError, TypeError, ValidationError) as e:
        return False, str(e)


def validate_against_json_schema(data, schema_path):
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    try:
        validate(instance=data, schema=schema)
        return True, None
    except JsonSchemaValidationError as e:
        return False, e.message


def extract_inline_css(html: str):
    return re.findall(
        r"<style\b[^>]*>(.*?)</style>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


def extract_inline_js(html: str):
    return re.findall(
        r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )


def validate_html_structure(html: str):
    if not html or not html.strip():
        return False, "HTML is empty."

    stripped = html.strip()
    lowered = stripped.lower()

    if not lowered.startswith("<!doctype html"):
        return False, "Missing or invalid <!DOCTYPE html>."

    try:
        soup = BeautifulSoup(stripped, "html.parser")
    except Exception as e:
        return False, f"HTML parsing failed: {e}"

    if soup.find("html") is None:
        return False, "Missing <html> tag."
    if soup.find("head") is None:
        return False, "Missing <head> tag."
    if soup.find("body") is None:
        return False, "Missing <body> tag."
    if soup.find("title") is None:
        return False, "Missing <title> tag."

    body = soup.find("body")
    if body and not body.get_text(strip=True) and not body.find_all(True):
        return False, "Body is empty."

    return True, None


def validate_inline_css(html: str):
    css_blocks = extract_inline_css(html)

    for index, css in enumerate(css_blocks, start=1):
        try:
            parsed = tinycss2.parse_stylesheet(
                css,
                skip_whitespace=True,
                skip_comments=True,
            )
        except Exception as e:
            return False, f"CSS block {index} could not be parsed: {e}"

        for rule in parsed:
            if getattr(rule, "type", None) == "error":
                return False, f"CSS block {index} syntax error: {rule.message}"

    return True, None


def validate_inline_js(html: str):
    js_blocks = extract_inline_js(html)
    if not js_blocks:
        return True, None

    node_path = shutil.which("node")
    if node_path is None:
        return True, None

    for index, js in enumerate(js_blocks, start=1):
        js = js.strip()
        if not js:
            continue

        js_file_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".js",
                delete=False,
                encoding="utf-8",
            ) as js_file:
                js_file.write(js)
                js_file_path = js_file.name

            result = subprocess.run(
                [node_path, "--check", js_file_path],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                err = result.stderr.strip() or result.stdout.strip() or "Unknown JS syntax error"
                return False, f"JS block {index} syntax error: {err}"

        except Exception as e:
            return False, f"JS block {index} validation failed: {e}"
        finally:
            if js_file_path and os.path.exists(js_file_path):
                os.remove(js_file_path)

    return True, None


def contains_unresolved_template_placeholders(html: str) -> bool:
    patterns = [
        r"\{\{\s*[a-zA-Z_][a-zA-Z0-9_\.\-\s\|:\(\)]*\s*\}\}",
        r"\{%[\s\S]*?%\}",
        r"<%[=\-]?[\s\S]*?%>",
    ]
    return any(re.search(pattern, html) for pattern in patterns)


def validate_for_browser_runtime(html: str):
    lowered = html.lower()

    if contains_unresolved_template_placeholders(html):
        return False, "Template placeholders detected."

    if re.search(r"<script\b[^>]*\btype\s*=\s*['\"]module['\"]", lowered):
        return False, "Module scripts are not allowed for this standalone validation."

    if re.search(r"<link\b[^>]*rel\s*=\s*['\"]stylesheet['\"]", lowered):
        return False, "External stylesheet link found. Expected inline CSS only."

    if re.search(r"<script\b[^>]*\bsrc\s*=", lowered):
        return False, "External script src found. Expected inline JS only."

    return True, None


def validate_response_html(html):
    html_ok, html_err = validate_html_structure(html)
    if not html_ok:
        return False, html_err

    css_ok, css_err = validate_inline_css(html)
    if not css_ok:
        return False, css_err

    js_ok, js_err = validate_inline_js(html)
    if not js_ok:
        return False, js_err

    runtime_ok, runtime_err = validate_for_browser_runtime(html)
    if not runtime_ok:
        return False, runtime_err

    return True, None
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def save_json(data, output_path: str):
    full_path = BASE_DIR / output_path
    full_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return str(full_path)


def save_html(html: str, output_path: str = "portfolio.html"):
    full_path = BASE_DIR / output_path
    full_path.write_text(html, encoding="utf-8")
    return str(full_path)

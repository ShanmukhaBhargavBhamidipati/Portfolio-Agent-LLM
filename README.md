# Portfolio Agent

Portfolio Agent is a local Flask app that turns resume text and portfolio instructions into a standalone personal website. It parses resume content into structured JSON, generates a complete HTML portfolio, validates the output, saves the latest artifacts locally, and lets you review and revise the result in a browser UI.

## What this project does

The app supports an end-to-end portfolio generation loop:

1. You paste resume text or describe the portfolio you want.
2. The model returns a structured response with a user-facing message and optional `parsed_resume` data.
3. Resume data is validated against `schemas/resume_schema.json` and saved as `parsed_resume.json`.
4. Generated HTML is validated for structure, inline CSS, inline JavaScript, and standalone-browser compatibility.
5. Invalid HTML can go through an automatic repair loop.
6. Valid HTML is saved as `portfolio.html` and shown in the web UI.
7. You rate the output from 1 to 10.
8. If the rating is 7 or below, you can request revisions and optionally include public inspiration URLs.
9. The app analyzes those URLs and uses them to guide the next iteration.

## Features

- Local browser-based workflow
- Resume parsing into structured JSON
- JSON schema validation for parsed resume output
- Standalone HTML portfolio generation
- Automatic HTML repair attempts
- Rating and revision loop
- Public inspiration URL analysis
- Local artifact saving for `parsed_resume.json` and `portfolio.html`

## Tech stack

- Python
- Flask
- OpenAI Python SDK
- Pydantic
- JSON Schema
- BeautifulSoup
- tinycss2
- Playwright

## Project structure

```text
portfolio-agent-github-ready/
├── app.py
├── web_app.py
├── config.py
├── load_files.py
├── pydantic_checker.py
├── terminal_chat.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── core/
│   ├── api_client.py
│   ├── chat_service.py
│   ├── dom_analyzer.py
│   ├── history.py
│   ├── inspiration.py
│   ├── logging_config.py
│   ├── models.py
│   ├── prompt_builders.py
│   ├── response_models.py
│   ├── storage.py
│   ├── transport_models.py
│   ├── url_utils.py
│   └── validators.py
├── prompts/
│   ├── system_prompt.txt
│   ├── html_retry_prompt.txt
│   └── portfolio_revision_prompt.txt
├── schemas/
│   ├── llm_response_schema.py
│   └── resume_schema.json
├── static/
│   ├── app.css
│   └── app.js
└── templates/
    └── index.html
```

Generated during use:

```text
parsed_resume.json
portfolio.html
```

## Requirements

Install these first:

- Python 3.11+
- pip
- Playwright browser binaries
- Node.js (optional but recommended for inline JavaScript validation)

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd portfolio-agent-github-ready
```

### 2. Create and activate a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### Windows Command Prompt

```bat
python -m venv .venv
.venv\Scripts\activate
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Chromium

```bash
python -m playwright install chromium
```

### 5. Create your local `.env`

```bash
cp .env.example .env
```

Then open `.env` and set your real API key.

Example:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5-mini
OPENAI_TIMEOUT_SECONDS=120
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

## Running the app

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## How to use it

### Generate a portfolio

Paste resume text or describe the website you want.

Example:

```text
Create a modern software engineer portfolio with a dark theme, strong project cards, and a contact section. Here is my resume:
[paste resume here]
```

### Review the parsed resume

If the model returns structured resume data, the app validates it, saves it to `parsed_resume.json`, and shows it in the Parsed Resume panel.

### Review generated HTML

If the model returns valid HTML, the app saves it to `portfolio.html`, previews it in the UI, and switches to rating mode.

### Rate the result

Send a number from `1` to `10`.

- `8` to `10`: accept the current portfolio and end the session
- `1` to `7`: request changes and continue the revision loop

### Revise the portfolio

Describe what should change.

Example:

```text
Make the hero section cleaner, reduce the amount of text above the fold, and use a more premium dark palette.
```

You can also include up to 3 public inspiration URLs.

Example:

```text
Make it feel more editorial and minimal. Use these as inspiration:
https://example.com
https://example.org
```

## API routes

- `GET /` - main UI
- `GET /api/state` - current session snapshot
- `POST /api/chat` - submit a message
- `POST /api/reset` - reset the session
- `GET /api/history` - conversation history
- `GET /api/parsed-resume` - saved parsed resume content

## Environment variables

- `OPENAI_API_KEY`: required
- `OPENAI_MODEL`: optional, defaults to `gpt-5-mini`
- `OPENAI_TIMEOUT_SECONDS`: optional, defaults to `120`
- `FLASK_HOST`: optional, defaults to `127.0.0.1`
- `FLASK_PORT`: optional, defaults to `5000`

## Notes and limitations

- The app keeps one in-memory session per running server instance.
- Generated HTML must be standalone. External JS and external CSS links are rejected by validation.
- Inspiration analysis works best with public pages that render as regular HTML/CSS/JS.
- Node.js is optional, but without it the inline JavaScript syntax check is skipped.

## GitHub publishing checklist

Before pushing this repo:

- Keep your real `.env` file local only.
- Never commit API keys or generated secrets.
- Do not commit generated files like `parsed_resume.json` or `portfolio.html`.
- Do not commit local caches, virtual environments, or internal `.git` folders copied from another machine.
- Rotate any API key that was ever stored inside this folder, inside a zip, or in screenshots/messages.

## Common issues

### `OPENAI_API_KEY is missing in your .env file`

Create `.env` from `.env.example` and add your real key.

### Playwright errors during inspiration analysis

Install Chromium with:

```bash
python -m playwright install chromium
```

### JavaScript validation is not running

Install Node.js so the app can use `node --check` for inline script validation.

## Suggested future improvements

- Add automated tests for validators and chat state transitions
- Support multiple saved portfolio versions
- Add downloadable exports from the UI
- Persist sessions instead of keeping them only in memory
- Add Docker support

## License

No license file is included in this package. Add your preferred license before publishing if you want others to reuse the code.

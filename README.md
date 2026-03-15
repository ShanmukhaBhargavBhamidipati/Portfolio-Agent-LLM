# Portfolio Agent

Portfolio Agent is a local Flask app that helps you turn raw resume text and portfolio requirements into a standalone personal website.

It uses the OpenAI API to:
- parse resume content into structured JSON
- generate a complete portfolio page as standalone HTML
- validate the generated HTML/CSS/JS before saving it
- let you review, rate, and revise the portfolio in a browser UI
- optionally analyze public inspiration websites and use them to guide revisions

Everything runs locally on your machine except the model calls.

---

## What it does

The app supports a full portfolio-generation loop:

1. You paste resume text or describe the portfolio you want.
2. The model returns a structured response containing:
   - a `message`
   - an optional `parsed_resume` object
3. If resume data is returned, the app validates it against `schemas/resume_schema.json` and saves it as `parsed_resume.json`.
4. If HTML is returned, the app validates:
   - HTML structure
   - inline CSS syntax
   - inline JavaScript syntax
   - standalone browser compatibility rules
5. If HTML validation fails, the app attempts automatic repair.
6. If valid HTML is produced, it is saved as `portfolio.html` and previewed in the web app.
7. You rate the result from 1 to 10.
8. If the rating is 7 or below, you can provide revision feedback and optional inspiration URLs.
9. The app revises the portfolio and repeats the review loop.

---

## Features

- Local browser-based chat workflow
- Resume parsing into structured JSON
- JSON schema validation for parsed resume output
- Standalone portfolio HTML generation
- Automatic HTML repair attempts when validation fails
- Revision loop driven by user ratings and feedback
- Inspiration URL analysis for design guidance
- Live browser preview of the latest generated portfolio
- Saved local artifacts for easy inspection

---

## Tech stack

- Python
- Flask
- OpenAI Python SDK
- Pydantic
- JSON Schema
- BeautifulSoup
- tinycss2
- Playwright

---

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

---

## How the app works

### 1. Web app entry point

`app.py` starts the Flask server by calling `create_app()` from `web_app.py`.

### 2. Session management

`web_app.py` manages a single in-memory `ChatSession` with routes for:
- `/` for the UI
- `/api/chat` for submitting messages
- `/api/state` for current app state
- `/api/reset` for resetting the session
- `/api/history` for conversation history
- `/api/parsed-resume` for reading saved resume JSON

### 3. Core chat logic

`core/chat_service.py` handles the application workflow:
- sending user input to the model
- validating structured responses
- saving parsed resume data
- validating generated HTML
- retrying invalid HTML generations
- managing rating and revision state
- analyzing inspiration URLs during revisions

### 4. Validation

`core/validators.py` checks generated output before it is accepted:
- required HTML tags like `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>`, and `<title>`
- inline CSS syntax with `tinycss2`
- inline JS syntax with Node.js when available
- browser-runtime rules such as no external script or stylesheet dependencies

### 5. Inspiration analysis

`core/dom_analyzer.py` analyzes public inspiration sites and summarizes their structure and visual characteristics. Those summaries are injected into the revision prompt.

---

## GitHub safety checklist

Before pushing this project publicly or privately:

- keep your real `.env` file local only and never commit it
- use `.env.example` as the template for other developers
- do not commit generated files like `parsed_resume.json` or `portfolio.html`
- do not commit `.git/`, `__pycache__/`, virtual environments, logs, or local databases
- rotate any API key that was ever stored in the repository folder, a zip, a screenshot, or chat history

Recommended first-time setup after cloning:

```bash
cp .env.example .env
# then add your real OPENAI_API_KEY locally
```

If a secret was exposed previously, remove it from the repo, rotate it at the provider, and avoid reusing it.

---


## Requirements

Before running the app, install:

- Python 3.11 or newer
- pip
- Playwright browser binaries
- Node.js (optional, but recommended)

### Why Node.js is optional

The app can validate inline JavaScript syntax using `node --check`. If Node.js is not installed, the rest of the app still works, but JS syntax checking is skipped.

---

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

This is needed for inspiration site analysis.

### 5. Create your `.env` file

Create a file named `.env` in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

The app reads this variable in `config.py`.

---

## Running the app

Start the Flask server:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

## Using the app

### Generate a portfolio

In the chat box, paste resume text or describe the site you want.

Example:

```text
Create a modern software engineer portfolio. Use a dark theme, highlight my projects, and include a contact section. Here is my resume:
[paste resume here]
```

### Review the parsed resume

If the model returns structured resume data, the app:
- validates it against the resume schema
- saves it to `parsed_resume.json`
- shows it in the Parsed Resume panel

### Review generated HTML

If the model returns valid HTML, the app:
- saves it to `portfolio.html`
- previews it in the Generated Portfolio panel
- switches the UI into rating mode

### Rate the result

Send a number from `1` to `10`.

- `8` to `10`: the portfolio is accepted and the session ends
- `1` to `7`: the app asks for revision feedback

### Revise the portfolio

Describe what should change.

Example:

```text
Make the layout cleaner, reduce the amount of text above the fold, and use a more premium dark color palette.
```

You can also include up to 3 public inspiration URLs.

Example:

```text
Make it feel more editorial and minimal. Use these as inspiration:
https://example.com
https://example.org
```

The app analyzes those pages and uses the summaries when generating the next revision.

---

## Outputs

The app may generate these files in the project root:

### `parsed_resume.json`
Validated structured resume data returned by the model.

### `portfolio.html`
The latest valid standalone portfolio page.

---

## API routes

The Flask app exposes these routes:

- `GET /` – main UI
- `GET /api/state` – current session snapshot
- `POST /api/chat` – submit a message
- `POST /api/reset` – reset the session
- `GET /api/history` – conversation history
- `GET /api/parsed-resume` – saved parsed resume content

---

## Notes and limitations

- The app currently keeps one in-memory session per running server instance.
- Generated HTML must be standalone. External JS and external CSS links are rejected by validation.
- Inspiration URL analysis works best with public pages that render as normal HTML/CSS/JS sites.
- The default model in `core/api_client.py` is currently:

```python
model = "gpt-5-mini"
```

You can change that in code if you want to target a different model.

---

## Common issues

### `OPENAI_API_KEY is missing in your .env file`
Create a `.env` file in the repo root and set:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### Playwright errors during inspiration analysis
Install Chromium with:

```bash
python -m playwright install chromium
```

### JavaScript validation is not running
Install Node.js so the app can use `node --check` for inline script validation.

---

## Suggested next improvements

A few useful upgrades for the project would be:
- add `.env.example`
- add tests for validators and chat state transitions
- support multiple saved portfolio versions
- let users download the generated HTML from the UI
- persist sessions instead of keeping them only in memory
- make the model configurable through environment variables

---

## License

Add your preferred license here before publishing the repository.

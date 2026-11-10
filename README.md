# AI Quiz Generator & Notes Summarizer

A Django web app built for VTU students. Pick a subject and difficulty to get an AI-generated multiple-choice quiz, or paste your notes to get a short summary. Powered by the Google Gemini API)

## Features

- **AI quiz generation:** 10 MCQs per quiz, each with four options (A-D) and exactly one correct answer, with plausible distractors.
- **5 subjects and 3 difficulty levels:** AI, DBMS, Analysis and Design of Algorithms, Operating Systems, Biology; easy, medium or hard.
- **Instant scoring:** score, correct/incorrect counts, accuracy percentage, a feedback message, and a review mode that highlights the right answers.
- **Notes summarizer:** paste up to 5,000 characters and get a 2-3 sentence summary.
- **Reliable AI output:** Gemini is constrained to a Pydantic response schema, so quiz data always comes back as valid JSON (no free-text parsing).
- **Abuse protection:** per-IP rate limiting on all AI endpoints, server-side input validation, CSRF protection.
- **Clean UI:** responsive layout, light/dark theme toggle, loading states, friendly error messages.

## Tech Stack

| Layer | Tools |
|-------|-------|
| Backend | Python, Django 5.1 |
| AI | Google Gemini API (`google-genai`), Pydantic structured output |
| Security | `django-ratelimit`, Django CSRF protection |
| Config | `python-dotenv`, `dj-database-url` |
| Database | SQLite (default), PostgreSQL (via `DATABASE_URL`) |
| Frontend | HTML, CSS, vanilla JavaScript (Django templates) |

## Project Structure

```
quiz/
├── manage.py
├── requirements.txt
├── .env.example
├── quiz/                      # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── quiz_app/
│   ├── views.py               # Page views + AI endpoints (validation, rate limiting)
│   ├── urls.py
│   ├── models.py
│   └── services/
│       └── gemini.py          # All Gemini calls, schemas and error handling
└── templates/
    ├── home.html
    ├── quiz.html
    └── summarizer.html
```

All Gemini calls live in `services/gemini.py`. Views never touch the SDK directly, which keeps them thin, gives one place to handle errors, and makes the AI layer easy to mock in tests.

## Getting Started

### Prerequisites

- Python 3.10+
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
copy .env.example .env           # Windows
# cp .env.example .env           # macOS / Linux
```

Open `.env` and fill in `SECRET_KEY` and `GEMINI_API_KEY`. To generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

### Run

```bash
python manage.py migrate
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | none | Django secret key. App refuses to start without it. |
| `GEMINI_API_KEY` | Yes | none | Gemini API key. If missing, AI endpoints return 503. |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | Gemini model used for quizzes and summaries. |
| `DEBUG` | No | `False` | Set `True` for local development only. |
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated list of allowed hostnames. |
| `AI_RATE_LIMIT` | No | `10/m` | Per-IP limit shared by all AI endpoints (e.g. `10/m`, `100/h`). |
| `DATABASE_URL` | No | SQLite | Set to `postgres://user:password@host:5432/dbname` to use PostgreSQL. |

Never commit your `.env` file. It is already listed in `.gitignore`.

## API Endpoints

Both endpoints accept `POST` with a JSON body and require a CSRF token (the bundled pages send it automatically).

### `POST /generate-quiz/`

Request:

```json
{ "subject": "DBMS", "difficulty": "medium" }
```

Response `200`: a list of questions.

```json
[
  {
    "question": "Which normal form removes partial dependencies?",
    "options": { "A": "1NF", "B": "2NF", "C": "3NF", "D": "BCNF" },
    "answer": "B"
  }
]
```

### `POST /summarize-paragraph/`

Request:

```json
{ "paragraph": "Your notes here..." }
```

Response `200`:

```json
{ "summary": "A 2-3 sentence summary of the notes." }
```

### Error responses

All errors return JSON in the form `{ "error": "message" }`.

| Status | Meaning |
|--------|---------|
| 400 | Invalid body, invalid subject or difficulty, empty text, or text over 5,000 characters |
| 429 | Rate limit exceeded |
| 502 | Gemini call failed or returned an unreadable response |
| 503 | `GEMINI_API_KEY` is not configured |

## How It Works

1. The user picks a subject and difficulty on the quiz page.
2. The frontend sends a `POST` request to `/generate-quiz/` with a CSRF token.
3. The view checks the rate limit, validates the input (subject length, difficulty whitelist), then calls the service layer.
4. `gemini.py` prompts Gemini with a Pydantic schema (`MCQuestion`) so the response is structured JSON with four options and a letter answer.
5. The frontend builds the quiz using DOM `textContent` (never `innerHTML`), so AI-generated text can never run as HTML or JavaScript.
6. Scoring happens in the browser, with a results screen and answer review.

## Security Notes

- Secrets and environment-specific settings come from environment variables, never from code.
- AI endpoints are rate limited per IP and share one combined budget, returning a friendly JSON 429.
- Input is validated server-side (JSON shape, subject length, difficulty whitelist, paragraph length).
- AI output is rendered with `textContent` to prevent XSS.
- Internal exceptions are logged server-side; users only see safe, generic error messages.

## Roadmap

- [x] Phase 1: quiz generation, summarizer, rate limiting, validation, secure config
- [ ] Save quiz results to the database and show real progress stats
- [ ] User accounts and quiz history
- [ ] More VTU subjects and a subject/module picker
- [ ] Unit tests for views and the Gemini service (with a mocked client)
- [ ] Deployment (Docker / Render)

## Author

**Red** - Information Science Engineering, CMR Institute of Technology, Bengaluru

import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from .services import gemini

ALLOWED_DIFFICULTIES = {"easy", "medium", "hard"}
MAX_SUBJECT_LENGTH = 100
MAX_PARAGRAPH_LENGTH = 5000


# --- Page views ---------------------------------------------------------------

def home(request):
    return render(request, "home.html")


def quiz(request):
    return render(request, "quiz.html")


def summarizer(request):
    return render(request, "summarizer.html")


# --- Helpers ------------------------------------------------------------------

def ai_rate(group, request):
    """Read the limit from settings at request time (so AI_RATE_LIMIT in .env is honoured)."""
    return settings.AI_RATE_LIMIT


def _error(message, status):
    return JsonResponse({"error": message}, status=status)


def _json_body(request):
    """Return the parsed JSON object from the request body, or None if it is invalid."""
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


# --- AI endpoints -------------------------------------------------------------
# Both endpoints share the rate-limit group "ai", so one IP gets one combined budget
# of Gemini calls. block=False lets us return our own friendly JSON 429 instead of
# Django's default 403 page.

@require_POST
@ratelimit(group="ai", key="ip", rate=ai_rate, method="POST", block=False)
def generate_quiz_view(request):
    if getattr(request, "limited", False):
        return _error("Too many requests. Please wait a minute and try again.", 429)

    data = _json_body(request)
    if data is None:
        return _error("Invalid request body.", 400)

    subject = str(data.get("subject") or "").strip()
    difficulty = str(data.get("difficulty") or "").strip().lower()

    if not subject or len(subject) > MAX_SUBJECT_LENGTH:
        return _error("Please choose a valid subject.", 400)
    if difficulty not in ALLOWED_DIFFICULTIES:
        return _error("Difficulty must be easy, medium or hard.", 400)

    try:
        questions = gemini.generate_mcq_quiz(subject, difficulty)
    except gemini.GeminiError as exc:
        return _error(exc.message, exc.status)

    # Same response shape as before: a JSON list of {question, options, answer}.
    return JsonResponse(questions, safe=False)


@require_POST
@ratelimit(group="ai", key="ip", rate=ai_rate, method="POST", block=False)
def summarize_paragraph_view(request):
    if getattr(request, "limited", False):
        return _error("Too many requests. Please wait a minute and try again.", 429)

    data = _json_body(request)
    if data is None:
        return _error("Invalid request body.", 400)

    paragraph = str(data.get("paragraph") or "").strip()
    if not paragraph:
        return _error("No paragraph provided", 400)
    if len(paragraph) > MAX_PARAGRAPH_LENGTH:
        return _error(f"Text is too long (max {MAX_PARAGRAPH_LENGTH} characters).", 400)

    try:
        summary = gemini.summarize_text(paragraph)
    except gemini.GeminiError as exc:
        return _error(exc.message, exc.status)

    return JsonResponse({"summary": summary})

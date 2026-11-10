"""All Gemini API calls live in this one module.

Views never talk to the Gemini SDK directly. That keeps the views thin, gives one place
to handle errors, and lets tests replace this module with a fake.
"""
import logging
from typing import Literal

from django.conf import settings
from google import genai
from google.genai import types
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Any failure while talking to Gemini.

    `message` is always safe to show to the user; `status` is the HTTP status the view returns.
    """

    def __init__(self, message, status=502):
        super().__init__(message)
        self.message = message
        self.status = status


# --- Response schema -------------------------------------------------------
# We pass these models to Gemini as the response schema. Gemini is then constrained to
# return JSON of exactly this shape, so we never parse free text or strip code fences.
# Options is an object with fixed keys A-D (instead of a free-form dict) because Gemini's
# schema format does not support dicts with arbitrary keys.

class Options(BaseModel):
    A: str
    B: str
    C: str
    D: str


class MCQuestion(BaseModel):
    question: str
    options: Options
    answer: Literal["A", "B", "C", "D"]


# --- Client ----------------------------------------------------------------

def _client():
    if not settings.GEMINI_API_KEY:
        raise GeminiError("The AI service is not configured on this server.", status=503)
    return genai.Client(api_key=settings.GEMINI_API_KEY)


# --- Public functions ------------------------------------------------------

def generate_mcq_quiz(subject, difficulty, count=10):
    """Return a list of dicts: {question, options: {A..D}, answer}."""
    prompt = (
        f"Generate {count} multiple-choice questions on the subject of {subject} "
        f"at {difficulty} difficulty. Each question must have exactly four options "
        f"(A, B, C, D), exactly one of which is correct. The three wrong options must be "
        f"plausible. Give the letter of the correct option as the answer."
    )
    try:
        response = _client().models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[MCQuestion],
            ),
        )
    except GeminiError:
        raise
    except Exception:
        # Phase 3 will split this into quota / timeout / other with specific messages.
        logger.exception("Gemini quiz generation failed")
        raise GeminiError("Could not generate the quiz right now. Please try again.")

    questions = response.parsed  # list[MCQuestion] built from the schema, or None
    if not questions:
        logger.error("Gemini returned no parsable questions")
        raise GeminiError("The AI returned an unreadable response. Please try again.")
    return [q.model_dump() for q in questions]


def summarize_text(text):
    """Return a 2-3 sentence summary as plain text."""
    prompt = f"Summarize the following notes in 2-3 concise sentences:\n\n{text}"
    try:
        response = _client().models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
    except GeminiError:
        raise
    except Exception:
        logger.exception("Gemini summarization failed")
        raise GeminiError("Could not summarize right now. Please try again.")

    summary = (response.text or "").strip()
    if not summary:
        raise GeminiError("The AI returned an empty summary. Please try again.")
    return summary

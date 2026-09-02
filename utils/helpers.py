"""
helpers.py - Shared utilities for the Resume Analyzer Agent.

Uses the official Google Gemini SDK: google-genai
Free tier available at: https://aistudio.google.com/app/apikey

The new SDK (google-genai >= 1.0) replaces the deprecated google-generativeai package.
"""

import os
import json
import logging

from dotenv import load_dotenv, find_dotenv
from google import genai
from google.genai import types

# Load .env from current folder or any parent folder
# This means .env can live in resume-analyzer-agent/ OR its parent folder
load_dotenv(find_dotenv(usecwd=True) or find_dotenv())

# Set up logging so we can debug issues easily
logger = logging.getLogger("resume_analyzer")


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Maximum characters to send to the LLM to avoid token limits.
# Gemini 1.5 Flash supports 1M tokens — keeping conservative for reliability.
MAX_INPUT_CHARS = 15000

# Default model — gemini-2.0-flash is fast, capable, and has a free tier
DEFAULT_MODEL = "gemini-2.0-flash"


def get_model_name() -> str:
    """Get the configured Gemini model name from environment variables."""
    return os.getenv("GEMINI_MODEL", DEFAULT_MODEL)


# ─────────────────────────────────────────────────────────────────────────────
# LLM Client
# ─────────────────────────────────────────────────────────────────────────────

def get_llm_client() -> genai.Client:
    """
    Create and return a configured Gemini client.

    Raises:
        ValueError: If GEMINI_API_KEY is not set in environment variables.
    """
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY is not set. Please add your API key to a .env file.\n"
            "1. Copy .env.example to .env\n"
            "2. Replace 'your_gemini_api_key_here' with your actual Gemini API key\n"
            "3. Get a FREE key from: https://aistudio.google.com/app/apikey"
        )

    return genai.Client(api_key=api_key)


# ─────────────────────────────────────────────────────────────────────────────
# LLM Calling Utility
# ─────────────────────────────────────────────────────────────────────────────

def call_llm(
    prompt: str,
    system_message: str = "You are a helpful assistant.",
    temperature: float = 0.3,
    max_retries: int = 2,
) -> dict:
    """
    Call the Gemini LLM and parse the response as JSON.

    This function:
    1. Creates a Gemini client using the API key from .env
    2. Sends the prompt with JSON MIME type to force structured output
    3. Parses the response as JSON
    4. Retries on transient failures (up to max_retries times)

    Args:
        prompt: The user prompt to send to the LLM.
        system_message: System instructions that set the LLM's behavior/role.
        temperature: Controls randomness (0 = deterministic, 1 = creative).
        max_retries: Number of times to retry on failure.

    Returns:
        A dictionary parsed from the LLM's JSON response.

    Raises:
        ValueError: If API key is missing (not retried).
        RuntimeError: If all retry attempts fail.
    """
    model_name = get_model_name()
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            logger.info(
                f"LLM call attempt {attempt + 1}/{max_retries + 1} using {model_name}"
            )

            # Create a fresh client for each call
            client = get_llm_client()

            # Combine system message + user prompt
            full_prompt = f"{system_message}\n\n{prompt}"

            # Call Gemini with JSON output mode
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    response_mime_type="application/json",  # Force JSON output
                ),
            )

            # Extract text from response
            response_text = response.text

            if not response_text or not response_text.strip():
                raise ValueError("Gemini returned an empty response")

            # Parse JSON
            result = json.loads(response_text)
            logger.info("LLM call successful")
            return result

        except json.JSONDecodeError as e:
            last_error = f"LLM returned invalid JSON: {e}"
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
        except ValueError:
            # Re-raise config errors immediately (no point retrying)
            raise
        except Exception as e:
            last_error = f"LLM call failed: {e}"
            logger.warning(f"Attempt {attempt + 1} failed: {last_error}")

    # All retries exhausted
    raise RuntimeError(
        f"Failed to get a valid response from the LLM after {max_retries + 1} attempts. "
        f"Last error: {last_error}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Text Utilities
# ─────────────────────────────────────────────────────────────────────────────

def truncate_text(text: str, max_chars: int = MAX_INPUT_CHARS) -> str:
    """
    Truncate text to a maximum number of characters.

    Prevents sending extremely long documents to the LLM, which could
    exceed token limits or increase costs unnecessarily.

    Args:
        text: The text to truncate.
        max_chars: Maximum number of characters to keep.

    Returns:
        The truncated text with a note if truncation occurred.
    """
    if len(text) <= max_chars:
        return text

    truncated = text[:max_chars]
    truncated += (
        "\n\n[NOTE: Text was truncated due to length. "
        "Analysis is based on the content above.]"
    )
    logger.info(f"Text truncated from {len(text)} to {max_chars} characters")
    return truncated


def format_score_color(score: int) -> str:
    """
    Return a color string based on the score value (for Streamlit UI).

    Args:
        score: A score from 0 to 100.

    Returns:
        'green' (>=75), 'orange' (>=50), or 'red' (<50).
    """
    if score >= 75:
        return "green"
    elif score >= 50:
        return "orange"
    else:
        return "red"

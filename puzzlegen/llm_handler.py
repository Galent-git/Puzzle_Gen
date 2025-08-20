# ==============================================================================
# puzzlegen/llm_handler.py
#
# Gemini client helpers for:
#   - Lazy loading of prompts.json
#   - Lazy initialization of a shared genai.Client
#   - Generating a puzzle for a given category
#   - Validating the structure of puzzle JSON payloads
#
# This module relies on puzzle_config for MODEL_NAME, REQUIRED_PUZZLE_KEYS,
# and PROMPT_LIBRARY_PATH; and expects GOOGLE_API_KEY to be present in env.
# ==============================================================================

import os
import json
from google import genai

import puzzle_config as config

# --- Prompt Library (lazy) ----------------------------------------------------
_PROMPT_LIBRARY = None
def get_prompt_library() -> dict | None:
    """Load and cache the prompt library from config.PROMPT_LIBRARY_PATH.

    Returns:
        dict | None: Mapping of category -> prompt text, or None if load fails.
    """
    global _PROMPT_LIBRARY
    if _PROMPT_LIBRARY:
        return _PROMPT_LIBRARY

    print("   - Loading prompts.json for the first time...")
    try:
        _PROMPT_LIBRARY = json.loads(config.PROMPT_LIBRARY_PATH.read_text(encoding="utf-8"))
        print(f"   - ✅ Prompts loaded: {config.PROMPT_LIBRARY_PATH.name}")
        return _PROMPT_LIBRARY
    except Exception as e:
        print(f"   - ❌ FATAL: Could not load or parse the prompt library: {e}")
        return None


# --- Gemini Client (lazy) -----------------------------------------------------
_GEMINI_CLIENT = None
def get_gemini_client() -> genai.Client | None:
    """Create and cache the Gemini client using GOOGLE_API_KEY.

    Returns:
        genai.Client | None: Initialized client or None on failure.
    """
    global _GEMINI_CLIENT
    if _GEMINI_CLIENT:
        return _GEMINI_CLIENT

    print("   - Initializing Gemini client...")
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment.")
        _GEMINI_CLIENT = genai.Client(api_key=api_key)
        print("   - ✅ Gemini client initialized successfully.")
        return _GEMINI_CLIENT
    except Exception as e:
        print(f"   - ❌ FATAL: Could not initialize Gemini client: {e}")
        return None


# --- Core API Surface ---------------------------------------------------------
def generate_puzzle_from_llm(category: str) -> dict | None:
    """Request a single puzzle from Gemini for the given category.

    Loads the corresponding category prompt from prompts.json and invokes the
    configured model. Strips common ```json fences before parsing.

    Args:
        category: Name of the category used to select the prompt.

    Returns:
        dict | None: Parsed puzzle JSON on success, otherwise None.
    """
    prompts = get_prompt_library()
    if not prompts:
        return None

    prompt_text = prompts.get(category)
    if not prompt_text:
        print(f"   - ERROR: No prompt found in prompts.json for category '{category}'.")
        return None

    client = get_gemini_client()
    if not client:
        return None

    try:
        model_name = f"models/{config.MODEL_NAME}"
        response = client.models.generate_content(model=model_name, contents=prompt_text)

        cleaned = (response.text or "").strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(cleaned)

    except json.JSONDecodeError:
        print("   - API Error: Response was not valid JSON.")
        try:
            print(f"   - Raw Response: {response.text}")
        except Exception:
            pass
        return None
    except Exception as e:
        print(f"   - An unexpected API error occurred: {e}")
        return None


def validate_puzzle_structure(puzzle_data: dict) -> bool:
    """Check that the payload contains all required keys (case-insensitive).

    Args:
        puzzle_data: The raw puzzle dict returned by the model.

    Returns:
        bool: True if REQUIRED_PUZZLE_KEYS ⊆ keys(puzzle_data), else False.
    """
    if not isinstance(puzzle_data, dict):
        return False
    keys_upper = {k.upper() for k in puzzle_data.keys()}
    return config.REQUIRED_PUZZLE_KEYS.issubset(keys_upper)

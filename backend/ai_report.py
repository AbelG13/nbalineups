# """
# AI Report Generation Module
# Generates AI-powered pregame reports using Google Gemini API (free tier available)
# """
# import os
# import json
# import pandas as pd
# from typing import List, Dict, Optional
# from report import report_data
# from dotenv import load_dotenv
# from datetime import datetime

# # Try to import Gemini library
# try:
#     import google.generativeai as genai
#     GEMINI_AVAILABLE = True
#     print("DEBUG: google.generativeai import OK")
# except ImportError as e:
#     GEMINI_AVAILABLE = False
#     genai = None
#     print("DEBUG: google.generativeai import FAILED:", e)
# # Load environment variables
# # Get the directory where this script is located
# SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# ENV_PATH = os.path.join(SCRIPT_DIR, '.env')

# # Try loading from backend directory first, then fall back to default behavior
# if os.path.exists(ENV_PATH):
#     load_dotenv(ENV_PATH)
# else:
#     load_dotenv()  # Fall back to default behavior (current directory)

# # Get API key from environment
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# # Debug: Print if API key was found (without showing the actual key)
# if GEMINI_API_KEY:
#     print(f"✓ GEMINI_API_KEY loaded successfully (length: {len(GEMINI_API_KEY)} characters)")
#     print(f"  Looking for .env file at: {ENV_PATH}")
# else:
#     print(f"✗ GEMINI_API_KEY not found in environment")
#     print(f"  Expected .env file location: {ENV_PATH}")
#     print(f"  .env file exists: {os.path.exists(ENV_PATH)}")

# # Configure Gemini if API key is available
# if GEMINI_API_KEY and GEMINI_AVAILABLE:
#     try:
#         genai.configure(api_key=GEMINI_API_KEY)
#         print(f"✓ Gemini API configured successfully")
#     except Exception as e:
#         print(f"Warning: Failed to configure Gemini: {e}")

# # Paths
# DATA_DIR = os.path.join(SCRIPT_DIR, "data")
# CACHE_PATH = os.path.join(DATA_DIR, "ai_cache.json")


# # ---------------------------------------------------------------------------
# # Gemini helper
# # ---------------------------------------------------------------------------

# def _call_gemini(prompt: str) -> str:
#     """
#     Low-level helper to call Gemini with a text prompt.
#     Tries a list of models and returns the first successful response text.
#     """
#     if not GEMINI_API_KEY:
#         return (
#             "Error: GEMINI_API_KEY not configured. Please set it in your .env file. "
#             "Get a free API key at `https://makersuite.google.com/app/apikey`."
#         )

#     if not GEMINI_AVAILABLE:
#         return (
#             "Error: Google Generative AI library not installed. "
#             "Please install with: pip install google-generativeai"
#         )

#     model_names_to_try = [
#         "gemini-2.5-flash",   # latest + fast
#         "gemini-2.0-flash",
#         "gemini-2.5-pro",
#         "gemini-2.0-flash-exp",
#     ]

#     last_error: Optional[str] = None

#     for model_name in model_names_to_try:
#         try:
#             print(f"Trying Gemini model: {model_name}...")
#             model = genai.GenerativeModel(model_name)
#             response = model.generate_content(prompt)
#             print(f"✓ Successfully used model: {model_name}")
#             return response.text
#         except Exception as e:
#             last_error = str(e)
#             print(f"⚠ {model_name} failed: {last_error[:200]}")
#             continue

#     # If all models failed, try to list available models for debugging context
#     available_models = []
#     try:
#         for m in genai.list_models():
#             if "generateContent" in m.supported_generation_methods:
#                 model_name = m.name.split("/")[-1]
#                 available_models.append(model_name)
#     except Exception:
#         pass

#     available_info = (
#         f"Available models: {', '.join(available_models[:10])}"
#         if available_models
#         else "Could not list available models"
#     )
#     return (
#         "Error generating AI content. "
#         f"Tried models: {', '.join(model_names_to_try)}. "
#         f"{available_info}. "
#         f"Last error: {last_error or 'unknown'}"
#     )


# # ---------------------------------------------------------------------------
# # Simple JSON cache (per game, per stage)
# # ---------------------------------------------------------------------------

# def _load_cache() -> Dict:
#     """
#     Load cache from disk.
#     Structure:
#     {
#       "first_layer": { game_id: { "text": "...", "updated_at": "ISO" } },
#       "second_layer": { game_id: { "text": "...", "updated_at": "ISO" } }
#     }
#     """
#     if not os.path.exists(CACHE_PATH):
#         return {"first_layer": {}, "second_layer": {}}

#     try:
#         with open(CACHE_PATH, "r", encoding="utf-8") as f:
#             data = json.load(f)
#         if not isinstance(data, dict):
#             raise ValueError("Cache root is not a dict")
#         data.setdefault("first_layer", {})
#         data.setdefault("second_layer", {})
#         return data
#     except Exception as e:
#         print(f"Warning: failed to load AI cache: {e}")
#         return {"first_layer": {}, "second_layer": {}}


# def _save_cache(cache: Dict) -> None:
#     os.makedirs(DATA_DIR, exist_ok=True)
#     try:
#         with open(CACHE_PATH, "w", encoding="utf-8") as f:
#             json.dump(cache, f, indent=2)
#     except Exception as e:
#         print(f"Warning: failed to save AI cache: {e}")


# # ---------------------------------------------------------------------------
# # High-level orchestration using llm_messages payloads
# # ---------------------------------------------------------------------------

# def _build_prompt_from_payload(payload: Dict) -> str:
#     """
#     Generic prompt builder for both stages.

#     The `payload` is the structured dict from llm_messages (either first or second
#     message). We pass the JSON to Gemini and instruct it to follow the
#     embedded `instructions`.
#     """
#     instructions = payload.get("instructions", {})

#     instructions_text = json.dumps(instructions, indent=2)
#     payload_text = json.dumps(payload, indent=2)

#     prompt = (
#         "You are an AI assistant that receives structured JSON input with an "
#         "`instructions` section describing your role, task, goals, and "
#         "output requirements.\n\n"
#         "First, read the `instructions` object carefully and follow it exactly.\n"
#         "Then, use the rest of the JSON as context (game_data, players, "
#         "trend_analysis, etc.) to produce your answer.\n\n"
#         "Instructions JSON:\n"
#         f"{instructions_text}\n\n"
#         "Full payload JSON (for context):\n"
#         f"{payload_text}\n\n"
#         "Now produce your final answer, strictly following the instructions and "
#         "output_requirements. Do not repeat the JSON; output only your analysis."
#     )
#     return prompt


# # Public API

# def generate_first_layer_analyses() -> Dict[str, str]:
#     """
#     Generate (or load from cache) first-layer game trend analyses for all games.

#     Returns:
#         dict: { game_id (str): analysis_text }
#     """
#     from llm_messages import build_first_message

#     cache = _load_cache()
#     first_layer_cache: Dict[str, Dict] = cache.get("first_layer", {})

#     # Build payloads for today's games (injuries vs no injuries already handled)
#     payloads = build_first_message()

#     for game_id, payload in payloads.items():
#         key = str(game_id)
#         cached_entry = first_layer_cache.get(key) or {}
#         cached_text = (cached_entry.get("text") or "").strip()

#         # If we have a non-error cached text, reuse it
#         if cached_text and not cached_text.startswith("Error:"):
#             continue

#         prompt = _build_prompt_from_payload(payload)
#         text = _call_gemini(prompt)

#         # Do not cache obvious error strings
#         if text and not str(text).strip().startswith("Error:"):
#             first_layer_cache[key] = {
#                 "text": text,
#                 "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
#             }

#     cache["first_layer"] = first_layer_cache
#     _save_cache(cache)

#     # Return just the text mapping for convenience
#     return {gid: v.get("text", "") for gid, v in first_layer_cache.items()}


# def generate_second_layer_analyses() -> Dict[str, str]:
#     """
#     Generate (or load from cache) second-layer player-prop-oriented analyses.

#     This uses the outputs from the first layer as an input to the second
#     message payloads.

#     Returns:
#         dict: { game_id (str): analysis_text }
#     """
#     from llm_messages import build_all_second_messages

#     cache = _load_cache()
#     second_layer_cache: Dict[str, Dict] = cache.get("second_layer", {})

#     # Ensure first-layer outputs exist (and are cached)
#     first_layer_outputs = generate_first_layer_analyses()

#     # Build payloads for second layer
#     payloads = build_all_second_messages(first_layer_outputs)

#     for game_id, payload in payloads.items():
#         key = str(game_id)
#         cached_entry = second_layer_cache.get(key) or {}
#         cached_text = (cached_entry.get("text") or "").strip()

#         # If we have a non-error cached text, reuse it
#         if cached_text and not cached_text.startswith("Error:"):
#             continue

#         prompt = _build_prompt_from_payload(payload)
#         text = _call_gemini(prompt)

#         # Do not cache obvious error strings
#         if text and not str(text).strip().startswith("Error:"):
#             second_layer_cache[key] = {
#                 "text": text,
#                 "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
#             }

#     cache["second_layer"] = second_layer_cache
#     _save_cache(cache)

#     return {gid: v.get("text", "") for gid, v in second_layer_cache.items()}


# def get_ai_reports_for_all_games() -> Dict[str, str]:
#     """
#     Backwards-compatible convenience wrapper.

#     Historically this returned a single layer of AI reports keyed by game_id.
#     We now treat this as the **first layer** outputs.
#     """
#     return generate_first_layer_analyses()

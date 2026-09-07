import os
import re
import json
from typing import Dict, Any, List, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv

load_dotenv(override=True)

# Initialize offline VADER analyzer
_analyzer = SentimentIntensityAnalyzer()

# Sensitive brand crisis and consumer protection triggers
CRISIS_KEYWORDS = [
    "scam", "fraud", "fake", "counterfeit", "poison", "toxic", "allergy", "allergic",
    "hospital", "cheated", "complaint", "court", "lawsuit", "sue", "illegal", "police",
    "fir", "defective", "hazard", "burn", "infection", "expired", "ruined", "harmful",
    "banned", "penalty", "refund", "stolen", "side effect", "damage", "ccpa", "asci"
]

_keyword_patterns = [
    (kw, re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE))
    for kw in CRISIS_KEYWORDS
]

# Hinglish (Romanized Hindi) sentiment markers
HINGLISH_NEGATIVE = [
    "bekaar", "bekar", "ghatiya", "bakwas", "bakwaas", "dhokha", "barbaad", "barbad",
    "loot", "lut", "looting", "chori", "paisa dooba", "kharaab", "kharab",
    "ganda", "kachra", "nakli", "mat lo", "mat khareedo", "paise barbaad"
]

HINGLISH_POSITIVE = [
    "achha", "acha", "badhiya", "badiya", "zabardast", "mast", "sahi", "shandar",
    "kamaal", "sundar", "bhot accha", "bahut accha", "lajawab"
]

# Regex for Indic Scripts (Devanagari, Bengali, Gurmukhi, Gujarati, Tamil, Telugu, Kannada, Malayalam)
INDIC_SCRIPTS_PATTERN = re.compile(
    r"[\u0900-\u097F"  # Devanagari (Hindi, Marathi, Sanskrit)
    r"\u0980-\u09FF"  # Bengali
    r"\u0A00-\u0A7F"  # Gurmukhi (Punjabi)
    r"\u0A80-\u0AFF"  # Gujarati
    r"\u0B80-\u0BFF"  # Tamil
    r"\u0C00-\u0C7F"  # Telugu
    r"\u0C80-\u0CFF"  # Kannada
    r"\u0D00-\u0D7F]" # Malayalam
)


def detect_language_and_script(text: str) -> str:
    """
    Detects language or script family:
    - Returns 'indic' if Devanagari or other Indian scripts are present
    - Returns 'hinglish' if Romanized Hindi markers are detected
    - Returns 'en' for English
    - Returns other language codes if detected by langdetect with high confidence
    """
    if INDIC_SCRIPTS_PATTERN.search(text):
        return "indic"

    text_lower = text.lower()
    for kw in HINGLISH_NEGATIVE + HINGLISH_POSITIVE:
        if re.search(rf"\b{re.escape(kw)}\b", text_lower):
            return "hinglish"

    # Use langdetect for Latin text if text is reasonably long
    if len(text.strip().split()) >= 4:
        try:
            from langdetect import DetectorFactory, detect_langs
            DetectorFactory.seed = 0
            langs = detect_langs(text)
            # If English is detected with reasonable probability (>= 0.25), classify as English
            for l in langs:
                if l.lang == "en" and l.prob >= 0.25:
                    return "en"
            # Otherwise, if a non-English language is detected with high confidence (>= 0.70)
            if langs and langs[0].prob >= 0.70:
                return langs[0].lang
        except Exception:
            pass

    return "en"


def analyze_multilingual_with_llm(
    text: str,
    detected_lang: str,
    provider: Optional[str] = None,
    api_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Calls Gemini, Groq, or Ollama to evaluate sentiment of non-English / Hinglish comments.
    Returns structured analysis or None if AI call fails or credentials missing.
    """
    selected_provider = provider or os.getenv("AI_PROVIDER", "gemini").lower()
    llm = None

    try:
        if selected_provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if key:
                llm = ChatGoogleGenerativeAI(
                    model=os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash"),
                    google_api_key=key,
                    temperature=0.1
                )
        elif selected_provider == "groq":
            from langchain_groq import ChatGroq
            key = api_key or os.getenv("GROQ_API_KEY")
            if key:
                llm = ChatGroq(
                    model_name="llama-3.3-70b-versatile",
                    groq_api_key=key,
                    temperature=0.1
                )
        elif selected_provider == "ollama":
            from langchain_community.chat_models import ChatOllama
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            llm = ChatOllama(model="qwen2.5:7b", base_url=base_url, temperature=0.1)
    except Exception:
        llm = None

    if not llm:
        return None

    try:
        from langchain_core.messages import SystemMessage

        prompt = f"""You are an expert multilingual sentiment analyst for Indian social media comments (Hindi, Hinglish, Tamil, Telugu, etc.).
Analyze this comment: "{text}" (detected script/language: {detected_lang}).

Evaluate:
1. True sentiment: "positive", "negative", or "neutral".
2. Sentiment score from -1.0 (very negative) to +1.0 (very positive).
3. Flag for human review (True if complaint, scam claim, defect, allergy, or legal threat; False if clean).
4. Plain-language explanation in English explaining what the commenter said and why it was scored.

Output valid JSON ONLY with this structure:
{{
  "sentiment": "positive"|"negative"|"neutral",
  "sentiment_score": float,
  "flagged_for_review": bool,
  "explanation": "Plain language explanation in English..."
}}"""

        response = llm.invoke([SystemMessage(content=prompt)])
        content = response.content.strip()
        if "{" in content and "}" in content:
            json_str = content[content.find("{"):content.rfind("}")+1]
            data = json.loads(json_str)
            return {
                "sentiment": data.get("sentiment", "neutral").lower(),
                "sentiment_score": float(data.get("sentiment_score", 0.0)),
                "flagged_for_review": bool(data.get("flagged_for_review", False)),
                "explanation": str(data.get("explanation", "")).strip(),
                "language": detected_lang,
                "matched_keywords": []
            }
    except Exception:
        return None

    return None


def analyze_comment(
    text: str,
    provider: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Multilingual sentiment analysis pipeline (Option B):
    1. Detects script and language (English, Hinglish, Indic scripts, foreign).
    2. English comments -> Scored via offline VADER lexicon.
    3. Non-English / Hinglish comments -> Evaluated with Multilingual LLM (Option B) if available.
    4. Offline fallback -> Non-English routed to 'needs_review' (flagged for manual review, zero blind guessing).
    """
    if not text or not text.strip():
        return {
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "flagged_for_review": False,
            "explanation": "",
            "language": "en",
            "matched_keywords": []
        }

    lang = detect_language_and_script(text)

    # --- Path 1: English Comments (Fast Offline VADER) ---
    if lang == "en":
        scores = _analyzer.polarity_scores(text)
        compound = round(float(scores.get("compound", 0.0)), 3)

        if compound >= 0.05:
            sentiment = "positive"
        elif compound <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        matched_keywords = [
            kw for kw, pattern in _keyword_patterns
            if pattern.search(text)
        ]

        flagged = bool(matched_keywords) or (sentiment == "negative" and compound <= -0.3)

        explanation = ""
        if flagged:
            if matched_keywords and sentiment == "negative":
                explanation = (
                    f"Flagged for human review: High negative sentiment ({compound:+.2f}) "
                    f"with crisis keyword(s): {', '.join(matched_keywords)}."
                )
            elif matched_keywords:
                explanation = (
                    f"Flagged for human review: Mentions sensitive brand reputation keyword(s): "
                    f"{', '.join(matched_keywords)}."
                )
            else:
                explanation = f"Flagged for human review: Strongly negative consumer feedback ({compound:+.2f})."

        return {
            "sentiment": sentiment,
            "sentiment_score": compound,
            "flagged_for_review": flagged,
            "explanation": explanation,
            "language": "en",
            "matched_keywords": matched_keywords
        }

    # --- Path 2: Non-English or Hinglish (Option B: Multilingual AI Layer) ---
    llm_result = analyze_multilingual_with_llm(text, lang, provider=provider, api_key=api_key)
    if llm_result:
        return llm_result

    # --- Path 3: Zero-Guessing Fallback (Offline / No Key) ---
    return {
        "sentiment": "needs_review",
        "sentiment_score": 0.0,
        "flagged_for_review": True,
        "explanation": f"Non-English / Indian regional comment detected in '{lang}' script (unscored — needs manual read).",
        "language": lang,
        "matched_keywords": []
    }

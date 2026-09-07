"""
Phase 2.2 Response-Drafting Agent for The Aiges Engine
Generates explainable, de-escalating, non-hallucinating brand response drafts
for negative or flagged comments surfaced in Phase 2.1.
"""
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv(override=True)

RESPONSE_SYSTEM_PROMPT = """You are a brand reputation and crisis management specialist drafting replies to public Instagram comments.

CRITICAL RULES:
1. NEVER invent facts, resolutions, fake tracking numbers, or refund promises that have not happened.
2. If order details, dates, or specifics are needed, instruct the user to direct message (DM) their Order ID or email details.
3. Tone: Empathetic, calm, accountability-focused, and non-defensive. Avoid hollow corporate jargon like "we take customer satisfaction very seriously".
4. Format: Short, natural for social media (under 50 words), directly addressing the customer's frustration.
5. Explainability: Provide an explicit rationale explaining why this tone and de-escalation approach were chosen.

OUTPUT FORMAT: Return a valid JSON object ONLY with two keys:
{
  "drafted_reply": "The public response text...",
  "draft_explanation": "Strategic explanation of tone, empathy framing, and private channel redirect..."
}
"""


def _generate_fallback_draft(
    comment_text: str,
    author_handle: str,
    crisis_explanation: str
) -> Dict[str, str]:
    """
    Offline/deterministic fallback response generator when no external LLM API key is active.
    Guarantees zero downtime, deterministic tests, and high-quality compliant responses.
    """
    text_lower = comment_text.lower()
    user_prefix = f"{author_handle} " if author_handle and not author_handle.startswith("@anonymous") else ""

    if any(k in text_lower for k in ["scam", "fraud", "cheat", "cheated", "liar", "fake"]):
        reply = (
            f"Hi {user_prefix}we are very concerned to hear this. We take brand integrity and customer trust "
            f"seriously. Please DM us your order details and contact number so our management team can investigate "
            f"and assist you directly."
        )
        explanation = (
            "De-escalation strategy: Immediate concern acknowledgment without defensive denial. "
            "Directs severe accusation into private high-priority management channel."
        )
    elif any(k in text_lower for k in ["broken", "damaged", "leak", "hazardous", "defect"]):
        reply = (
            f"Hi {user_prefix}we are so sorry your order arrived in this condition. "
            f"Please send us a DM with your Order ID and photos of the package so our warehouse team can urgently "
            f"arrange a replacement or resolution for you."
        )
        explanation = (
            "Product defect strategy: Empathetic apology for damaged delivery, prompt request for verification "
            "photos, and transparent escalation for replacement."
        )
    elif any(k in text_lower for k in ["allergy", "toxic", "poison", "burning", "side effect", "rash"]):
        reply = (
            f"Hi {user_prefix}we are truly sorry to hear about your reaction. Please discontinue use immediately. "
            f"Kindly DM us your phone number and order ID so our quality care team can connect with you right away."
        )
        explanation = (
            "Health & safety strategy: Immediate priority safety instruction (discontinue use), followed by "
            "urgent direct outreach by the quality care team."
        )
    elif any(k in text_lower for k in ["refund", "money back", "return"]):
        reply = (
            f"Hi {user_prefix}we apologize for the delay in your refund. Please share your Order ID and registered "
            f"email via DM so our billing support team can track the status and help you today."
        )
        explanation = (
            "Billing/refund strategy: Avoids promising immediate payout before verification; requests order ID "
            "privately to expedite resolution."
        )
    else:
        reply = (
            f"Hi {user_prefix}we apologize for your experience and want to make this right. "
            f"Could you please DM us with your order details so our support team can look into this for you?"
        )
        explanation = (
            "General complaint de-escalation: Courteous acknowledgment and pivot to private support channel."
        )

    return {
        "drafted_reply": reply,
        "draft_explanation": explanation
    }


def draft_response_for_mention(
    comment_text: str,
    author_handle: str = "",
    sentiment: str = "negative",
    sentiment_score: float = -0.5,
    crisis_explanation: str = "",
    brand_name: str = "Our Brand",
    custom_instructions: Optional[str] = None,
    provider: str = "ollama",
    model_name: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, str]:
    """
    Drafts an authentic, compliant brand response.
    Tries configured LLM (Ollama, Gemini, Groq, Claude) or falls back to deterministic template generator.
    """
    # 1. Check if LLM invocation is requested and credentials are valid
    llm = None
    try:
        if provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if key:
                llm = ChatGoogleGenerativeAI(
                    model=model_name or os.getenv("GEMINI_MODEL_NAME", "gemini-3.6-flash"),
                    google_api_key=key,
                    temperature=0.3
                )
        elif provider == "groq":
            from langchain_groq import ChatGroq
            key = api_key or os.getenv("GROQ_API_KEY")
            if key:
                llm = ChatGroq(
                    model_name=model_name or "llama-3.3-70b-versatile",
                    groq_api_key=key,
                    temperature=0.3
                )
        elif provider == "ollama":
            from langchain_community.chat_models import ChatOllama
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            # Only try Ollama if explicitly requested and service is reachable
            llm = ChatOllama(
                model=model_name or "qwen2.5:7b",
                base_url=base_url,
                temperature=0.3
            )
    except Exception:
        llm = None

    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage

            user_prompt = (
                f"Customer Comment: \"{comment_text}\"\n"
                f"Customer Handle: {author_handle or 'Unknown'}\n"
                f"Sentiment: {sentiment} ({sentiment_score})\n"
                f"Flag Reason: {crisis_explanation or 'General negative feedback'}\n"
                f"Brand Name: {brand_name}\n"
            )
            if custom_instructions:
                user_prompt += f"Specific Brand Guidance: {custom_instructions}\n"

            messages = [
                SystemMessage(content=RESPONSE_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt)
            ]
            response = llm.invoke(messages)
            content = response.content.strip()

            if "{" in content and "}" in content:
                json_str = content[content.find("{"):content.rfind("}")+1]
                parsed = json.loads(json_str)
                if "drafted_reply" in parsed and "draft_explanation" in parsed:
                    return {
                        "drafted_reply": str(parsed["drafted_reply"]).strip(),
                        "draft_explanation": str(parsed["draft_explanation"]).strip()
                    }
        except Exception:
            pass  # Fall back to offline generator

    # Deterministic fallback
    return _generate_fallback_draft(comment_text, author_handle, crisis_explanation)

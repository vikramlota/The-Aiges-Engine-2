# The Aiges Engine — Marketing Compliance Auditor

An intelligent, multi-modal advertising compliance engine for the Indian digital market. Given influencer posts or YouTube/Instagram URLs, it audits compliance against **ASCI** (Advertising Standards Council of India) and **CCPA** (Central Consumer Protection Authority) rules, detects misleading health/financial claims, and explains *why* in plain language with assigned risk levels.

---

## Folder Structure

```
Project-Market/
├── app.py                         # Streamlit web dashboard (main entry point)
├── core/                          # Core compliance rules & evaluation logic
│   ├── __init__.py
│   ├── engine.py                  # Rule execution & PostInput definition
│   ├── rules.py                   # ASCI/CCPA guidelines & risk scoring
│   ├── models.py                  # Dataclasses (UnifiedAuditReport, VisualAuditResult)
│   └── datastruct.py              # Backward-compatibility alias for models.py
├── ai/                            # LLM & NLP intelligence layer
│   ├── __init__.py
│   ├── ai_engine.py               # LangChain LLM auditor (Ollama / Gemini / Groq)
│   └── claim_classifier.py        # Zero-shot transformer claim classifier
├── pipelines/                     # Platform ingestion & OCR pipelines
│   ├── __init__.py
│   ├── ig_pipeline.py             # Instagram Graph API + OCR pipeline
│   └── yt_pipeline.py             # YouTube Data API + transcript & OCR pipeline
├── utils/                         # Utilities & reporting tools
│   ├── __init__.py
│   ├── generate_validation_log.py # Excel validation workbook generator
│   └── get_permanent_token.py     # Meta Graph API token exchange helper
├── scripts/                       # CLI scripts & runnable examples
│   ├── __init__.py
│   └── demo.py                    # Standalone compliance audit demo
├── data/                          # Data artifacts & local media cache
│   ├── temp_media/                # Downloaded media & OCR frames
│   └── validation_log.xlsx        # Generated audit logs
├── .env                           # API keys & configuration
├── .gitignore
├── requirements.txt               # Documented dependencies
└── README.md
```

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Web Dashboard (Streamlit Prototype)
```bash
streamlit run app.py
```

### 3. Run the Production Full-Stack App (FastAPI + React)

#### Start FastAPI Backend (in `tf_gtx` venv):
```bash
# In WSL:
source ~/tf_gtx/bin/activate
uvicorn backend.main:app --reload --port 8000
```

#### Start React Frontend:
```bash
# In another terminal:
cd frontend
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

#### Run Backend Test Suite:
```bash
source ~/tf_gtx/bin/activate
pytest backend/tests -v
```

### 4. Run the CLI Demo
```bash
python3 scripts/demo.py
# or
python3 -m scripts.demo
```

---

## How It Works

### Core Rule Audit
```python
from core.engine import PostInput, audit_post

post = PostInput(
    platform="Instagram",
    content_type="static_post",       # static_post / reel_story / video / youtube_short / audio_podcast
    material_connection="paid",       # paid / gifted_barter / affiliate / family_business / none_genuine
    caption="#ad Loving this new serum!",
)

result = audit_post(post)
print(result.status)        # COMPLIANT / FLAGGED / NEEDS EXPERT REVIEW / PENDING REVIEW
print(result.risk_level)    # CRITICAL / HIGH / MEDIUM / LOW / ADVISORY
print(result.summary())     # Plain-language explanation of every issue
```

### AI-Powered Caption Analysis
```python
from ai.ai_engine import audit_post_with_ai

ai_audit = audit_post_with_ai(
    caption="This herbal tea cures thyroid completely! #collab",
    platform="Instagram",
    provider="ollama", # or "gemini", "groq"
    model_name="qwen3:8b"
)
print(ai_audit.reviewer_explanation)
print(ai_audit.recommended_fix)
```

### Platform Ingestion Pipelines
```python
from pipelines.ig_pipeline import fetch_single_ig_post, run_ig_pipeline
from pipelines.yt_pipeline import fetch_single_yt_video, run_yt_pipeline
```

---

## Compliance Rules & Guidelines

- **Rules reference**: `core/rules.py` contains the authoritative ASCI label definitions (`APPROVED_LABELS`, `AMBIGUOUS_LABELS`), risk categories, and guidelines.
- **Risk levels**: Checks are classified into `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, and `ADVISORY` to help prioritize urgent consumer safety and legal compliance issues.

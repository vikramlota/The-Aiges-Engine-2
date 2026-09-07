# Vishwas AI — Phase 2.1: Sentiment & Reputation Monitoring — Context Prompt

**Purpose:** paste this at the top of a new conversation (or save as `CLAUDE.md` in this sub-phase's working folder) to build this specific piece with full context, without re-explaining the whole project.

---

## Project context

Vishwas AI is an explainable, compliance-native platform for brand reputation and marketing in India, built by a solo, non-funded founder. Phase 1 — an ASCI/CCPA disclosure compliance engine — exists, is tested, and (status depends on when you're reading this) may already have real validation evidence from paying pilot agencies. This sub-phase is the first piece of Phase 2: sentiment and reputation monitoring on Instagram accounts already being audited.

## Hard constraints — permanent, do not relitigate

- Never fabricate reviews, engagement, or synthetic "social proof."
- Every output that could reach a client or the public needs a human-approval step. This applies here too: sentiment flags and anomaly alerts are *signals for a human*, never autonomous actions.
- Every automated flag carries a plain-language explanation. No black-box scores.
- Default to official platform APIs. Don't add scraping without a deliberate, separate legal-review conversation — India's DPDP Act leaves scraping of "public" personal data in a genuinely unresolved position.

## What already exists — reference, don't rebuild

- `vishwas_compliance/` — the Python disclosure-compliance rule engine (`rules.py`, `engine.py`). Fully tested, has its own test suite.
- An Instagram ingestion pipeline (`ig_pipeline.py`) using Business Discovery API access — reuse this exact access pattern for pulling comments, don't build new auth.
- Depending on build progress: a Streamlit demo app, and/or a FastAPI backend + React frontend with JWT auth, a SQL database, and a Chroma vector store powering "similar past audits."

## This sub-phase's scope — deliberately narrow

Monitor **comments on the same Instagram accounts already being audited** — not a new multi-platform listening pipeline. That's a later, separate decision.

**New data model — `Mention`:**
`id, owner_id (FK User), post_id, platform, author_handle, text, sentiment (positive/negative/neutral), sentiment_score (-1.0 to 1.0), detected_at, flagged_for_review (bool)`

**Sentiment analysis: start with a lexicon-based scorer (e.g. VADER), not a transformer model.** This is deliberate, not a shortcut — it runs fully offline, no model download, and is genuinely adequate for short informal comment text. A transformer sentiment model would likely score higher accuracy but depends on a reliable model download every environment it runs in — the same fragility that hit earlier parts of this project. Upgrade later only if accuracy is confirmed as the actual bottleneck.

**Anomaly detection: a simple statistical rule, not ML.** Flag when daily negative-sentiment volume exceeds roughly 2x the trailing 7-day average. Resist making this fancier before it's proven useful on real data.

**Routes:**
- `POST /api/mentions/ingest` — body `{ "post_id": "..." }`, fetches comments, scores sentiment, stores. Manually triggered at first; a scheduled job is a later optimization.
- `GET /api/mentions` — filterable by `sentiment`, `flagged_only`; filtered by the logged-in user's own tracked accounts, same ownership discipline as `/api/audits`.
- `GET /api/mentions/summary` — aggregate counts, a simple daily trend, and whether the current period is anomalous.

## Exit criteria for this sub-phase

Sentiment labels roughly match your own read of a comment on spot-check (same validation discipline as Phase 1's disclosure flags), and at least one real spike genuinely corresponded to something worth knowing about — not just noise.

## How to help from here

- Assume a solo, non-funded, technical founder who builds and tests incrementally — real tests before shipping, not just "it imports."
- Default to zero/low-cost, offline-reliable solutions over ones that depend on external downloads succeeding.
- Don't relitigate the hard constraints above, even if a request seems to invite it.
- This sub-phase is the dependency for Phase 2.2 (response-drafting) — build it to actually produce real flagged mentions, since the next phase drafts replies to exactly this data.

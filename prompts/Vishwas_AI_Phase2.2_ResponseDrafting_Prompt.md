# Vishwas AI — Phase 2.2: Response-Drafting Agent — Context Prompt

**Purpose:** paste this at the top of a new conversation (or save as `CLAUDE.md` in this sub-phase's working folder) to build this specific piece with full context, without re-explaining the whole project.

---

## Project context

Vishwas AI is an explainable, compliance-native platform for brand reputation and marketing in India, built by a solo, non-funded founder. Phase 1 (disclosure compliance) and Phase 2.1 (sentiment/reputation monitoring) exist before this sub-phase starts. This piece drafts suggested replies to negative or flagged comments surfaced by 2.1 — it does not stand alone.

## Hard constraints — permanent, do not relitigate

- Never fabricate reviews, engagement, or synthetic "social proof."
- **A drafted reply is never auto-posted, under any circumstance.** A human approves or edits every single one before it goes anywhere public. This is the single most important rule for this specific sub-phase — the whole point of "drafting" instead of "responding."
- Every draft should be explainable — why this tone, why this content — not just handed over as a black box.
- Default to official platform APIs for anything involving posting.

## Do not start this sub-phase until

Phase 2.1 (sentiment/reputation monitoring) is producing real flagged mentions from real accounts. Building response-drafting against fake or synthetic mention data means never actually learning whether the drafts are good — the whole value of this piece depends on having genuine negative comments to practice on.

## What already exists — reference, don't rebuild

- `vishwas_compliance/` — the disclosure engine.
- The Phase 2.1 `Mention` model and its ingestion/sentiment pipeline — this sub-phase adds fields and one route to it, it doesn't replace it.
- Existing backend (FastAPI, JWT auth, SQL database) and frontend, if built by this point.

## This sub-phase's scope

**New fields on the existing `Mention` model:**
`drafted_reply (text, nullable), approved_by (FK -> User, nullable), approved_at (datetime, nullable)`

**LLM integration:** the Claude API is a natural fit given the rest of this project's context — generate a suggested reply given the comment's text and relevant context (the brand, the platform, the sentiment). Keep the prompt focused: draft a reply, don't decide whether to post it.

**Routes:**
- `POST /api/mentions/{id}/draft-reply` — generates a suggested reply, stores it in `drafted_reply`. Does **not** post anything, does **not** mark the mention as handled.
- `POST /api/mentions/{id}/approve` — a separate, explicit human action that records `approved_by` and `approved_at`. Never conflate "a draft exists" with "a human signed off on it" — these must be two distinct, auditable states.

**Prompt design note:** the drafted reply should read like it's written by the brand's actual voice, not a generic customer-service template — but never invent facts about the brand, the product, or a resolution that hasn't actually happened. If the comment needs a factual answer the model doesn't have (e.g. "when will my refund arrive"), the draft should say so honestly rather than guess, and flag that a human needs to fill in the real answer.

## Exit criteria for this sub-phase

A reviewer (you, or whoever's doing this by the time it's built) would actually send a meaningful fraction of the drafted replies with light or no editing — not rewrite every single one from scratch. If most drafts get thrown out, that's a real signal to revisit the prompt design, not to ship anyway.

## How to help from here

- Assume a solo, non-funded, technical founder who builds and tests incrementally.
- Treat the approve/draft separation as non-negotiable in any implementation you propose — don't suggest shortcuts that blur "drafted" and "sent," even for convenience.
- Don't relitigate the hard constraints above, even if a request seems to invite it.

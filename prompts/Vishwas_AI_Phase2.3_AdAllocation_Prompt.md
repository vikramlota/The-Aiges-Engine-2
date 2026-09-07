# Vishwas AI — Phase 2.3: Game-Theory Ad-Allocation Agent — Context Prompt

**Purpose:** paste this at the top of a new conversation (or save as `CLAUDE.md` in this sub-phase's working folder) to build this specific piece with full context, without re-explaining the whole project.

---

## Project context

Vishwas AI is an explainable, compliance-native platform for brand reputation and marketing in India, built by a solo, non-funded founder. Phase 1 (disclosure compliance), Phase 2.1 (sentiment monitoring), and Phase 2.2 (response drafting) exist before this sub-phase starts. This is the highest-stakes piece of Phase 2 — it touches real advertising spend, not just content review.

## Hard constraints — permanent, do not relitigate

- Every budget-shift recommendation is a *suggestion for a human to approve*, never an autonomous spend change — same compliance-gate principle as everything else in this project, now applied to real money.
- Every recommendation carries a plain-language explanation of why (which channel, what data, what confidence) — no black-box allocation scores.
- Never fabricate performance data or extrapolate confidently from too little data — say so honestly when a channel doesn't have enough history to recommend anything yet.

## Do not start this sub-phase until

An agency already trusts you enough to connect real ad platform accounts — this depends on relationship trust built through Phases 1, 2.1, and 2.2, not just technical readiness. Building this against synthetic ad-spend data teaches you nothing about whether real budget decisions are being made well, and the stakes (real client money) are meaningfully higher than anything built so far — worth having genuine trust in place first.

## What already exists — reference, don't rebuild

- `vishwas_compliance/`, the Phase 2.1 sentiment pipeline, and the Phase 2.2 response-drafting agent.
- Existing backend (FastAPI, JWT auth, SQL database) and frontend.

## This sub-phase's scope

**New external dependency:** OAuth integration with Google Ads API and/or Meta Marketing API — this is real infrastructure (handling ad account access, real spend/performance data) and deserves its own careful security review before building, not a quick add-on.

**Core algorithm:** a multi-armed bandit — Thompson Sampling is the standard, well-documented starting choice — treating each ad channel or creative as an "arm." Shift budget recommendations toward whichever arm is currently returning the best marginal ROI, while still allocating enough to unproven arms to detect one that's actually improving. This is genuine statistics, not a simple rule — worth a dedicated design pass (what's the reward signal, what's the exploration rate, how much historical data is needed before a recommendation is trustworthy) rather than a quick implementation.

**New data model, sketched at a high level (design in full when you actually get here):** an `AdChannel` or `Campaign` record per connected account (channel name, current spend, current performance metrics), and an `AllocationRecommendation` record (suggested shift, reasoning, confidence, human-approval fields — same `approved_by`/`approved_at` pattern as Phase 2.2's replies).

**Routes, sketched:**
- `POST /api/ad-accounts/connect` — OAuth flow for connecting a real ad account.
- `GET /api/ad-accounts/{id}/performance` — pull current spend/performance data.
- `POST /api/ad-accounts/{id}/recommend` — run the bandit algorithm, return a recommendation with reasoning, never auto-apply it.
- `POST /api/recommendations/{id}/approve` — explicit human sign-off before any real budget change happens outside this tool.

## Exit criteria for this sub-phase

A recommendation, when followed, measurably outperforms what the agency would have done by gut feel over a comparable period — not just "the math ran," but a real before/after comparison on actual campaign results.

## How to help from here

- Assume a solo, non-funded, technical founder who builds and tests incrementally.
- This sub-phase involves real money and real third-party financial APIs — hold code review and security practices to a noticeably higher bar than earlier, lower-stakes pieces of this project.
- Don't relitigate the hard constraints above, even if a request seems to invite it.
- If asked to build this before Phases 2.1/2.2 have real usage, or before an agency has actually agreed to connect a real account, say so plainly rather than proceeding quietly.

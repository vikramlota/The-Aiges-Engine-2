# Vishwas AI — Build Guide (Backend + React Frontend)

A route-by-route, requirement-by-requirement map for building this yourself.
No code here on purpose — this is the contract between backend and frontend,
and the order of operations, so you're not guessing either.

---

## 1. Requirements

**Backend (Python)**
- `fastapi` + `uvicorn` — the API framework and server
- `sqlalchemy` — database ORM (works with SQLite now, Postgres later, same code)
- `bcrypt` — password hashing. Use it directly, not through `passlib` —
  `passlib`'s bcrypt integration is currently broken against modern bcrypt
  releases (confirmed this myself while building the earlier version).
- `python-jose[cryptography]` — JWT creation/verification for login sessions
- `pydantic` (comes with FastAPI) — request/response validation
- `chromadb` — the vector database, for the "similar past audits" feature
- `scikit-learn` — specifically `HashingVectorizer`, to generate the vectors
  Chroma stores. Not a downloaded transformer model — that needs a real
  internet connection to huggingface.co every time it's not already
  cached, which is a fragile thing to depend on. A hashing vectorizer is
  deterministic, needs no download, and is good enough for the caption
  volumes this tool will actually see for a long while.
- Your existing `vishwas_compliance` package (the rule engine) — reused
  as-is, not rewritten.

**Frontend (React)**
- `vite` — scaffolding/dev server (faster and simpler than Create React App)
- `react-router-dom` — for the login/signup/app-view routing
- No Redux, no heavy state library needed at this size — React's built-in
  Context API is enough to hold "who's logged in" and "what's the current
  token." Reach for something heavier only if this genuinely outgrows it.
- Plain `fetch` is fine; `axios` is a convenience, not a requirement.

**Infrastructure**
- Database: SQLite to start (zero setup). Swap to Postgres later (Supabase
  or Neon free tier) by changing one connection string — don't set up
  Postgres before you need it.
- `SECRET_KEY` env var for signing JWTs — must be a real random value in
  any deployed version, never the placeholder you develop with.
- `DATABASE_URL` env var — optional, defaults to local SQLite if unset.
- `CORS_ORIGINS` env var on the backend — **you'll need this in dev**,
  since Vite's dev server runs on a different port (typically
  `localhost:5173`) than FastAPI (typically `localhost:8000`). Without
  CORS configured to allow the Vite origin, every request from your React
  app will fail silently in a way that's confusing to debug the first time.

---

## 2. Data models (backend database tables)

**User**
| field | type | notes |
|---|---|---|
| id | integer, primary key | |
| email | string, unique | |
| hashed_password | string | bcrypt output, never the raw password |
| created_at | datetime | |

**AuditRecord**
| field | type | notes |
|---|---|---|
| id | integer, primary key | |
| owner_id | integer, foreign key → User.id | every query must filter by this |
| platform, content_type, material_connection | string | |
| caption | text | |
| influencer_handle, post_url | string | |
| status | string | COMPLIANT / FLAGGED / NEEDS EXPERT REVIEW / PENDING REVIEW |
| risk_level | string, nullable | CRITICAL / HIGH / MEDIUM / LOW / ADVISORY / null |
| violations, expert_review, explanations | text (JSON-encoded) | |
| summary | text | |
| created_at | datetime | |

---

## 3. API routes you need

All routes below except signup/login/health/meta require an
`Authorization: Bearer <token>` header. A request without one, or with an
invalid/expired one, should return **401**, not a silent failure.

### Auth

**`POST /api/auth/signup`**
Request body:
```json
{ "email": "user@example.com", "password": "at least 8 chars" }
```
Response `201`:
```json
{ "id": 1, "email": "user@example.com", "created_at": "2026-..." }
```
Errors: `400` if the email already exists.

**`POST /api/auth/login`**
Request: `application/x-www-form-urlencoded`, fields `username` (yes,
`username` — it's the OAuth2 password-flow convention even though it's an
email) and `password`.
Response `200`:
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```
Errors: `401` on wrong email/password — don't reveal which one was wrong.

**`GET /api/auth/me`**
Response `200`: same shape as signup's response. Use this on app load to
check whether a stored token is still valid before showing the logged-in view.

### Meta (so your React dropdowns never hardcode a second copy of the rules)

**`GET /api/meta`**
Response `200`:
```json
{
  "platforms": ["Instagram", "YouTube", "..."],
  "content_types": ["static_post", "reel_story", "video", "youtube_short", "audio_podcast"],
  "material_connections": [{ "key": "paid", "label": "Monetary payment for the post." }, "..."],
  "expert_review_categories": [{ "key": "health_wellness_claims", "label": "Health, Wellness & Nutraceutical Claims" }, "..."]
}
```
Fetch this once when the app loads and populate every dropdown from it.
If the rule engine ever adds a category, your frontend updates itself —
you're not maintaining the list twice.

### Audits

**`POST /api/audits`** — run a check and save it
Request body — every field from your `PostInput` dataclass, same names:
```json
{
  "platform": "Instagram",
  "content_type": "static_post",
  "material_connection": "paid",
  "caption": "...",
  "influencer_handle": "", "post_url": "",
  "is_virtual_influencer": false,
  "ai_disclosure_present_and_persistent": null,
  "makes_health_finance_or_technical_claim": false,
  "credentials_or_substantiation_shown": null,
  "video_verbal_disclosure_second": null,
  "video_overlay_covers_sponsored_segment": null,
  "story_label_superimposed": null,
  "ai_generated_or_enhanced": false,
  "ai_content_label_present": null,
  "names_specific_competitor": false,
  "unqualified_superiority_claim": null,
  "product_category": null,
  "mandatory_disclaimer_present": null,
  "content_categories": []
}
```
Response `201`:
```json
{
  "id": 1,
  "status": "FLAGGED",
  "risk_level": "HIGH",
  "violations": ["approved_label", "placement"],
  "expert_review": [],
  "explanations": { "approved_label": "...", "placement": "..." },
  "summary": "FLAGGED (highest risk: HIGH) --\n...",
  "caption": "...",
  "created_at": "2026-...",
  "similar_past_audits": [
    { "id": 3, "caption": "...", "status": "FLAGGED", "risk_level": "HIGH", "similarity": 0.82 }
  ]
}
```
Errors: `422` if `content_type` / `material_connection` / `content_categories`
contain a value the engine doesn't recognize — validate before you hit the
engine, and surface the real error message to the user, don't swallow it.

**`GET /api/audits`** — history list for the logged-in user only
Response `200`: array of `{ id, caption, status, risk_level, created_at }`.
**Never** return another user's audits here — filter by `owner_id` from
the token, not by anything the client sends.

**`GET /api/audits/{id}`** — single audit detail
Same shape as the `POST` response, including a freshly computed
`similar_past_audits`. If the ID doesn't belong to the requesting user,
return **404**, not 403 — don't confirm the ID even exists to someone who
doesn't own it.

### Health

**`GET /api/health`** → `{ "status": "ok" }`. Useful for confirming the
backend's actually up before you start debugging your frontend.

---

## 4. React app structure

```
src/
  main.jsx              # entry point, wraps App in the router + auth context
  App.jsx                # top-level route definitions
  api/
    client.js             # fetch wrapper: attaches the Bearer token,
                           # handles 401 by logging out automatically
  context/
    AuthContext.jsx        # holds { user, token, login(), logout() },
                           # exposes a useAuth() hook
  pages/
    LoginPage.jsx
    SignupPage.jsx
    DashboardPage.jsx      # the main audit form + result + history view
  components/
    ProtectedRoute.jsx     # redirects to /login if not authenticated
    AuditForm.jsx          # mirrors the POST /api/audits body exactly
    ResultDisplay.jsx      # status banner, violations, expert-review, similar audits
    HistoryList.jsx
```

**Auth flow specifics:**
- Store the token in `localStorage` to start (simplest thing that works).
  Know the trade-off: it's readable by any JS on the page, so an XSS bug
  could steal it. An httpOnly cookie is more resistant to that but needs
  more backend work — a reasonable upgrade once there's real user data
  worth the extra protection, not a blocker for a first version.
- On app load: read the token from storage, call `GET /api/auth/me`. If
  it succeeds, you're logged in. If it 401s, clear the token and show the
  login page. This is what makes a page refresh not log someone out.
- Every API call goes through one central function that attaches the
  `Authorization` header and watches for 401 globally — write this once,
  not per-call.

**Form field logic to carry over** (same conditional-field behavior the
vanilla JS version has): video/audio fields only appear when
`content_type` is video/youtube_short/audio_podcast; the Story
superimposed field only for `reel_story`; credential/AI-disclosure/etc.
sub-fields only appear once their parent checkbox is checked. Match this
in React with conditional rendering based on form state, not hidden CSS
classes — cleaner and less error-prone in React than the vanilla-JS
show/hide-a-div approach.

---

## 5. Suggested build order

1. **Backend first, fully working, tested with `curl` or Postman** —
   auth (signup/login/me), then `/api/meta`, then audits. Don't touch
   React until you can complete a full signup → login → create-audit →
   list-history flow from the command line.
2. **Scaffold the React app** (`npm create vite@latest`), get a blank page
   rendering, confirm it can reach `/api/health` across CORS before
   building anything else — this is the step most likely to silently
   trip people up.
3. **Auth pages** — signup and login forms, wired to the real endpoints,
   storing the token, redirecting on success.
4. **Protected route wrapper** — confirm an unauthenticated user actually
   gets bounced to `/login`.
5. **`/api/meta` fetch + dropdown population** — before the full form, so
   you can see real options rendering.
6. **The audit form** — start with just caption + the three required
   dropdowns, get one real result rendering, *then* add the conditional
   fields.
7. **Result display** — status banner, violations, expert-review section,
   similar-past-audits.
8. **History list + click-through to a past result.**
9. **Deploy** — backend to Render/Railway, frontend as a static build
   (Vite's `npm run build` output) to the same host or Vercel/Netlify;
   update `CORS_ORIGINS` on the backend to the real deployed frontend URL.

---

## 6. Testing worth doing as you go (not after)

- Backend: FastAPI's `TestClient` — write a test the moment a route
  works, not at the end. The highest-value ones: wrong password rejected,
  one user can't see another's audits, invalid `content_type` returns
  422 not a 500.
- Frontend: even manual testing benefits from a checklist — after every
  feature, re-check signup → login → audit → logout → login again still
  works. Auth bugs love to hide in the "already logged in" state that's
  easy to stop re-testing once the first version works.

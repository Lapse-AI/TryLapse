# Launch Rehearsal — Argyle (extended run + fixes)

| Field | Value |
|-------|--------|
| **Run ID** | `phase0-argyle-20260529-003` |
| **Date** | May 29, 2026 |
| **Prior** | `phase0-argyle-20260529-002` |
| **Source repo** | `/Users/sparshnagpal/Desktop/projects/Trainer Dashboard` |

---

## AI Search (`/ai-search`)

| | |
|---|---|
| **Journey** | Submit natural-language query |
| **Result** | **Fail (prod)** — `Sorry, I encountered an error: Failed to fetch` |
| **Root cause** | Page called `http://localhost:8002/api/v1/ai-candidate-search` — no backend on Vercel |
| **Fix applied** | `src/app/ai-search/page.tsx` → use same-origin `/api/semantic-search` |
| **Evidence** | `J6-S1` — query returned Failed to fetch before fix |

**After deploy:** Re-test query *"Find HR professionals in Mumbai with 10+ years experience"*.

---

## Resume Parser (`/resume-parser-gemini`)

| | |
|---|---|
| **Journey** | Land → choose file → parse |
| **Result** | **Pass (surface)** — clear UX; Parse disabled until file selected |
| **Copy** | GEMINI API, rate-limit handling, exponential backoff |
| **Not tested** | Actual file upload + parse (no sample resume in run) |
| **Evidence** | `J7-S1` — Choose File + disabled Parse Resumes button |

---

## Code fixes (Trainer Dashboard)

| Issue | File | Change |
|-------|------|--------|
| I6 City filter | `src/app/database/page.tsx` | Enter applies city; match on **full address** not first comma segment |
| I7 View Profile | `src/app/database/page.tsx`, `ai-search/page.tsx` | Removed `target="_blank"` (same-tab nav) |
| I8 Empty job titles | `src/app/database/profile/[id]/page.tsx` | Fallback "Role not specified" |
| I9 Invalid Date | `src/app/database/profile/[id]/page.tsx` | `formatFileDate()` guard |
| I13 AI Search down | `src/app/ai-search/page.tsx` | Route to `/api/semantic-search` |

**Deploy required** — fixes are local until pushed to Vercel.

---

## Updated readiness

| Area | Before | After fix (expected) |
|------|--------|----------------------|
| Candidate Database filters | Amber | **Green** (city Enter + address match) |
| Profile navigation | Amber | **Green** (same-tab links) |
| AI Search | **Red** | **Amber/Green** post-deploy |
| Resume Parser | Untested E2E | **Amber** (UI ok; parse not exercised) |

---

## Next steps

1. **Deploy** Trainer Dashboard to Vercel.  
2. Re-run AI Search query on production.  
3. Upload a test `.pdf`/`.docx` on Resume Parser.  
4. **Rotate password** shared in chat.

# Test groups (dev auth)

Temporary **Phase 1** product scoping for rehearsal testing from one dashboard (Cal.com, Argyle, self-test, staging).

**Sign-in is optional.** The full dashboard works without signing up. Pick a product from the top-bar dropdown; runs and compare filter to that product. Sign-in only labels who is testing (`localStorage`).

## Where it lives

| Surface | Location |
|---------|----------|
| Product switcher | Top bar — violet dropdown (Cal.com, Argyle, …) |
| Persona + target | Sidebar workspace card |
| Runs / compare | Filtered by active product (`useScopedRunSummaries`) |
| Init preset | Init wizard — **Test group preset** panel |
| Config selection | Runner, Sitemap, Workflows, Config (YAML) — `selected-config.ts` |

## How to use

1. Open http://127.0.0.1:8081/
2. Top bar → pick **Cal.com**, **Argyle**, **Self-test**, or **Staging** (no login).
3. Optional: menu → **Sign in (optional)** for a tester label.
4. **Runs** and **command center** show only runs for that product.
5. **Init** → apply preset → **Runner** → run selected config.

Group persists in `rehearse:testGroupId` (default `lr-self`).

## Group → target → config → runs

| Group | Target URL | Config id | Run id / host match |
|-------|------------|-----------|---------------------|
| Cal.com | `https://cal.com` | `cal-com-phase0` | `cal-com-*`, cal.com host |
| Argyle | faculty-dashboard-eight.vercel.app | `argyle-*` | `argyle-*`, matching host |
| Self-test | `http://127.0.0.1:8081` | `lr-self` | `lr-self-*`, localhost |
| Staging | `https://example.com` | `enterprise-saas` | `enterprise-*` |

Matching logic: `runMatchesTestGroup()` in `test-groups.ts` (run id prefix, target URL host, product name).

## Implementation files

- `Frontend_V1/src/lib/test-groups.ts` — groups + run matching
- `Frontend_V1/src/lib/test-auth.ts` — optional mock auth
- `Frontend_V1/src/hooks/use-test-group.ts` — React hook
- `Frontend_V1/src/components/test-group-auth.tsx` — top-bar UI
- `Frontend_V1/src/lib/api/hooks.ts` — `useScopedRunSummaries()`

**Not production auth** — replace with real identity + server-side workspace isolation before partner launch.

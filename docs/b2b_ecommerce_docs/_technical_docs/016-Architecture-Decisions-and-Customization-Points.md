# 016 — Architecture Decisions and Customization Points

The decisions that shaped the platform, why they were made, what they cost, and where to extend
the system without fighting it.

---

## Core Architecture Decisions

### AD-1 · Headless Odoo, custom REST API

**Decision.** Odoo serves as ERP and API only. All customer- and account-manager-facing screens
are a separate Next.js application. Odoo's website/QWeb storefront is not used.

**Why.** B2B buying is a quote negotiation, not a checkout. The required UX (parallel named
baskets, target prices, live chat with an account manager, request-a-product) is far from
`website_sale`'s model. A modern React stack also lets the frontend evolve without Odoo upgrade
risk.

**Cost.** ~110 endpoints to design, document and version by hand; CORS and session complexity;
two deployment pipelines.

---

### AD-2 · Parallel `portal_state` alongside Odoo's `state`

**Decision.** Orders carry a 9-state business status independent of Odoo's 4-value native
state, mapped onto it at every transition.

**Why.** The business needs to distinguish RFQ submitted, RFQ updated, quotation submitted, PO
submitted, in progress and delivered. Odoo's `draft/sent/sale/cancel` cannot express that, and
widening it would break every standard sale flow.

**Cost.** Two fields to keep consistent. Two transitions delegate to real Odoo actions
(quotation send, order confirm) rather than writing fields directly — bypassing them would skip
the PDF, the e-mail and the ERP confirmation.

**Rule.** Never write `portal_state` directly for `quotation_submitted` or `in_progress`. Route
the change through the update endpoint so the delegation runs.

---

### AD-3 · Tenancy enforced in the API layer, not by record rules

**Decision.** Multi-tenant isolation is applied inside `api_*` model methods. The module defines
no `ir.rule`.

**Why.** All portal traffic runs through `sudo()` for performance and to avoid partial-access
errors mid-serialisation. Record rules would be bypassed by `sudo()` anyway, so the scoping
lives where it is actually effective.

**Cost.** **No safety net.** An endpoint that forgets the company scope leaks across tenants.
This is the single highest-risk convention in the codebase.

**Rule.** Every new read must derive its domain from the resolved user's
`portal_company_partner_id`. Every new write must re-verify ownership. Treat this as a
mandatory review item, not a guideline.

---

### AD-4 · `lp_base` as a shared technical foundation

**Decision.** The response envelope, CORS handling and auth decorators live in a separate,
business-free module that other modules subclass.

**Why.** Three modules were duplicating the same plumbing, and duplicate `/test` routes across
modules were colliding at registration.

**Consequence.** Response shape, error semantics and CORS policy change in exactly one place.

---

### AD-5 · Business errors return HTTP 200

**Decision.** Only session expiry returns HTTP 401. Every other failure returns HTTP 200 with a
non-zero `response_code`.

**Why.** A single, unambiguous client contract: HTTP status means transport health,
`response_code` means business outcome. It also prevents infrastructure layers from retrying or
intercepting business failures.

**Cost.** Standard HTTP tooling and monitoring see everything as success. Client code must
branch on `response_code` — never on the status.

---

### AD-6 · Session cookies, not bearer tokens

**Decision.** Authentication uses Odoo's native session cookie with `withCredentials: true`.

**Why.** Reuses Odoo's session, permission and revocation machinery. No token issuance,
refresh or storage to build.

**Cost.** Cross-origin cookie handling; CSRF disabled on API routes, so the CORS policy plus
the credentialed cookie carry the protection. Adding a native mobile client would need a
different scheme.

---

### AD-7 · ID obfuscation as defence in depth {#id-obfuscation}

**Decision.** An abstract model provides reversible XOR + Base64 obfuscation of externally
exposed record IDs, toggled by a system parameter, applied to banners and notifications.

**Why.** Mitigates enumeration and IDOR probing without a schema change or a UUID migration.

**Explicitly not.** This is obfuscation, not encryption. It is a supplement to authentication
and tenancy scoping, never a substitute.

**Operational care.** Flipping the toggle or changing the salt invalidates every identifier a
client already holds. Coordinate with a portal deploy.

---

### AD-8 · Static navigation, AMM only filters {#amm-open-mode}

**Decision.** The portal navigation tree is a static typed structure in the frontend. AMM
supplies permissions that filter it. When AMM is absent or its lookup fails, the store stays in
OPEN mode and everything renders.

**Why.** The portal must run standalone — during development, when AMM is not installed, and
when the permission service is briefly unavailable. Deriving the menu entirely from the API
would make the portal unusable in all three cases.

**Cost.** The screen catalogue exists in two places and must be kept in sync. The join key is
the screen `reference`.

**Current limitation.** AMM is UI-level only. Backend endpoints are not permission-gated — the
enforcement hook exists as a no-op. Do not rely on AMM for data protection; rely on AD-3.

---

### AD-9 · Odoo.sh WebSocket workarounds are load-bearing

**Decision.** Subscribe-first framing, string-channel message mirroring, HTTP presence
heartbeat, and a stale-presence cron.

**Why.** The Odoo.sh gateway rejects any frame sent before `subscribe` (close 4001), never
relays record channels to non-Odoo web clients, and does not deliver socket-close events.

**Cost.** Duplicate chat messages on-premises (deduplicated by message id) and extra HTTP
traffic. Each workaround looks like redundant code until it is removed and Odoo.sh breaks.

**Rule.** Do not "simplify" these paths without testing on Odoo.sh specifically — they cannot
be validated locally.

---

### AD-10 · Thin controllers, fat models

**Decision.** Controllers parse, call one model method, wrap the result. All logic, validation,
scoping and serialisation live in models as `api_*` / `*_payload` methods returning plain dicts.

**Why.** The same logic is reachable from the API, the back-office and tests. Serialisation
helpers (`_prepare_*_dict`) guarantee one shape across list, detail and update responses.

**Cost.** Large model files — the three biggest carry most of the domain.

---

### AD-11 · Dual activation flags

**Decision.** A portal user is usable only when the vendor's `activate` **and** the client's
`portal_activate` are both true.

**Why.** The vendor must be able to suspend a client's access irrespective of what the client's
own admin does, while still delegating day-to-day user management to the client.

---

### AD-12 · Per-client order sequences

**Decision.** Each client company owns an `ir.sequence`; portal order numbers are drawn from it
at creation, in addition to Odoo's global sale-order name.

**Why.** B2B customers expect a continuous, private numbering series and must not be able to
infer the vendor's total order volume.

---

### AD-13 · Independent release trains

**Decision.** Backend and frontend version and deploy separately, through different
infrastructure and different approval models.

**Why.** Different ownership, cadence and infrastructure. Coupling them would block portal fixes
behind the ERP merge queue.

**Cost.** A release is a *pair*. The portal's release files record both head commits so a pair
can be reconstructed. Deploy backend first when a change spans both.

---

### AD-14 · Continuous deployment for the production portal only

**Decision.** The live portal is a Cloudflare Worker rebuilt automatically on every push to
GitHub `main` (OpenNext adapter). The four internal environments keep the manual Docker build.

**Why.** The portal is stateless and carries no business rules, so a bad build is cheap to roll
forward. Shipping storefront fixes should not queue behind the ERP promotion chain.

**Cost — and it is the sharpest edge in the platform.** Production has *no* approval gate while
its backend counterpart has three (`staging-b2b` → `pre-prod` → `training` → `production`, all
merged by the ERP Team). A portal change that depends on a new endpoint can therefore go live
before that endpoint exists in production Odoo.

**Compounding factor.** The repo has two remotes with different roles: PRs are reviewed on
Azure DevOps, but only a push to the **GitHub** remote deploys. Merging a PR looks like
shipping and is not; pushing `main` to GitHub *is* shipping.

**Rule.** Validate on `staging-b2b` and `pre-prod`, confirm the backend has reached Odoo.sh
`production`, then push. Nothing in the pipeline will stop you if you do not.

---

## Customization Points

Where to extend, in decreasing order of safety.

### Configuration only — no code

| Need | Where |
|------|-------|
| New client segment with its own pricing | Client category + pricelist |
| Product visibility for a client | Price rules on that client's pricelist |
| Campaign banners, scheduled or client-targeted | Banner records |
| New portal role / menu restriction | AMM roles and assignments |
| Turn account-manager e-mails on or off | Settings → B2B Ecommerce |
| Enable ID obfuscation | System parameters |

### Data extension — declarative

| Need | Where |
|------|-------|
| New portal screen in the permission catalogue | `ecommerce_access_data` screen + permission records, matched by a frontend nav entry with the same `reference` |
| New notification type | Extend the `ecommerce.notification` type selection |
| New mail wording | The shipped mail templates |
| New back-office queue | An action with a `portal_state` domain plus a menu item |

### Code extension — follow the conventions

| Need | Steps |
|------|-------|
| New API endpoint | 1 · model method returning a dict with `response_code` · 2 · thin controller subclassing the ecommerce base controller, with a **globally unique method name** · 3 · error codes in the central file · 4 · company scoping applied · 5 · frontend `endpoints`/`service`/`types` triple · 6 · store action |
| New portal screen | Page under `app/` with the right guard · nav entry with an AMM `reference` · AMM screen + permission records |
| New order state | Add to the `portal_state` selection **and** to the portal→Odoo state mapping · decide whether it notifies · add the queue in both portals and the back-office |
| New model exposed to the portal | Inherit `ecommerce.base.secure_model` if IDs go outside · add `ir.model.access` rules · implement `_prepare_*_dict` · scope by company |
| Live back-office lists | Inherit `ecommerce.base_auto_refresh_model` |

### Do not

- Do not add business logic to controllers.
- Do not write `portal_state = quotation_submitted` or `in_progress` directly (AD-2).
- Do not query portal data without a company scope (AD-3).
- Do not reuse a controller method name that exists elsewhere in the inheritance chain.
- Do not remove the WebSocket workarounds (AD-9).
- Do not build on `ecommerce.tier` — it is not loaded.
- Do not add raw endpoint strings or `process.env` reads in frontend components.

---

## Known Technical Debt

| Item | Impact | Direction |
|------|--------|-----------|
| Three admin route prefixes (`/ecommerce/api/admin/*`, `/api/admin/*`, `/ecommerce/admin/api/*`) | Inconsistent client configuration | Standardise new endpoints on `/ecommerce/api/admin/*` |
| AMM enforcement is a no-op on the backend | Permissions are UI-level only | Gate endpoints once the permission model settles |
| `ecommerce.tier` present but unloaded | Confusing for newcomers | Remove the files |
| Three very large model files | Hard to navigate and review | Split by concern (catalog / admin management / import) |
| No `test` npm script despite Vitest + Playwright being configured | Nothing runs tests before a production deploy — and production now deploys automatically | Add the script and make the Cloudflare build fail on it |
| No approval gate on production deploys | A push to GitHub `main` is live in minutes (AD-14) | Protect `main`, or gate the Cloudflare build on a passing test/lint run |
| Two portal environments map to one Odoo.sh `training` branch | Easy to deploy against the wrong API host | Verify `NEXT_PUBLIC_APP_API_BASE_URL` before every training deploy |
| Two portal build targets (container + Worker) | A change can behave differently under OpenNext than under the standalone server | Run `preview:cloudflare` locally before pushing to `main` |
| Local-dev timezone differs from the backend default | Dates render differently in dev than in production | Cosmetic only — `.env.production` already sets `Asia/Riyadh`, matching the backend |

---

## Exclusions {#exclusions}

Per the documentation scope, the following exist in the source tree but are **not** documented
as features because they are unreachable from any menu or screen, or not loaded:

| Item | Status |
|------|--------|
| `ecommerce.tier` model and views | Commented out of the model registry; views not in the manifest |
| `pending_approval` order state | Present in the `portal_state` selection but never reached — no screen or endpoint transitions into it. The lifecycle runs `draft → rfq_submitted` directly |
| Arabic / any second language | **Not supported.** The portals are English only. The language flag toggle in the client header is commented out, no translation catalogue is loaded, and the localised message key some endpoints still return is ignored by both portals |
| Passwordless / OTP sign-in | **Not supported.** Login is password-only. The one-time code exists solely for the forgotten-password reset and never creates a session |
| `access.service` abstract model | Declared, no behaviour |
| `require_permission` guard in `lp_base` | Placeholder, no-op |
| `/admin/client-users`, `/admin/users-tags` | Pages exist; their sidebar entries are commented out |
| `/demo-page` | Development scratch page |
| Commented-out back-office menus (To Invoice, Orders to Upsell) | Not registered |
| Repo-root Docker files | Local development only, outside the deploy pipeline |

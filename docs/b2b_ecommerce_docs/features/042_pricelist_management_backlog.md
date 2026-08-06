# Pricelist Management — Backlog Stories (Azure DevOps)

**Portal:** Account Manager Portal (AMP)
**Prefix convention:** `AMP-PL >> <epic>.<story>` — e.g. `AMP-PL >> 02.1`
**Companion docs:** `040_pricelist_management_technical_plan.md` (technical) · `041_pricelist_management_time_plan.md` (business)

Each story below is written **business-first** — the description and acceptance criteria are what a
product owner or tester reads. UI stories then carry a **Test Cases (UI)** table for the QA tester,
and every story ends with **Technical Notes** for the developer picking it up.

## How to Read This Document

### Story anatomy

| Section | Audience |
| --- | --- |
| Description | Product owner, stakeholders |
| Acceptance criteria | Product owner — the definition of done |
| **Test Cases (UI)** | **QA tester — manual test script, UI stories only** |
| Technical notes | Developer |

**Test case ID format:** `TC-<story>-<nn>` — e.g. `TC-02.1-03`.

Stories `AMP-PL >> 01.1`, `01.2` and `04.2` have **no Test Cases section** — they deliver data records
and documentation with no screen of their own. Their effect is proven in `AMP-PL >> 04.1`.

### Standard test users

Set these up once; every UI story's test cases refer to them by role name.

| Test user | Role | Pricing rights |
| --- | --- | --- |
| `qa.superadmin` | Super Admin | Full |
| `qa.pricing` | Pricing Manager | Full |
| `qa.accmgr` | Account Manager | View only |
| `qa.readonly` | Read Only Manager | View only |
| `qa.noaccess` | *(no pricing permission)* | None |

---

## Sequencing Study

### Why the epics are ordered this way

| Epic | Name | Why it sits here |
| --- | --- | --- |
| **01** | Access Foundation | Registers the screens so the feature is reachable from the sidebar and so every later story has a permission to bind its buttons to. It is backend-only and touches no API, so it can run**in parallel** with everything else — but it must be *done* before release readiness. |
| **02** | Pricelist Directory | The entry point. Everything else is reached by clicking a row here, so this screen must exist before the detail view has anywhere to be opened from. Within the epic: read before write — list and search first, then create, then edit, then retire. |
| **03** | Detail & Price Rules | Depends on 02 for navigation. Within the epic: the detail shell must exist before the rules table can be placed inside it, and the rules table must exist before add/edit/remove have anything to act on. |
| **04** | Release Readiness | Verification and documentation can only be meaningful once the behaviour they describe exists. Always last. |

### Dependency graph

```text
        ┌──────────────────────────┐
        │  01  Access Foundation   │  (parallel — off the critical path)
        │  01.1 → 01.2             │
        └──────────────────────────┘
                                          ┌─────────────────┐
  02.1  List & search  ──►  02.2  Create  │                 │
        │                                 │  independent    │
        ├──────────────►  02.3  Edit      │  of each other  │
        │                                 │                 │
        └──────────────►  02.4  Retire    └─────────────────┘
        │
        ▼
  03.1  Detail view
        │
        ▼
  03.2  Rules list  ──►  03.3  Add rule  ──►  03.4  Edit rule
                                          └►  03.5  Remove rule
        │
        ▼
  04.1  Role verification  ──►  04.2  API docs & Postman
```

### Rules applied

1. **Read before write.** A list story always precedes the create/edit/delete stories that mutate it — you cannot verify a write without a read.
2. **Navigation before destination.** A screen is only built once something links to it.
3. **Independent siblings stay separate.** `02.2`, `02.3`, `02.4` do not depend on each other and can be picked up by different developers once `02.1` is merged.
4. **Permissions ship with the feature, verified at the end.** Epic 01 can land early; 04.1 proves it works role by role.

### Story index

| ID | Title | Depends on |
| --- | --- | --- |
| `AMP-PL >> 01.1` | Register Pricelist screens in Access Management | — |
| `AMP-PL >> 01.2` | Grant pricelist permissions to roles | 01.1 |
| `AMP-PL >> 02.1` | View and search the pricelist directory | — |
| `AMP-PL >> 02.2` | Create a new pricelist | 02.1 |
| `AMP-PL >> 02.3` | Edit a pricelist | 02.1 |
| `AMP-PL >> 02.4` | Retire a pricelist | 02.1 |
| `AMP-PL >> 03.1` | Open a pricelist detail view | 02.1 |
| `AMP-PL >> 03.2` | View the price rules of a pricelist | 03.1 |
| `AMP-PL >> 03.3` | Add a price rule ⚠️ *includes an extra backend task — see its notes* | 03.2 |
| `AMP-PL >> 03.4` | Edit a price rule | 03.2 |
| `AMP-PL >> 03.5` | Remove a price rule | 03.2 |
| `AMP-PL >> 04.1` | Verify access per role | 01.2, 02.*, 03.* |
| `AMP-PL >> 04.2` | Update API documentation and Postman collection | 02.*, 03.* |

---

# EPIC 01 — Access Foundation

---

## `AMP-PL >> 01.1` — Register Pricelist screens in Access Management

**As a** platform administrator
**I want** the Pricelist screens to appear in the Account Manager Portal's access catalogue
**So that** I can control who sees and uses them, the same way I control every other screen.

### Business description

Pricing is a new area of the portal. Before anyone can be given access to it, the system needs to
know these screens exist. This story adds "Pricelists" to the portal's screen catalogue, under the
existing **Products Management** section of the menu, together with the list of actions that can be
permitted on it (view, open, create, edit, delete).

Two entries are registered: the pricelist screen itself, and a sub-entry for the price rules inside
it. They are kept separate so the business can grant someone the right to *see* prices without the
right to *change the rules*.

### Acceptance criteria

- [ ] "Pricelists" appears in the Access Management screen catalogue under **Products Management**, after Brands.
- [ ] A sub-entry for **Pricelist Items** exists beneath it.
- [ ] Five actions are available to grant on Pricelists: View, View Detail, Create, Edit, Delete.
- [ ] Four actions are available to grant on Pricelist Items: View, Create, Edit, Delete.
- [ ] No existing screen, category or permission is changed or removed.

### Technical notes

- Module: `addons_lp_ecommerce/access_management/`.
- Add to `data/access_screen_catalogue_data.xml`:
  - `amp.pricelists` — `path` `/admin/pricelists`, `icon` `pi pi-dollar`, `sequence` **40**, `category_id` → **existing** `cat_amp_products`.
  - `amp.pricelist_items` — same category, `parent_id` → `amp.pricelists`.
- **Do not create a new `access.screen.category`** — reuse `cat_amp_products`. Existing sequences there are 10 / 20 / 30, hence 40.
- Add to `data/access_permission_data.xml`, code pattern `<screen_ref>.<action>`:
  - `amp.pricelists.view` (view), `.read_detail` (**custom**), `.create`, `.edit`, `.delete`
  - `amp.pricelist_items.view`, `.create`, `.edit`, `.delete`
- ⚠️ `read_detail` **must** be `action_type = 'custom'`. A model constraint allows only one standard `view`/`create`/`edit`/`delete` per screen, and `view` is taken by the list. This is why Items is a separate screen rather than more permissions on one screen.
- `access.screen.reference` has a UNIQUE constraint — keep the `<app_code>.<screen>` pattern.
- These two files are **not** `noupdate`, so a module upgrade picks them up cleanly.

---

## `AMP-PL >> 01.2` — Grant pricelist permissions to roles

**As a** platform administrator
**I want** the right roles to receive the new pricing permissions automatically
**So that** the team can use the feature on day one without me configuring each role by hand.

### Business description

Once the screens exist, the four existing portal roles need to be told what they may do with them:

| Role | Pricelists | Price Rules |
| --- | --- | --- |
| Super Admin | Full | Full |
| Pricing Manager | Full | Full |
| Account Manager | View only | View only |
| Read Only Manager | View only | View only |

Account Managers can *see* the price a client receives but cannot change it — a separation of duty
the business does not have today.

> ⚠️ **Confirm before starting:** the **Pricing Manager** role is view-only in the system today. This
> story is what turns it into a genuine editing role. Product owner sign-off required.

### Acceptance criteria

- [ ] Super Admin and Pricing Manager hold all nine pricing permissions.
- [ ] Account Manager and Read Only Manager hold exactly three: Pricelists View, Pricelists View Detail, Price Rules View.
- [ ] The grants apply to **existing** databases (staging and production), not only to a fresh install.
- [ ] No permission unrelated to pricing is added to or removed from any role.

### Technical notes

- Roles live in `data/access_role_data.xml`: `role_amp_super_admin`, `role_amp_pricing_manager`, `role_amp_read_only_manager`, `role_amp_account_manager`.
- 🚨 **This file is loaded with `noupdate="1"`.** Editing the XML has **no effect on an already-installed database** — existing roles keep their old permission set on upgrade. Update the XML *and* ship a **migration script** that appends the new permission IDs to the existing roles. Without the migration, this story will pass on a fresh DB and silently fail on staging.
- `access.role` has a constraint that permissions must belong to the same `application_id` as the role — all nine are `app_amp`, so this is satisfied.
- Note `access.role.write()` calls `_action_revoke_all_devices()` on the assigned users whenever `permission_ids` changes. Expect affected users to be logged out after the migration runs; flag this in the release notes.

---

# EPIC 02 — Pricelist Directory

---

## `AMP-PL >> 02.1` — View and search the pricelist directory

**As an** account manager or pricing manager
**I want** to see all pricelists in one screen and search them
**So that** I can find the pricing I need without going into the back-office system.

### Business description

A new **Pricelists** page in the Account Manager Portal, reached from the Products Management
section of the sidebar. It shows each pricelist's **name** and **currency**. A search box filters by
name or currency. The list is paginated. Clicking a pricelist's name opens its detail view.

### Acceptance criteria

- [ ] "Pricelists" appears in the sidebar for users who have been granted the View permission, and is absent for those who have not.
- [ ] The page lists all portal pricelists with Name and Currency columns.
- [ ] The search box filters by name or by currency and shows a clear "no results" state.
- [ ] Results are paginated; page size can be changed.
- [ ] Clicking a pricelist name opens its detail view.
- [ ] The page shows a sensible loading state and a readable message if data cannot be loaded.

### Test cases (UI)

**Preconditions:** at least 25 portal pricelists exist, spanning at least two currencies (e.g. SAR
and USD), plus one archived pricelist.

| ID | Scenario | Steps | Expected result |
| --- | --- | --- | --- |
| TC-02.1-01 | Menu visible with permission | Sign in as`qa.pricing` | "Pricelists" appears in the sidebar under**Products Management**, below Brands |
| TC-02.1-02 | Menu hidden without permission | Sign in as`qa.noaccess` | "Pricelists" is**not** in the sidebar |
| TC-02.1-03 | Direct URL blocked | As`qa.noaccess`, type `/admin/pricelists` in the address bar | Access is refused / redirected — the list is never shown |
| TC-02.1-04 | Columns render | Open the page as`qa.pricing` | Each row shows Name and Currency; no other columns |
| TC-02.1-05 | Search by name | Type a known pricelist name in the search box | Only matching pricelists remain |
| TC-02.1-06 | Search by currency | Type`USD` | Only USD pricelists remain |
| TC-02.1-07 | Search — partial match | Type the first 3 letters of a name | Matching pricelists remain (search is "contains", not "starts with") |
| TC-02.1-08 | Search — no results | Type`zzzzzz` | A clear "no results" message appears; the table is not left blank or broken |
| TC-02.1-09 | Clear search | Clear the search box | The full list returns |
| TC-02.1-10 | Pagination — navigate | Click page 2 | The second page of results loads |
| TC-02.1-11 | Pagination — totals ⚠️ | Note the total count on page 1, then go to page 2 | The total is the**same** on both pages and matches the real number of pricelists *(guards a known defect where the total was recalculated per page)* |
| TC-02.1-12 | Page size | Change page size to 50 | Up to 50 rows are shown and the page count updates |
| TC-02.1-13 | Open detail | Click a pricelist**name** | The detail view for that pricelist opens |
| TC-02.1-14 | No View button | Inspect the actions column | Only**Edit** and **Delete** are present — there is no separate View button |
| TC-02.1-15 | Archived hidden | Look for the archived pricelist | It does**not** appear in the default list |
| TC-02.1-16 | Loading state | Reload the page on a throttled connection | A loading indicator shows; the page does not flash empty or show a false "no results" |
| TC-02.1-17 | Backend unavailable | Stop the backend, reload | A readable error message appears — not a blank screen or a raw technical error |
| TC-02.1-18 | Arabic display | Switch the interface to Arabic | Labels are translated and the layout renders right-to-left without overlap |

### Technical notes

- Route: `/admin/pricelists`. Guard reads `screens[]` from `GET /amm/api/permissions?app=amp&user=<login>`.
- Endpoint **already exists** — `GET /api/admin/pricelists`, params `page`, `limit`, `search`, `active`. Response shape in `040_…md` §4.1. No backend work in this story.
- Note the route prefix is `/api/admin/…`, **not** `/ecommerce/api/admin/…`. This diverges from other admin controllers; keep the whole feature on the existing prefix and log the divergence as tech debt.
- Frontend: `src/app/admin/pricelists/`, service in `src/infrastructure/api/pricelist/`, state in `src/stores/pricelist.store.ts` (`loadPricelists` already exists).
- The backend filters on `is_ecommerce_portal = True`; only portal pricelists appear — this is intended.
- ⚠️ Existing bug worth fixing here: `api_get_pricelists` computes `total_count = len(pricelists)` **after** applying `limit`/`offset`, so pagination totals are wrong on any page beyond the first. Use `search_count(domain)` instead.

---

## `AMP-PL >> 02.2` — Create a new pricelist

**As a** pricing manager
**I want** to create a pricelist from the portal
**So that** I can set up new pricing without raising a request to IT.

### Business description

A **New Pricelist** button on the directory screen opens a short form asking for a **name** and a
**currency**. Both are required. On save, the pricelist is created and appears in the list, ready
for price rules to be added to it.

### Acceptance criteria

- [ ] A "New Pricelist" button is visible only to users granted the Create permission.
- [ ] The form requires a name and a currency; saving without either shows a clear validation message.
- [ ] After saving, the new pricelist appears in the list without a manual page refresh.
- [ ] The newly created pricelist can immediately be opened and have rules added to it.

### Test cases (UI)

| ID | Scenario | Steps | Expected result |
| --- | --- | --- | --- |
| TC-02.2-01 | Button visible with permission | Sign in as`qa.pricing`, open Pricelists | "New Pricelist" button is visible |
| TC-02.2-02 | Button hidden without permission | Sign in as`qa.accmgr` | "New Pricelist" is**not** visible |
| TC-02.2-03 | Create — happy path | Click New, enter name`QA Test List`, currency `SAR`, save | The pricelist is created and a success message appears |
| TC-02.2-04 | Appears without refresh | Immediately after TC-02.2-03 | `QA Test List` is in the table **without** manually reloading the page |
| TC-02.2-05 | Missing name | Leave name blank, choose a currency, save | A clear validation message names the missing field; nothing is created |
| TC-02.2-06 | Missing currency | Enter a name, leave currency unset, save | A clear validation message appears; nothing is created |
| TC-02.2-07 | Both fields missing | Save an empty form | Validation is shown for both fields |
| TC-02.2-08 | Whitespace-only name | Enter`"   "` as the name, save | Treated as empty — validation is shown, not a pricelist named with spaces |
| TC-02.2-09 | Cancel discards | Fill the form, click Cancel | The dialog closes and nothing is created |
| TC-02.2-10 | Usable immediately | Open`QA Test List` right after creating it | The detail view opens and a price rule can be added to it |
| TC-02.2-11 | Long name | Enter a 200-character name, save | Either saved and displayed without breaking the layout, or rejected with a clear message — not a raw server error |
| TC-02.2-12 | Double submit | Click Save twice quickly | Only**one** pricelist is created |
| TC-02.2-13 | Arabic display | Repeat TC-02.2-03 with the interface in Arabic | Form labels, validation and success messages are all in Arabic |

### Technical notes

- New endpoint: `POST /api/admin/pricelists/create`, body `{ name, currency_id }`. Contract in §4.3.
- Add `api_create_pricelist` to `ecommerce/models/pricelist.py`; route in `ecommerce/controllers_admin/pricelist_api.py`.
- 🔑 **Set `is_ecommerce_portal = True` on create** — the list endpoint filters on it, so a pricelist created without this flag will save successfully and then be invisible in the portal.
- 🔑 **Return `'0'` on success, not a custom code.** Verified against `brand.py`, `res_partner.py`, `portal_user_tag.py`, `res_users.py` — every create/update path returns `SUCCESS` (`'0'`). The module defines constants like `BRAND_CREATED` `6207` and `PORTAL_USER_CREATED` `5112` that are **dead code, referenced nowhere**. `fetchy.odoo.client.ts` and every store treat anything other than `'0'` as a failure, so returning a `*_CREATED` code would surface as an error in the UI.
- New **error** codes only, in `ecommerce/api_errors.py` → `PricelistApiErrors` plus messages in `API_ERROR_MESSAGES`: `6005` name required, `6006` currency required. (Also add `6003` ID required and `6004` invalid ID, used by 02.3/02.4.)
- Follow the existing controller pattern (see `brand_api.py`): read JSON or form-data based on `content_type`, wrap in `try/except`, return via `self.api_response(**payload)`.

---

## `AMP-PL >> 02.3` — Edit a pricelist

**As a** pricing manager
**I want** to rename a pricelist or change its currency
**So that** I can correct mistakes and keep pricing labelled clearly.

### Business description

An **Edit** action on each row of the directory (and on the detail screen) opens the same short form,
pre-filled. The name and currency can both be changed.

### Acceptance criteria

- [ ] The Edit action is visible only to users granted the Edit permission.
- [ ] The form opens pre-filled with the current name and currency.
- [ ] The same validation as creation applies — name and currency are both required.
- [ ] After saving, the updated values are reflected in the list immediately.

### Test cases (UI)

| ID | Scenario | Steps | Expected result |
| --- | --- | --- | --- |
| TC-02.3-01 | Action visible with permission | Sign in as`qa.pricing`, open Pricelists | An**Edit** action is on every row |
| TC-02.3-02 | Action hidden without permission | Sign in as`qa.accmgr` | No Edit action on any row |
| TC-02.3-03 | Form pre-filled | Click Edit on`QA Test List` | The form opens showing the current name and currency already populated |
| TC-02.3-04 | Rename | Change the name to`QA Test List v2`, save | The new name appears in the list immediately |
| TC-02.3-05 | Change currency | Change SAR to USD, save | The currency column updates immediately |
| TC-02.3-06 | Clear the name | Delete the name, save | Validation is shown; the original name is unchanged |
| TC-02.3-07 | Cancel discards | Change the name, click Cancel | The list still shows the original name |
| TC-02.3-08 | Edit from detail view | Open a pricelist, use Edit in the header | The same form opens and behaves identically |
| TC-02.3-09 | No unintended change | Edit only the name and save | The currency is untouched |
| TC-02.3-10 | Currency does not convert prices ⚠️ | Note a rule price, change the pricelist currency, reopen the rules | The**number is unchanged** — only the currency label differs. Confirm this is the agreed behaviour before raising a defect |
| TC-02.3-11 | Arabic display | Repeat TC-02.3-04 in Arabic | Labels, validation and success messages are in Arabic |

### Technical notes

- New endpoint: `POST /api/admin/pricelists/update`, body `{ id, name, currency_id }`. Contract in §4.4.
- Add `api_update_pricelist` to the model. Reuse the validation from 02.2. Returns `'0'` on success — see the code convention note in 02.2. New error code `6007` no fields to update, mirroring `BrandApiErrors.NO_FIELDS_TO_UPDATE`.
- Reuse the same form component as 02.2 in edit mode — do not build a second form.
- ⚠️ Changing the currency does **not** convert existing rule prices; the stored figures stay as they are and are simply reinterpreted in the new currency. Confirm with the product owner whether a warning should be shown; out of scope to convert.

---

## `AMP-PL >> 02.4` — Retire a pricelist

**As a** pricing manager
**I want** to retire a pricelist that is no longer used
**So that** the list stays clean without losing any pricing history.

### Business description

A **Delete** action on each row retires a pricelist after a confirmation prompt. Retiring is
**archiving, not erasing** — the pricelist disappears from the working list, but past orders and
pricing history remain intact and auditable. A retired pricelist can be restored by an administrator.

### Acceptance criteria

- [ ] The Delete action is visible only to users granted the Delete permission.
- [ ] A confirmation prompt appears before anything happens, naming the pricelist.
- [ ] After confirming, the pricelist no longer appears in the default list.
- [ ] Historical orders that used this pricelist are unaffected.
- [ ] The record still exists in the system and can be restored.

### Test cases (UI)

**Preconditions:** one disposable pricelist (`QA Retire Me`) and one pricelist that is referenced by
a historical order.

| ID | Scenario | Steps | Expected result |
| --- | --- | --- | --- |
| TC-02.4-01 | Action visible with permission | Sign in as`qa.pricing` | A**Delete** action is on every row |
| TC-02.4-02 | Action hidden without permission | Sign in as`qa.accmgr` | No Delete action on any row |
| TC-02.4-03 | Confirmation appears | Click Delete on`QA Retire Me` | A confirmation prompt appears and**names the pricelist** |
| TC-02.4-04 | Cancel is safe | Dismiss the prompt | The pricelist is still in the list, unchanged |
| TC-02.4-05 | Confirm retires | Confirm the prompt | The pricelist disappears from the list |
| TC-02.4-06 | Message wording ⚠️ | Read the success message in TC-02.4-05 | It says**archived / retired**, not "deleted" — the record still exists |
| TC-02.4-07 | Archive is treated as success ⚠️ | Observe the screen after confirming | A**success** message is shown — *not* an error toast. *(Guards a known integration risk: the archive response uses a distinct code that the UI must treat as success)* |
| TC-02.4-08 | Stays hidden after reload | Reload the page | The retired pricelist still does not appear |
| TC-02.4-09 | History intact | Open the historical order that used the other pricelist | The order opens normally and its pricing is unchanged |
| TC-02.4-10 | Retire from detail view | Open a pricelist, use Delete in the header | Same confirmation and outcome; the user is returned to the list |
| TC-02.4-11 | Restorable | Ask an administrator to restore the retired pricelist | It reappears in the list with its rules intact |
| TC-02.4-12 | Arabic display | Repeat TC-02.4-05 in Arabic | The confirmation prompt and success message are in Arabic |

### Technical notes

- New endpoint: `POST /api/admin/pricelists/delete`, body `{ id }`. Contract in §4.5.
- 🔑 **Archive, do not `unlink()`** — set `active = False`. The list endpoint already supports an `active` filter, and hard-deleting a pricelist referenced by a tier or a client would break pricing history and can raise a FK error.
- 🔑 **This is the one endpoint in the feature that does not return `'0'` on success.** It returns `6008 PRICELIST_ARCHIVED`, mirroring the live precedent in `res_partner.api_delete_client`, where permanent delete returns `'0'` but soft delete returns `CLIENT_ARCHIVED` `5905`. Everything else in this feature returns `'0'` — see 02.2.
- ⚠️ **Frontend must special-case `6008` as a success.** `fetchy.odoo.client.ts` and the stores treat non-`'0'` as failure, so without this the archive will work server-side and still show an error toast.
- Also add `6009` in use — reserved if a guard against archiving a pricelist assigned to active clients or tiers is wanted. Confirm with the product owner whether to block or merely warn.
- Message wording should say *archived*, not *deleted*, so the API response matches the business meaning.

---

# EPIC 03 — Detail & Price Rules

---

## `AMP-PL >> 03.1` — Open a pricelist detail view

**As an** account manager or pricing manager
**I want** to open a single pricelist and see its details
**So that** I have a dedicated place to review and manage the prices inside it.

### Business description

Clicking a pricelist name opens a detail page showing its **name** and **currency**, with **Edit**
and **Delete** actions in the header and a link back to the directory. This page is also the
container for the price rules table delivered in `AMP-PL >> 03.2`.

### Acceptance criteria

- [ ] The page is reachable only by users granted the View Detail permission; others are redirected.
- [ ] Name and currency are displayed.
- [ ] Edit and Delete actions appear in the header, each respecting its own permission.
- [ ] A back link returns to the directory.
- [ ] Opening a pricelist that does not exist shows a clear "not found" message rather than an error screen.

### Test cases (UI)

| ID | Scenario | Steps | Expected result |
| --- | --- | --- | --- |
| TC-03.1-01 | Open from list | As`qa.pricing`, click a pricelist name | The detail view opens for that pricelist |
| TC-03.1-02 | Name and currency shown | Inspect the header | Both the name and currency of the correct pricelist are displayed |
| TC-03.1-03 | Blocked without permission | As`qa.noaccess`, open a detail URL directly | Access is refused / redirected — no pricing data is shown |
| TC-03.1-04 | View-only role | As`qa.accmgr`, open a pricelist | The page opens and shows name and currency, with**no** Edit or Delete action |
| TC-03.1-05 | Edit respects permission | As`qa.pricing` | Edit and Delete are both present in the header |
| TC-03.1-06 | Back link | Click "Back to Pricelists" | The directory reopens |
| TC-03.1-07 | Non-existent record | Change the ID in the URL to one that does not exist | A clear "not found" message appears — not a blank page or a raw error |
| TC-03.1-08 | Invalid ID | Put letters in place of the ID in the URL | Handled gracefully with a readable message |
| TC-03.1-09 | Retired pricelist | Open a pricelist that has been retired | Behaviour matches the agreed design (not-found or a clear "archived" indicator) — never a crash |
| TC-03.1-10 | Direct link works | Copy the detail URL, open it in a new tab | The same pricelist loads directly, without going through the list first |
| TC-03.1-11 | Arabic display | Switch to Arabic | Labels are translated and the layout is right-to-left without overlap |

### Technical notes

- Route: `/admin/pricelists/[id]`.
- Endpoint **already exists** — `GET /api/admin/pricelists/details?id=<id>`. Contract in §4.2. No backend work.
- Not-found returns `response_code` `6001`; handle it as an empty state, not a thrown error.
- Reuse the Edit and Delete flows from 02.3 / 02.4 rather than duplicating them.

---

## `AMP-PL >> 03.2` — View the price rules of a pricelist

**As an** account manager or pricing manager
**I want** to see every price rule inside a pricelist
**So that** I know exactly what a customer will be charged and under what conditions.

### Business description

Inside the detail page, a **Items / Rules** table lists each rule with:

| Column | Meaning |
| --- | --- |
| Product / Variant | Which product the price applies to. A blank variant means*all variants* of that product. |
| Price | What the customer pays. |
| Min Qty | The smallest quantity that unlocks this price — how volume discounts are expressed. |
| Start date | When the price becomes active. Blank means immediately. |
| End date | When the price stops applying. Blank means no expiry. |

A search box filters by product name. The table is paginated.

### Acceptance criteria

- [ ] The table appears only for users granted the Price Rules View permission.
- [ ] All five columns are shown, with blank start/end dates rendered as a clear "—" rather than empty space.
- [ ] A rule that applies to all variants of a product is visually distinguishable from one tied to a single variant.
- [ ] Searching by product name filters the table.
- [ ] The table is paginated and shows an empty state when the pricelist has no rules yet.

### Test cases (UI)

**Preconditions:** a pricelist with at least 25 rules, including one tied to a **specific variant**,
one applying to **all variants**, one with **no dates**, one with **both dates**, and one with a
**start date only**. Plus one pricelist with **no rules at all**.

| ID | Scenario | Steps | Expected result |
| --- | --- | --- | --- |
| TC-03.2-01 | Table visible with permission | Open a pricelist as`qa.pricing` | The Items / Rules table is shown |
| TC-03.2-02 | Table hidden without permission | Open the same page as`qa.noaccess` (if reachable) | The rules table is not shown |
| TC-03.2-03 | View-only role sees rules | Open as`qa.accmgr` | Rules are fully visible, with no Add / Edit / Delete actions |
| TC-03.2-04 | Columns render | Inspect the table | Product/Variant, Price, Min Qty, Start Date and End Date are all present |
| TC-03.2-05 | Blank dates | Find the rule with no dates | Both date cells show a clear placeholder (`—`), not blank space |
| TC-03.2-06 | Start date only | Find that rule | Start shows a date, End shows`—` |
| TC-03.2-07 | All-variants rule | Compare it to the specific-variant rule | The two are visually distinguishable — a tester can tell at a glance which applies to all variants |
| TC-03.2-08 | Search by product | Type a known product name | Only that product's rules remain |
| TC-03.2-09 | Search — no results | Search`zzzzzz` | A clear "no results" message appears |
| TC-03.2-10 | Pagination | Go to page 2 | The next rules load and the total stays consistent across pages |
| TC-03.2-11 | Empty state | Open the pricelist with no rules | A clear "no rules yet" message appears, with the Add Item action still available to`qa.pricing` |
| TC-03.2-12 | Correct scoping ⚠️ | Note the rules on pricelist A, then open pricelist B | B shows**only its own** rules — no bleed-through from A |
| TC-03.2-13 | Price formatting | Inspect the price column | Prices show the expected number of decimals and are readable at a glance |
| TC-03.2-14 | Arabic display | Switch to Arabic | Headers are translated, dates and numbers stay legible, layout is right-to-left |

### Technical notes

- New endpoint: `GET /api/admin/pricelists/items`, params `pricelist_id` (required), `page`, `limit`, `search`. Contract in §4.6.
- Create `ecommerce/models/pricelist_item.py` extending `product.pricelist.item` with `get_item_details()` and `api_get_pricelist_items()`.
- Field mapping (UI → Odoo): Product `product_tmpl_id` · Variant `product_id` · Price `fixed_price` · Min Qty `min_quantity` · Start `date_start` · End `date_end`.
- Returns `'0'` on success — there is no `*_FETCHED` success code. Note `PRICELISTS_FETCHED` `6002` exists in `api_errors.py` but is dead code that no implementation returns; do not follow it.
- New error codes: `6010` item not found, `6011` item ID required.
- Use `search_count()` for the pagination total — do not repeat the `len()` bug noted in 02.1.

---

## `AMP-PL >> 03.3` — Add a price item / rule

**As a** pricing manager
**I want** to add a price  item / rule to a pricelist
**So that** I can set customer pricing, volume discounts and time-limited promotions myself.

### Business description

An **Add Item** button opens a form where the user picks a **product**, optionally narrows it to a
specific **variant**, then sets the **price**, the **minimum quantity**, and optionally a **start**
and **end date**.

Leaving the variant blank applies the price to every variant of that product. Leaving the dates
blank means the price applies immediately and never expires — which is how a standard tier price is
set up. Filling them in is how a seasonal promotion is scheduled to switch itself on and off.

### Acceptance criteria

- [ ] The Add Item button is visible only to users granted the Price Rules Create permission.
- [ ] Product is required; price is required.
- [ ] The variant list only offers variants belonging to the chosen product, and may be left empty.
- [ ] Dates may be left empty; when both are given, the end date must be after the start date.
- [ ] After saving, the new rule appears in the table without a manual refresh.

### Test cases (UI)

**Preconditions:** at least one product **with** variants and one product **without** variants.

| ID | Scenario | Steps | Expected result |
| --- | --- | --- | --- |
| TC-03.3-01 | Button visible with permission | Open a pricelist as`qa.pricing` | "Add Item" is visible |
| TC-03.3-02 | Button hidden without permission | Open as`qa.accmgr` | "Add Item" is not visible |
| TC-03.3-03 | Add — specific variant | Pick a product, pick a variant, price`120`, min qty `5`, save | The rule appears in the table showing the product and variant |
| TC-03.3-04 | Add — all variants | Pick a product, leave the variant empty, price`85`, min qty `10`, save | The rule is saved and displayed as applying to all variants |
| TC-03.3-05 | Appears without refresh | Immediately after saving | The new rule is in the table without a manual page reload |
| TC-03.3-06 | Product is required | Leave the product empty, set a price, save | Validation is shown; nothing is created |
| TC-03.3-07 | Price is required | Pick a product, leave the price empty, save | Validation is shown; nothing is created |
| TC-03.3-08 | Variant list is scoped ⚠️ | Choose product A, then open the variant dropdown | **Only** variants of product A are offered — no variants from other products |
| TC-03.3-09 | Variant list resets | Choose product A, select a variant, then switch to product B | The previously selected variant is cleared; the list now shows B's variants |
| TC-03.3-10 | Product without variants | Choose a product that has no variants | The variant field is empty or disabled, and the rule can still be saved |
| TC-03.3-11 | Dates optional | Save a rule leaving both dates empty | Saved successfully; both date cells show`—` |
| TC-03.3-12 | Scheduled promotion | Set start`01/03/2026`, end `30/06/2026`, save | Saved and both dates display correctly in the table |
| TC-03.3-13 | End before start | Set end date earlier than start date, save | A clear validation message appears; nothing is created |
| TC-03.3-14 | Same-day range | Set start and end to the same day | Handled per the agreed rule — accepted or rejected with a clear message, never a raw error |
| TC-03.3-15 | Zero price | Enter`0` as the price, save | Accepted (a free line is legitimate) or rejected with a clear message — confirm intent with the PO |
| TC-03.3-16 | Negative price | Enter`-5`, save | Rejected with a clear validation message |
| TC-03.3-17 | Volume break | Add two rules for the same product, min qty`1` and `10`, different prices | Both rules coexist in the table; neither overwrites the other |
| TC-03.3-18 | Cancel discards | Fill the form, click Cancel | Nothing is added |
| TC-03.3-19 | Double submit | Click Save twice quickly | Only**one** rule is created |
| TC-03.3-20 | Arabic display | Repeat TC-03.3-03 in Arabic | Labels, the date picker, validation and success messages are all in Arabic |

### Technical notes

- New endpoint: `POST /api/admin/pricelists/items/create`. Contract in §4.7.
- 🔑 Set `applied_on` from the payload: variant present → `'0_product_variant'`; variant blank → `'1_product'`. Force `compute_price = 'fixed'` — this simplified UI does not expose percentage or formula pricing.
- Returns `'0'` on success — see the code convention note in 02.2.

**Picker endpoints — read `040_…_technical_plan.md` §3.3 before starting.** The two dropdowns use
existing admin product endpoints, but there is one gap and two shape traps:

- 🚨 **Extra backend task: add a `search` param to `admin_get_products_payload`** (`models/product_template.py:903`). It currently accepts only `page` / `page_size` with a hard-coded `[('sale_ok','=',True)]` domain and **no name search at all**, so the "Search product…" field in the design cannot work as-is. Append `('name','ilike',search)` when the param is supplied — backward-compatible for existing callers. *This is easy to miss when estimating: the picker is not free.*
- ⚠️ `/ecommerce/api/admin/products` pages **0-based** with `page_size` (default 21) and returns `pager`, while the pricelist endpoints page 1-based with `limit` and return `pagination`. Do not share a paging helper without normalising. Products expose `name_en` / `name_ar` — there is **no plain `name`**.
- ⚠️ `/ecommerce/api/admin/product/variants` takes `product_tmp_id` — **not** `product_tmpl_id`. The wrong spelling returns `MISSING_REQUIRED_FIELDS`, not an empty list. Identifier in the response is `variant_id`, and `name` is the pre-joined combination (`"Color: Red / Size: L"`) — display it directly.
- 🔑 **A product with no attributes returns `variants: []`** — the endpoint skips attribute-less variants (`product_template.py:1942`). Treat an empty list as "no selectable variants, the rule applies to the whole product", **not** as an error. `variant_count` from the products endpoint lets you anticipate this before the call. Covered by TC-03.3-10.
- Field mapping inverts between the pickers and the save payload: products return `product_id` → send as `product_tmpl_id`; variants return `variant_id` → send as `product_id`. Map explicitly.
- New error codes: `6012` product required, `6013` price required, `6014` invalid date range.
- Validate `date_end > date_start` server-side, not only in the form.

---

## `AMP-PL >> 03.4` — Edit a price item / rule

**As a** pricing manager
**I want** to change an existing price rule
**So that** I can adjust a price or extend a promotion without deleting and re-creating it.

### Business description

An edit action on each rule row reopens the same form, pre-filled. Any field can be changed —
including extending a promotion by moving its end date.

### Acceptance criteria

- [ ] The edit action is visible only to users granted the Price Rules Edit permission.
- [ ] The form opens pre-filled with all current values, including the chosen variant.
- [ ] The same validation as creation applies.
- [ ] After saving, the row reflects the new values immediately.

### Test cases (UI)

| ID | Scenario | Steps | Expected result |
| --- | --- | --- | --- |
| TC-03.4-01 | Action visible with permission | Open a pricelist as`qa.pricing` | An edit action is on every rule row |
| TC-03.4-02 | Action hidden without permission | Open as`qa.accmgr` | No edit action on any row |
| TC-03.4-03 | Form pre-filled | Edit a rule that has a specific variant | Product,**variant**, price, min qty and both dates are all pre-filled correctly |
| TC-03.4-04 | Change price | Change price`120` → `115`, save | The row shows`115` immediately |
| TC-03.4-05 | Change min qty | Change min qty`5` → `10`, save | The row updates immediately |
| TC-03.4-06 | Extend a promotion | Move the end date later, save | The new end date is shown |
| TC-03.4-07 | Remove the end date | Clear the end date, save | The end date cell shows`—`; the rule no longer expires |
| TC-03.4-08 | Narrow to a variant | On an all-variants rule, select a specific variant, save | The row now shows that variant |
| TC-03.4-09 | Widen to all variants ⚠️ | On a variant-specific rule, clear the variant, save | The row now applies to all variants of the product |
| TC-03.4-10 | Validation still applies | Clear the price, save | Validation is shown; the original value is unchanged |
| TC-03.4-11 | Invalid date range | Set the end date before the start date, save | Validation is shown; nothing is saved |
| TC-03.4-12 | Cancel discards | Change a value, click Cancel | The row still shows the original value |
| TC-03.4-13 | Only the target row changes | Edit one rule and save | No other rule in the table is altered |
| TC-03.4-14 | Arabic display | Repeat TC-03.4-04 in Arabic | Labels, validation and success messages are in Arabic |

### Technical notes

- New endpoint: `POST /api/admin/pricelists/items/update`, body `{ id, … }`. Contract in §4.8.
- Support partial updates — only the supplied fields should be written.
- If the variant is changed or cleared, recompute `applied_on` using the same rule as 03.3.
- Reuse the 03.3 form component in edit mode — including its two picker endpoints and all the traps listed there. Returns `'0'` on success; new error code `6015` no fields to update.
- ⚠️ **Pre-filling the variant field costs an extra call.** The rule stores only `product_id` (the variant); to show the dropdown with the right option selected you must first call `/ecommerce/api/admin/product/variants?product_tmp_id=<template>` and then match on `variant_id`. Budget for it — TC-03.4-03 checks the variant is pre-filled correctly.
- If the product is changed during an edit, clear the variant and reload the list, same as TC-03.3-09.

---

## `AMP-PL >> 03.5` — Remove a price rule

**As a** pricing manager
**I want** to remove a price rule
**So that** pricing that no longer applies stops being used.

### Business description

A delete action on each rule row removes it after a confirmation prompt. Unlike retiring a whole
pricelist, an individual rule is genuinely removed — it is a line of configuration, not a historical
record.

### Acceptance criteria

- [ ] The delete action is visible only to users granted the Price Rules Delete permission.
- [ ] A confirmation prompt appears before removal.
- [ ] The rule disappears from the table after confirming.
- [ ] Removing a rule does not affect any other rule in the pricelist.

### Test cases (UI)

| ID | Scenario | Steps | Expected result |
| --- | --- | --- | --- |
| TC-03.5-01 | Action visible with permission | Open a pricelist as`qa.pricing` | A delete action is on every rule row |
| TC-03.5-02 | Action hidden without permission | Open as`qa.accmgr` | No delete action on any row |
| TC-03.5-03 | Confirmation appears | Click delete on a rule | A confirmation prompt appears identifying the rule |
| TC-03.5-04 | Cancel is safe | Dismiss the prompt | The rule is still in the table |
| TC-03.5-05 | Confirm removes | Confirm the prompt | The rule disappears from the table |
| TC-03.5-06 | Others untouched ⚠️ | Note all rules before deleting, then compare after | Every other rule is unchanged — same product, price, qty and dates |
| TC-03.5-07 | Correct rule removed ⚠️ | Delete the**second** row of a multi-page table | The row that was actually clicked is the one removed |
| TC-03.5-08 | Stays removed | Reload the page | The deleted rule does not return |
| TC-03.5-09 | Other pricelists unaffected | Open a different pricelist | Its rules are intact |
| TC-03.5-10 | Delete the last rule | Remove the only remaining rule | The empty state appears, with Add Item still available |
| TC-03.5-11 | Arabic display | Repeat TC-03.5-05 in Arabic | The confirmation prompt and success message are in Arabic |

### Technical notes

- New endpoint: `POST /api/admin/pricelists/items/delete`, body `{ id }`. Contract in §4.9.
- Hard `unlink()` is correct here — unlike the pricelist itself, a rule carries no history.
- Verify the rule belongs to the expected pricelist before deleting, so a wrong ID cannot remove a rule from another pricelist.
- Returns `'0'` on success. Unlike pricelist archive (02.4), a rule delete is a genuine delete and gets no custom code.

---

# EPIC 04 — Release Readiness

---

## `AMP-PL >> 04.1` — Verify access per role

**As a** product owner
**I want** confirmation that each role sees and can do exactly what was agreed
**So that** we release knowing pricing cannot be changed by someone who should only be able to view it.

### Business description

A verification pass across the four roles, checking both what appears on screen and what each user
can actually do:

| Role | Expected |
| --- | --- |
| Super Admin | Sees Pricelists; can create, edit, retire, and manage rules |
| Pricing Manager | Same as Super Admin for pricing |
| Account Manager | Sees Pricelists and rules;**no** create/edit/delete buttons anywhere |
| Read Only Manager | Sees Pricelists and rules;**no** action buttons anywhere |

### Acceptance criteria

- [ ] One test user per role has been checked against the table above.
- [ ] A user with no pricing permission does not see Pricelists in the sidebar and cannot reach the page by typing the URL.
- [ ] The Account Manager role can open a pricelist and read its rules, and has no button that would change them.
- [ ] Results are recorded on this work item.

### Test cases (UI)

This story **is** a test pass. Run the matrix below against the target environment and attach the
completed grid to the work item.

#### Permission matrix — tick each cell

| # | Action | `qa.superadmin` | `qa.pricing` | `qa.accmgr` | `qa.readonly` | `qa.noaccess` |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | "Pricelists" in sidebar | ✅ visible | ✅ visible | ✅ visible | ✅ visible | ❌ hidden |
| 2 | Open the pricelist list | ✅ | ✅ | ✅ | ✅ | ❌ blocked |
| 3 | "New Pricelist" button | ✅ | ✅ | ❌ absent | ❌ absent | — |
| 4 | Edit action on a row | ✅ | ✅ | ❌ absent | ❌ absent | — |
| 5 | Delete action on a row | ✅ | ✅ | ❌ absent | ❌ absent | — |
| 6 | Open a pricelist detail | ✅ | ✅ | ✅ | ✅ | ❌ blocked |
| 7 | See the rules table | ✅ | ✅ | ✅ | ✅ | — |
| 8 | "Add Item" button | ✅ | ✅ | ❌ absent | ❌ absent | — |
| 9 | Edit action on a rule | ✅ | ✅ | ❌ absent | ❌ absent | — |
| 10 | Delete action on a rule | ✅ | ✅ | ❌ absent | ❌ absent | — |

#### Additional checks

| ID | Scenario | Steps | Expected result |
| --- | --- | --- | --- |
| TC-04.1-01 | Menu placement | Sign in as`qa.pricing` | "Pricelists" sits under**Products Management**, after Brands — not in a new section |
| TC-04.1-02 | URL cannot bypass the menu ⚠️ | As`qa.noaccess`, paste the pricelist URL directly | Access is refused — hiding the menu item is not the only protection |
| TC-04.1-03 | View-only cannot reach edit by URL | As`qa.readonly`, try to open an edit form directly if it has its own URL | Access is refused or the form is read-only |
| TC-04.1-04 | Grants applied to an upgraded database ⚠️ | Run the full matrix on a**staging database that already existed** before this release, not a fresh install | Results match the matrix.*(Guards a known risk: role grants can load on a fresh install but silently skip an existing database)* |
| TC-04.1-05 | Users logged out after the change | Note whether assigned users' sessions ended when the permissions were applied | Expected side effect — confirm it is mentioned in the release notes rather than raising it as a defect |
| TC-04.1-06 | No unrelated permission drift | Spot-check Orders, Clients and Products for each role | Access to existing screens is exactly as it was before this release |

> ⚠️ **Report, do not raise as a defect:** permissions control **what the screen shows**, not what
> the server refuses. Every admin screen in the portal behaves this way today. If a tester reaches a
> pricing endpoint directly with a tool such as Postman using a view-only account, it may still
> respond. That is the known platform-wide limitation recorded in the plan — note it in the report.

### Technical notes

- Verify via `GET /amm/api/permissions?app=amp&user=<login>` per role: the Pricelists screen should appear in `screens[]` under Products Management with the right `path` and `icon`, and `permissions[]` should hold exactly the expected codes.
- Confirm the 01.2 migration actually ran on the target database — a fresh install and an upgraded install behave differently here.
- ⚠️ **Known limitation to state in the report, not a defect:** permissions gate the **UI only**. `access.service.check()` is permissive in `lp_base`, is not overridden, and is called nowhere, so the endpoints are authenticated-only, exactly like every other admin endpoint in the portal. Server-side enforcement is a separate platform initiative.

---

## `AMP-PL >> 04.2` — Update API documentation and Postman collection

**As a** developer or integrator
**I want** the new pricing endpoints documented and callable from Postman
**So that** the next person to touch this feature does not have to read the source to use it.

### Business description

Documentation and the shared Postman collection are brought up to date with the seven new service
calls, so the feature is maintainable after handover.

### Acceptance criteria

- [ ] All seven new endpoints are in the Postman collection with working sample requests.
- [ ] Every new error code is documented with its message.
- [ ] The feature documentation reflects what was actually built, including any decisions changed during implementation.

### Technical notes

- Endpoints to add: pricelist create / update / delete, items list / create / update / delete.
- Sample bodies and responses are in `040_pricelist_management_technical_plan.md` §4 — copy them rather than inventing new examples.
- Document codes `6003`–`6015` alongside the existing `6001`/`6002`.
- State the convention explicitly in the docs: **success is `'0'`**, and `6008 PRICELIST_ARCHIVED` is the sole exception. Note that `6002 PRICELISTS_FETCHED` is a pre-existing dead constant kept only for numbering continuity.
- Update `040_…md` §1 if any of the three open decisions were resolved differently during the build.

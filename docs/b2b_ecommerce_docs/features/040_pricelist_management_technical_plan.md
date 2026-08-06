# Pricelist Management — Account Manager Portal (AMP)

**Status:** Draft plan for review
**Audience:** Engineering
**Scope:** Pricelist screens in the AMP portal — list view, detail view, and an Items/Rules
sub-list. Only the fields named in the requirements are exposed; all other native
`product.pricelist` / `product.pricelist.item` fields stay hidden in v1.

---

## 1. Codebase Review Summary

| Layer                       | File                                                                | Current state                                                                                                                                                                                                                                                            |
| --------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Backend model ext.          | `ecommerce/models/pricelist.py`                                   | Adds`is_ecommerce_portal`, `item_count`, `action_open_pricelist_items()` to `product.pricelist`. **No item-side extension yet.**                                                                                                                           |
| Backend controller          | `ecommerce/controllers_admin/pricelist_api.py`                    | **Read-only.** `GET /api/admin/pricelists` (paginated, search, filters) and `GET /api/admin/pricelists/details`. No create/update/delete, no items endpoints.                                                                                                  |
| Errors                      | `ecommerce/api_errors.py` → `PricelistApiErrors`               | Only`6001 PRICELIST_NOT_FOUND`, `6002 PRICELISTS_FETCHED`. Range `6003–6099` is free.                                                                                                                                                                             |
| Odoo backend UI             | `ecommerce/views/pricelist_views.xml`, `ecommerce_menus.xml:53` | Native Odoo form/action for internal staff.**Out of scope** — this feature targets the AMP web portal only.                                                                                                                                                       |
| **Access Management** | `addons_lp_ecommerce/access_management/`                          | Purpose-built module:`access.application` → `access.screen.category` → `access.screen` → `access.permission` → `access.role` → `access.role.assignment`, seeded from `data/*.xml`. **No Pricelist screen in the AMP catalogue today.** See §5. |
| Frontend store              | `next_ecommerce/src/stores/pricelist.store.ts`                    | `loadPricelists`, `getPricelistById` only. No CRUD, no items state.                                                                                                                                                                                                  |
| Frontend API                | `next_ecommerce/src/infrastructure/api/pricelist/*`               | Mirrors backend 1:1 (list + details). Uses bare`/api/admin/pricelists` — inconsistent with other admin controllers under `/ecommerce/api/admin/…`.                                                                                                                 |
| AMP routes                  | `next_ecommerce/src/app/admin/**`                                 | No`pricelists` route exists today.                                                                                                                                                                                                                                     |

> **Not in scope:** `ecommerce/security/ir.model.access.csv`. That file governs the native Odoo ORM
> layer for internal Odoo users. This feature targets the AMP frontend, whose endpoints run through
> `.sudo()` — ORM-level ACL rows are not on the path. No changes there.

### Three decisions to settle on Day 1

1. **Route prefix.** Existing pricelist endpoints use `/api/admin/…`; other admin controllers use
   `/ecommerce/api/admin/…`. **Recommendation: keep `/api/admin/pricelists*`** for the whole feature —
   two endpoints already ship against it, and internal consistency beats a half-migration. Log the
   divergence as tech debt.
2. **Delete semantics.** **Recommendation: archive (`active = False`), not `unlink()`** — consistent
   with the `active` filter the list endpoint already supports and with the client archive/restore
   pattern. Hard-deleting a pricelist referenced by a tier or client would break pricing history.
3. **Backend permission enforcement.** `access.service.check()` is declared permissive
   (`return True`) in `lp_base`, is not overridden by `access_management`, and is **called nowhere**.
   Permissions gate the **UI only** today. These endpoints will be exactly as protected as every
   other admin endpoint — authenticated-only. Server-side enforcement is a **cross-cutting platform
   initiative**, not part of this feature.

---

## 2. UI — ASCII Wireframes

### 2.1 Pricelist List View — `/admin/pricelists`

Row name is the link into the detail view; the actions column carries **Edit** and **Delete** only.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  Pricelists                                              [+ New Pricelist]│
├──────────────────────────────────────────────────────────────────────────┤
│  🔍 [ Search by name or currency...            ]                          │
├──────────────────────────────────────────────────────────────────────────┤
│  NAME                         │ CURRENCY   │ ACTIONS                      │
├───────────────────────────────┼────────────┼──────────────────────────────┤
│  Gold Tier Pricing            │ SAR        │       [Edit]     [Delete]    │
│  Silver Tier Pricing          │ SAR        │       [Edit]     [Delete]    │
│  Export Customers (USD)       │ USD        │       [Edit]     [Delete]    │
│  Ramadan Promo 2026           │ SAR        │       [Edit]     [Delete]    │
│   ▲                                                                       │
│   └─ click the name to open the detail view                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                              ◀ 1  2  3 ▶   20 / page ▾    │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Pricelist Detail View — `/admin/pricelists/[id]`

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  ← Back to Pricelists                                                     │
│                                                                            │
│  Pricelist Details                                         [Edit] [Delete]│
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ Name*      [ Gold Tier Pricing                            ]      │    │
│  │ Currency*  [ SAR ▾ ]                                              │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                            │
│  Items / Rules                                              [+ Add Item]  │
│  🔍 [ Search product...            ]                                      │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │ PRODUCT / VARIANT      │ PRICE  │ MIN QTY │ START DATE │ END DATE │   │
│  ├────────────────────────┼────────┼─────────┼────────────┼──────────┤   │
│  │ Widget A / Red - L     │ 120.00 │    5    │ 2026-01-01 │ —        │[✎][🗑]│
│  │ Widget A / Blue - M    │ 118.50 │    5    │ 2026-01-01 │ —        │[✎][🗑]│
│  │ Widget B (all variants)│  85.00 │   10    │ 2026-03-01 │2026-06-30│[✎][🗑]│
│  └──────────────────────────────────────────────────────────────────┘    │
│                                              ◀ 1  2 ▶   20 / page ▾       │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Add / Edit Item Modal

```text
┌───────────────────────────────────────────┐
│  Add Price Rule                       [x] │
├───────────────────────────────────────────┤
│  Product*        [ Search product...  ▾ ] │
│  Variant          [ Select variant    ▾ ] │  ← optional; blank = applies to all variants
│  Price*          [ 0.00                 ] │
│  Min Qty*        [ 1                    ] │
│  Start Date/Time [ dd/mm/yyyy hh:mm     ] │  ← optional
│  End Date/Time   [ dd/mm/yyyy hh:mm     ] │  ← optional
│                                            │
│                       [Cancel]  [Save]    │
└───────────────────────────────────────────┘
```

The two pickers are backed by existing admin product endpoints, with one gap and two shape traps —
see **§3.3** before building this modal.

---

## 3. Endpoint Summary

Route family: **`/api/admin/pricelists*`** (per decision #1). All endpoints are
`@http_auth_validated`, return the standard `{response_code, response_message, …data}` envelope,
and carry CORS headers from `BaseController`.

### 3.1 Pricelist endpoints

| # | Method   | Path                              | Purpose                                    | Status    |
| - | -------- | --------------------------------- | ------------------------------------------ | --------- |
| 1 | `GET`  | `/api/admin/pricelists`         | List — paginated, search by name/currency | ✅ Exists |
| 2 | `GET`  | `/api/admin/pricelists/details` | Single pricelist by`id`                  | ✅ Exists |
| 3 | `POST` | `/api/admin/pricelists/create`  | Create (name + currency)                   | 🆕 New    |
| 4 | `POST` | `/api/admin/pricelists/update`  | Rename / change currency                   | 🆕 New    |
| 5 | `POST` | `/api/admin/pricelists/delete`  | Archive (`active = False`)               | 🆕 New    |

### 3.2 Items / Rules endpoints

| # | Method   | Path                                   | Purpose                                                 | Status |
| - | -------- | -------------------------------------- | ------------------------------------------------------- | ------ |
| 6 | `GET`  | `/api/admin/pricelists/items`        | List rules for a pricelist — paginated, product search | 🆕 New |
| 7 | `POST` | `/api/admin/pricelists/items/create` | Add a price rule                                        | 🆕 New |
| 8 | `POST` | `/api/admin/pricelists/items/update` | Edit a price rule                                       | 🆕 New |
| 9 | `POST` | `/api/admin/pricelists/items/delete` | Remove a price rule                                     | 🆕 New |

### 3.3 Endpoints consumed by the Add / Edit Item modal (§2.3)

The modal is the only screen in this feature that calls endpoints outside the pricelist family. Both
pickers are driven by **existing** admin product endpoints — but they do **not** drop in unchanged,
and the shapes differ from the pricelist endpoints in ways that will bite if assumed.

| #  | Method  | Path                                          | Used for                                 | Status                                               |
| -- | ------- | --------------------------------------------- | ---------------------------------------- | ---------------------------------------------------- |
| P1 | `GET` | `/ecommerce/api/admin/products`             | Product field                            | ⚠️ Exists,**needs a `search` param added** |
| P2 | `GET` | `/ecommerce/api/admin/product/variants`     | Variant field, after a product is chosen | ✅ Exists, usable as-is                              |
| P3 | `GET` | `/amm/api/permissions?app=amp&user=<login>` | Gating the Add / Edit / Delete buttons   | ✅ Exists                                            |

**P1 — `admin_get_products_payload` (`models/product_template.py:903`) has no search capability.**
It accepts only `page` and `page_size`, and its domain is hard-coded to `[('sale_ok', '=', True)]`.
The wireframe's "Search product…" field therefore **cannot be satisfied by the endpoint as it
stands**. Add an optional `search` param that appends `('name', 'ilike', search)` to the domain —
backward-compatible, since existing callers that omit it see identical behaviour.

Two further traps in P1:

- **Paging is 0-based** (`page = int(params.get('page') or 0)`, `page_size` default **21**) and the
  response nests under `pager`, not `pagination`. The pricelist endpoints in §3.1/§3.2 use 1-based
  `page` with `limit`. Do not share a paging helper between them without normalising.
- It `search()`es **every** matching product and slices in Python (`_paginate`,
  `product_template.py:166`). Fine for a picker with a `search` filter applied; do not reuse this
  pattern for the item list in §4.6, which must use `search_count()` + SQL-level `limit`/`offset`.

Response fields relevant to the modal — note there is **no plain `name`**:

```json
{
  "response_code": "0",
  "products": [
    { "product_id": 120, "name_en": "Widget A", "name_ar": "…",
      "variant_count": 3, "list_price": 130.0, "image_url": "…" }
  ],
  "pager": { "page": 0, "page_size": 21, "total": 248 }
}
```

**P2 — `admin_list_product_variants_payload` (`product_template.py:1910`).** Query param is
`product_tmp_id` — **not** `product_tmpl_id`, which is the Odoo field name used everywhere else in
this feature. Passing the wrong spelling returns `MISSING_REQUIRED_FIELDS`, not an empty list.

```json
{
  "response_code": "0",
  "product_tmp_id": 120,
  "summary": { "total_variants": 3 },
  "variants": [
    { "variant_id": 341, "name": "Color: Red / Size: L", "default_code": "WA-RED-L",
      "attributes": [ { "id": 1, "name": "Color", "value_id": 7, "value_name": "Red" } ],
      "lst_price": 130.0, "price_extra": 10.0, "active": true }
  ]
}
```

- Identifier is `variant_id`, not `id`. `name` is the pre-joined attribute combination
  (`"Color: Red / Size: L"`) — display it directly; do not rebuild it from `attributes`.
- 🔑 **Variants with no attributes are skipped** (`if not attributes: continue`). A product without
  attributes has one auto-created variant in Odoo, but this endpoint returns
  `variants: []` for it. The modal must treat an empty list as *"this product has no selectable
  variants"* — a normal state meaning the rule applies to the product as a whole — and **not** as an
  error or an empty dropdown the user is stuck on. Use `variant_count` from P1 to anticipate it.
- The variant field is optional by design: leaving it blank sets `applied_on = '1_product'` (§4.6).

### 3.4 Response-code convention — verified against the existing module

**Every success path returns `'0'` (`SUCCESS`, message `"Success"`). Custom codes are for failures
only.** This was verified by reading the shipped implementations, not assumed:

| Model                                  | Create / Update / Delete success returns                   | Custom success codes defined?                                                                                                                                 |
| -------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `models/brand.py`                    | `BrandApiErrors.SUCCESS` → `'0'`                      | Yes —`BRAND_CREATED` `6207`, `BRAND_UPDATED` `6208`, `BRAND_DELETED` `6209`, `BRANDS_FETCHED` `6206` … **all dead, never referenced** |
| `models/res_partner.py`              | `ClientApiErrors.SUCCESS` → `'0'`                     | ⚠️**Exception:** archive returns `CLIENT_ARCHIVED` `5905`, restore returns `CLIENT_RESTORED` `5906` — these *are* used                     |
| `models/portal_user_tag.py`          | `PortalUserTagApiErrors.SUCCESS` → `'0'`              | —                                                                                                                                                            |
| `models/product_request_line.py`     | `ApiErrorCodes.SUCCESS` → `'0'`                       | —                                                                                                                                                            |
| `models/res_users.py`                | `UserApiErrors.SUCCESS` → `'0'` (all 9 success paths) | Yes —`PORTAL_USER_CREATED` `5112`, `PORTAL_USER_UPDATED` `5113`, `AUTHENTICATED` `5116` … **all dead**                                    |
| `controllers_admin/pricelist_api.py` | `PricelistApiErrors.SUCCESS` → `'0'`                  | Yes —`PRICELISTS_FETCHED` `6002` **defined but never used**                                                                                        |

> **Trap to avoid:** the codebase is full of `*_CREATED` / `*_UPDATED` / `*_FETCHED` constants that
> look like the intended convention but are dead code — no implementation returns them, and the
> frontend checks `response_code === '0'`. Returning `6005` on a successful create would be read as
> a **failure** by `fetchy.odoo.client.ts` and every existing store. **Do not define new success
> codes.**
>
> The single justified exception is **archive**, which has a live precedent in `CLIENT_ARCHIVED`.
> Archiving a pricelist gets its own code so the UI can show "archived" rather than a generic
> success. Note that in `api_delete_client`, permanent delete returns `'0'` while *soft* delete
> returns `CLIENT_ARCHIVED` — we mirror that exactly.

### 3.5 New error codes (`PricelistApiErrors` + `API_ERROR_MESSAGES`)

Numbering continues from the existing `6001` / `6002` and mirrors the shape of `BrandApiErrors`
(`NOT_FOUND` / `ID_REQUIRED` / `INVALID_ID` / `NAME_REQUIRED` / `NO_FIELDS_TO_UPDATE` / `IN_USE`).

| Code     | Constant                                                               | Message                                   | Kind                                    |
| -------- | ---------------------------------------------------------------------- | ----------------------------------------- | --------------------------------------- |
| `6001` | `PRICELIST_NOT_FOUND` *(exists)*                                   | Pricelist not found                       | Error                                   |
| `6002` | `PRICELISTS_FETCHED` *(exists, dead — leave as-is, do not reuse)* | Pricelists fetched successfully           | —                                      |
| `6003` | `PRICELIST_ID_REQUIRED`                                              | Pricelist ID is required                  | Error                                   |
| `6004` | `INVALID_PRICELIST_ID`                                               | Invalid pricelist ID format               | Error                                   |
| `6005` | `PRICELIST_NAME_REQUIRED`                                            | Pricelist name is required                | Error                                   |
| `6006` | `PRICELIST_CURRENCY_REQUIRED`                                        | Currency is required                      | Error                                   |
| `6007` | `PRICELIST_NO_FIELDS_TO_UPDATE`                                      | No valid fields to update                 | Error                                   |
| `6008` | `PRICELIST_ARCHIVED`                                                 | Pricelist archived successfully           | ✅**Success** (the one exception) |
| `6009` | `PRICELIST_IN_USE`                                                   | Pricelist is assigned to clients or tiers | Error                                   |
| `6010` | `PRICELIST_ITEM_NOT_FOUND`                                           | Price rule not found                      | Error                                   |
| `6011` | `PRICELIST_ITEM_ID_REQUIRED`                                         | Price rule ID is required                 | Error                                   |
| `6012` | `PRICELIST_ITEM_PRODUCT_REQUIRED`                                    | Product is required                       | Error                                   |
| `6013` | `PRICELIST_ITEM_PRICE_REQUIRED`                                      | Price is required                         | Error                                   |
| `6014` | `PRICELIST_ITEM_INVALID_DATE_RANGE`                                  | End date must be after start date         | Error                                   |
| `6015` | `PRICELIST_ITEM_NO_FIELDS_TO_UPDATE`                                 | No valid fields to update                 | Error                                   |

Create, update, list and item-delete all return `'0'`. Only pricelist **archive** returns `6008`.

---

## 4. Endpoint Detail — Request / Response

### 4.1 `GET /api/admin/pricelists` *(exists — reviewed, unchanged)*

Query: `page`, `limit`, `search`, `company_id`, `currency_id`, `active`

```json
{
  "response_code": "0",
  "response_message": "Success",
  "data": {
    "pricelists": [
      {
        "id": 4,
        "name": "Gold Tier Pricing",
        "active": true,
        "sequence": 10,
        "currency": { "id": 1, "name": "SAR", "symbol": "SR" },
        "company": { "id": 1, "name": "My Company" },
        "country_groups": [],
        "rules_count": 12,
        "create_date": "2026-01-05T09:12:00",
        "write_date": "2026-06-10T14:02:00"
      }
    ],
    "pagination": { "page": 1, "limit": 20, "total": 4, "pages": 1 }
  }
}
```

### 4.2 `GET /api/admin/pricelists/details?id=4` *(exists)*

```json
{
  "response_code": "0",
  "response_message": "Success",
  "data": { "pricelist": { "id": 4, "name": "Gold Tier Pricing", "active": true, "sequence": 10,
    "currency": { "id": 1, "name": "SAR", "symbol": "SR" },
    "company": { "id": 1, "name": "My Company" },
    "country_groups": [], "rules_count": 12,
    "create_date": "2026-01-05T09:12:00", "write_date": "2026-06-10T14:02:00" } }
}
```

> Not found → `{ "response_code": "6001", "response_message": "Pricelist not found" }`

### 4.3 `POST /api/admin/pricelists/create`

```json
{ "name": "Ramadan Promo 2026", "currency_id": 1 }
```

```json
{
  "response_code": "0",
  "response_message": "Success",
  "data": { "pricelist": { "id": 9, "name": "Ramadan Promo 2026", "active": true, "sequence": 10,
    "currency": { "id": 1, "name": "SAR", "symbol": "SR" }, "company": null,
    "country_groups": [], "rules_count": 0,
    "create_date": "2026-07-28T10:00:00", "write_date": "2026-07-28T10:00:00" } }
}
```

> Server sets `is_ecommerce_portal = True` on create so the record appears in the AMP list
> (the list endpoint filters on it).

### 4.4 `POST /api/admin/pricelists/update`

```json
{ "id": 9, "name": "Ramadan Promo 2026 — Extended", "currency_id": 2 }
```

```json
{ "response_code": "0", "response_message": "Success",
  "data": { "pricelist": { "id": 9, "name": "Ramadan Promo 2026 — Extended",
    "currency": { "id": 2, "name": "USD", "symbol": "$" }, "…": "…" } } }
```

### 4.5 `POST /api/admin/pricelists/delete`

```json
{ "id": 9 }
```

```json
{ "response_code": "6008", "response_message": "Pricelist archived successfully",
  "data": { "id": 9, "active": false } }
```

> ⚠️ The **only** endpoint in this feature that does not return `'0'` on success. Mirrors the live
> `CLIENT_ARCHIVED` precedent in `api_delete_client`. The frontend must treat `6008` as a success,
> not route it through the generic error handler.

### 4.6 `GET /api/admin/pricelists/items`

Query: `pricelist_id` *(required)*, `page`, `limit`, `search` *(product name)*

Field mapping — UI label → Odoo field on `product.pricelist.item`:

| UI label       | Odoo field          | Notes                                                                          |
| -------------- | ------------------- | ------------------------------------------------------------------------------ |
| Product name   | `product_tmpl_id` | Required                                                                       |
| Variant name   | `product_id`      | Optional. Set →`applied_on = '0_product_variant'`; blank → `'1_product'` |
| Price          | `fixed_price`     | `compute_price` forced to `'fixed'` in this simplified UI                  |
| Min Qty        | `min_quantity`    | Float, default 0                                                               |
| Start datetime | `date_start`      | Optional                                                                       |
| End datetime   | `date_end`        | Optional                                                                       |

```json
{
  "response_code": "0",
  "response_message": "Success",
  "data": {
    "items": [
      {
        "id": 55,
        "pricelist_id": 4,
        "product_tmpl": { "id": 120, "name": "Widget A" },
        "product_variant": { "id": 341, "name": "Red - L" },
        "price": 120.0,
        "min_quantity": 5,
        "date_start": "2026-01-01T00:00:00",
        "date_end": null
      },
      {
        "id": 56,
        "pricelist_id": 4,
        "product_tmpl": { "id": 121, "name": "Widget B" },
        "product_variant": null,
        "price": 85.0,
        "min_quantity": 10,
        "date_start": "2026-03-01T00:00:00",
        "date_end": "2026-06-30T23:59:59"
      }
    ],
    "pagination": { "page": 1, "limit": 20, "total": 2, "pages": 1 }
  }
}
```

### 4.7 `POST /api/admin/pricelists/items/create`

Called by the Add / Edit Item modal on save. `product_tmpl_id` and `product_id` are sourced from the
P1 and P2 pickers in §3.3 — note those endpoints return `product_id` and `variant_id` respectively,
which map onto `product_tmpl_id` and `product_id` here. The naming inverts; map explicitly.

```json
{
  "pricelist_id": 4,
  "product_tmpl_id": 120,
  "product_id": 341,
  "price": 120.0,
  "min_quantity": 5,
  "date_start": "2026-01-01T00:00:00",
  "date_end": null
}
```

```json
{
  "response_code": "0",
  "response_message": "Success",
  "data": { "item": { "id": 57, "pricelist_id": 4,
    "product_tmpl": { "id": 120, "name": "Widget A" },
    "product_variant": { "id": 341, "name": "Red - L" },
    "price": 120.0, "min_quantity": 5,
    "date_start": "2026-01-01T00:00:00", "date_end": null } }
}
```

### 4.8 `POST /api/admin/pricelists/items/update`

```json
{ "id": 57, "price": 115.0, "min_quantity": 10, "date_end": "2026-12-31T23:59:59" }
```

```json
{ "response_code": "0", "response_message": "Success",
  "data": { "item": { "id": 57, "price": 115.0, "min_quantity": 10,
    "date_end": "2026-12-31T23:59:59", "…": "…" } } }
```

### 4.9 `POST /api/admin/pricelists/items/delete`

```json
{ "id": 57 }
```

```json
{ "response_code": "0", "response_message": "Success", "data": { "id": 57 } }
```

---

## 5. Access Management — Steps to Register the New Screens

New portal screens are registered as **data records** inside the `access_management` module, then
granted to roles. Steps only; the XML is written during implementation.

### 5.1 How the chain works

```text
access.application  (amp / client)
   └── access.screen.category      ← menu grouping, e.g. "Products Management"
         └── access.screen         ← one portal screen; carries route `path` + `icon`
               └── access.permission   ← one action on that screen (view/create/edit/delete/custom)
                     └── access.role      ← M2M bundle of permissions, scoped to one application
                           └── access.role.assignment   ← role ↔ user
```

The portal calls `GET /amm/api/permissions?app=amp&user=<login>` and receives `roles`,
`permissions[]` (flat list of codes) and `screens[]`. **Only screens carrying a granted `view`
permission are returned** — that array drives the sidebar menu and the route guards.

### 5.2 Naming conventions (enforced by constraints)

| Record                      | Pattern                                              | Example                   |
| --------------------------- | ---------------------------------------------------- | ------------------------- |
| `access.screen.reference` | `<app_code>.<screen>` — **globally unique** | `amp.pricelists`        |
| `access.permission.code`  | `<app_code>.<screen>.<action>`                     | `amp.pricelists.create` |
| `access.screen.path`      | The real Next.js route                               | `/admin/pricelists`     |
| `access.screen.icon`      | PrimeIcons class                                     | `pi pi-dollar`          |

**Constraint that shapes the design:** only **one** standard `action_type`
(`view`/`create`/`edit`/`delete`) is allowed **per screen**; `custom` may repeat. Because Pricelists
*and* their Items each need create/edit/delete, they **must be two separate screens** — Items
registered as a **sub-screen** (`parent_id` → Pricelists). This also lets the business grant
"can view prices but not change rules" cleanly.

### 5.3 Step-by-step

**Step 1 — Reuse the existing category.** Both screens attach to the existing
`cat_amp_products` ("Products Management", `app_amp`). **No new category record.** Existing screen
sequences there are 10 (Product Categories), 20 (Products), 30 (Brands) → Pricelists takes **40**.

**Step 2 — Add two screen records** to `data/access_screen_catalogue_data.xml`:

| Screen          | reference               | path                  | parent             | category             |
| --------------- | ----------------------- | --------------------- | ------------------ | -------------------- |
| Pricelists      | `amp.pricelists`      | `/admin/pricelists` | —                 | `cat_amp_products` |
| Pricelist Items | `amp.pricelist_items` | `/admin/pricelists` | `amp.pricelists` | `cat_amp_products` |

**Step 3 — Add nine permission records** to `data/access_permission_data.xml`:

| Screen                  | Permission codes                                                 | Types                                           |
| ----------------------- | ---------------------------------------------------------------- | ----------------------------------------------- |
| `amp.pricelists`      | `.view`, `.create`, `.edit`, `.delete`, `.read_detail` | view / create / edit / delete /**custom** |
| `amp.pricelist_items` | `.view`, `.create`, `.edit`, `.delete`                   | view / create / edit / delete                   |

> `read_detail` must be `custom` — `view` is already taken by the list and only one `view` per screen
> is allowed. This matches how Orders and Clients are already modelled.

**Step 4 — Grant permissions to roles** in `data/access_role_data.xml`:

| Role                           | Grant                                                                     | Rationale                                                                                         |
| ------------------------------ | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `role_amp_super_admin`       | All 9                                                                     | Full access by definition                                                                         |
| `role_amp_pricing_manager`   | All 9                                                                     | The feature's owner role — note it is currently*read-only*; this makes it a genuine editor     |
| `role_amp_read_only_manager` | `pricelists.view`, `pricelists.read_detail`, `pricelist_items.view` | View, never change                                                                                |
| `role_amp_account_manager`   | `pricelists.view`, `pricelists.read_detail`, `pricelist_items.view` | Must*see* the price a client gets, not set it — mirrors Products being view-only for this role |

**Step 5 — Plan the data migration (critical).** `data/access_role_data.xml` loads with
`noupdate="1"`. On an already-installed database, **editing that file has no effect on upgrade** —
existing roles keep their old permission set. The screens and permissions load fine (those files are
*not* `noupdate`), but the role grants need one of:

- a migration script that appends the new permission IDs to the existing roles, **or**
- a documented manual step for an admin to tick the new permissions in the Roles screen.

*Recommendation: migration script*, so staging and production converge without manual work.

**Step 6 — Upgrade and verify.** Upgrade `access_management`, run the role migration, then call
`GET /amm/api/permissions?app=amp&user=<login>` for one user per role and confirm the Pricelists
screen appears in `screens[]` under Products Management with the right `path`/`icon`, and that
`permissions[]` holds exactly the expected codes.

**Step 7 — Consume it in the frontend.** The sidebar and the `/admin/pricelists` route guard read
from `screens[]`; each button (`New`, `Edit`, `Delete`, `Add Item`, …) is gated on its permission
code from `permissions[]`. No new frontend plumbing — the same mechanism every existing AMP screen
already uses.

### 5.4 Records to create

| Model                      | Count | Notes                                              |
| -------------------------- | ----- | -------------------------------------------------- |
| `access.application`     | 0     | Reuse`app_amp`                                   |
| `access.screen.category` | 0     | Reuse`cat_amp_products`                          |
| `access.screen`          | 2     | `amp.pricelists` + child `amp.pricelist_items` |
| `access.permission`      | 9     | 5 on Pricelists, 4 on Items                        |
| `access.role`            | 0 new | 4 existing roles updated via migration (Step 5)    |

---

## 6. Implementation Sequence

Work is tracked as backlog stories in `042_pricelist_management_backlog.md`
(`AMP-PL >> 01.1` … `AMP-PL >> 04.2`). The order below is the dependency order, not a schedule.

```text
01  Access Foundation          ── screens + permissions + role grants
      │                           (independent of the API — can run in parallel)
      ▼
02  Pricelist Directory        ── list & search → create → edit → retire
      │
      ▼
03  Detail & Price Rules       ── detail view → rules list → add → edit → remove
      │
      ▼
04  Release Readiness          ── per-role verification → API docs & Postman
```

**Build order within a story:** error codes → model method → controller route → frontend types →
store action → component. The response shape in §4 is the contract; agree it before either side
starts so backend and frontend can proceed in parallel.

**Critical path:** routes 3–5 unblock the list view; route 6 unblocks the rules table; routes 7–9
unblock the item modal. The access-management records (epic 01) sit off the critical path — since
permissions gate the UI only (decision #3), they can land at any point before release readiness
without blocking feature work.

**Parallelisation:** backend and frontend can work the same story simultaneously once §4 is signed
off. Epic 01 is a backend-only stream that never blocks epics 02–03.

# Product Grid Listing: Switch from Templates to Variants (Study + Side Effects + Plan)

## 1) Goal (Why we want this)
Today the portal product grid lists **product templates** (`product.template`). That is simple, but users sometimes want to see what they can actually buy (the **variant**: `product.product`), especially when:
- Each variant has different availability or barcode/internal reference.
- Each variant can have a different image.
- The “best” variant to buy is not always the first variant.

**Target change**: Make the product grid able to list **variants** while keeping the **same response structure** used by the frontend today.


## 2) Current flow (what exists now)
### Frontend
- Product grid calls `productService.listProducts()`.
- Service calls `POST /ecommerce/api/products` with JSON body (page, page_size, public_categ_ids, brand_ids, tag_ids, attrs, …).

### Backend (Odoo)
- Controller: `POST /ecommerce/api/products`
- Model method: `product.template.get_products_payload()`
- Response is a list of “products” where each item is built from a `product.template` record.


## 3) What “listing variants” actually means
If we list `product.product`, we have two possible UX meanings:

### Option A (Recommended for minimal frontend changes): “Variant-powered template cards”
We still return **one card per template**, but we choose the “best variant” behind the scenes and use it for:
- image (variant image if exists)
- first_variant_id (becomes the chosen variant)
- optional extra fields later (barcode, default_code) if the UI needs them

This keeps the same user experience (one card per product) but improves correctness.

### Option B (True variant grid): “One card per variant”
We return one item per `product.product`. This gives maximum detail and is great for catalogs where each variant is treated as a separate sellable item.

This option usually requires frontend changes because:
- A template details page `/products/[id]` currently expects template id.
- “Filters” UX can feel duplicated (many variants of same template).

Because you requested “keep same response structure” and “make most changes in backend”, **Option A is the safest** starting point.


## 4) Side effects / risks (what can break or change)
This is the checklist to understand before implementing.

### A) Functional behavior changes
- **Duplicates** (Option B): templates with many variants will appear many times.
- **Featured flag**: `is_featured_product` is on template; variant list must still respect it via `product_tmpl_id`.
- **Website sequence**: sorting uses template `website_sequence`; variant list must sort using `product_tmpl_id.website_sequence`.
- **Categories, tags, brand**: these are template-level fields; variant domain must filter via `product_tmpl_id.*`.

### B) Compatibility with existing frontend routes
Today response contains:
- `product_id` (template id)
- `first_variant_id` (variant id)

If we change `product_id` to a variant id (Option B), the portal pages that open product details will likely break until we update:
- `/ecommerce/api/product` (details endpoint)
- Next.js routes/components that use `product_id`

So for “backend-only” change, keep:
- `product_id = template_id`
- `first_variant_id = chosen_variant_id`

### C) Pricing side effects
Your current pricing helper uses template logic (`_get_configurator_display_price` + template list_price conversion).
When listing variants:
- Some pricelist rules can target `product.product` directly.
- If you use “variant-powered template cards”, price can be:
  - template price (as today), OR
  - chosen variant price (more accurate when variant rules exist)

Recommendation:
- Start by keeping the pricing logic consistent with today (template-based).
- Add a later enhancement to compute variant price if you decide to show variant-level price.

### D) Performance side effects
Variant counts can be much larger than templates.
- Searching variants with large page_size can become heavier.
- Building filters (tags/brands/attributes) should be based on the **visible product set**. With variants, always decide if “visible set” means:
  - variants set, or
  - templates set derived from variants

Recommendation:
- For Option A, search variants only to pick the best variant per template, but keep template pagination stable.
- For Option B, reduce default page_size and rely on lazy load more.

### E) Attribute filtering logic changes
Current attribute filtering is template-oriented (walk template → variants → values).
For variants it becomes simpler:
- Filter directly using `product_template_variant_value_ids.product_attribute_value_id`.

But if you still display one card per template (Option A), you must decide:
- do we return templates that have **any** variant matching attributes? (usually yes)

### F) Image behavior
Variant may have its own image. If not, we must fall back to template.
- Backend already supports serving images for both models using:
  - `/ecommerce/api/image/product.product/<id>/image_1920`
  - `/ecommerce/api/image/product.template/<id>/image_1920`


## 5) Backend design to support switching (template vs variant) with minimal disruption
Add a single optional request parameter in the JSON body, for example:
- `list_mode`: `"template"` (default) or `"variant"`

This keeps:
- Same endpoint: `POST /ecommerce/api/products`
- Same response keys
- Most changes isolated to Odoo backend

Suggested payload example:
```json
{
  "page": 0,
  "page_size": 21,
  "public_categ_ids": [1],
  "brand_ids": [2],
  "tag_ids": [3],
  "attrs": "1:10,11|2:22",
  "list_mode": "variant"
}
```

### Behavior by list_mode
- `list_mode="template"`: current behavior (use `product.template` search).
- `list_mode="variant"`:
  - Option A: variant-powered template cards (recommended)
  - Option B: true variant grid (possible later)


## 6) Variant Mode — Field Source & Fallback Rules

**Rule:**  
Read from `product.product` first. If empty, fallback to `product_tmpl_id`.

**Purpose:**  
Keep the same response structure while clearly defining data source priority.

---

### Field Mapping

| Response Key | Variant Source (`product.product`) | Fallback (Template) | Notes |
|-------------|------------------------------------|---------------------|-------|
| `product_id` | `product_tmpl_id.id` | N/A | Keep template ID for compatibility |
| `slug` | `slug(template)` | N/A | Slug is safer at template level |
| `name` | `display_name` | `name` | Variant `display_name` includes attributes |
| `display_name` | `display_name` | `display_name` | Same logic |
| `is_published` | N/A | `is_published` | Template-level |
| `is_featured_product` | N/A | `is_featured_product` | Template-level |
| `need_call` | N/A | `need_call` | Template-level |
| `website_sequence` | N/A | `website_sequence` | Template-level |
| `image_url` | Variant image (if exists) | Template image | Use `/ecommerce/api/image/...` |
| `public_categ_ids` | N/A | `public_categ_ids.ids` | Template-level |
| `tags` | N/A | `product_tag_ids.ids` | Template-level |
| `description_sale` | N/A | `description_sale` | Template-level |
| `first_variant_id` | `id` (selected variant) | N/A | Chosen variant |
| `variant_count` | `len(product_tmpl_id.product_variant_ids)` | N/A | From template |
| `price` / `list_price` / `discount_percent` | Variant pricing (optional) | Template pricing | Start with template pricing |
| `ribbon` | N/A | `website_ribbon_id.name` | Template-level |

---

## 7) Search feature (keep same pattern, but works in both modes)
Today the portal search is mostly client-side (frontend filters the loaded list).
If we want server-side search while keeping the same request/response pattern, add:
- `search_term` in request body

Recommended search domain:
- Template mode: match `name` and `description_sale`.
- Variant mode: match `display_name`, and also `default_code` / `barcode` on variant if you want more power.

Important: keep the key name the same (`search_term`) in both modes so the frontend does not care.


## 8) Implementation steps (simple plan for junior dev)
This is the suggested implementation sequence with minimal risk.

### Step 1: Add `list_mode` parameter (no behavior change by default)
- In `get_products_payload`, read `list_mode = data.get("list_mode") or "template"`.
- If `list_mode == "template"` keep existing logic untouched.

### Step 2: Implement variant-mode domain builder (filters still behave the same)
Create a helper that returns a variant domain equivalent to template filters:
- Base conditions come from template fields using `product_tmpl_id.*`:
  - `sale_ok`, `is_published`, `service_tracking`
  - `public_categ_ids`, `brand_id`, `product_tag_ids`
- Attribute filters use variant field:
  - `product_template_variant_value_ids.product_attribute_value_id`

### Step 3 (Option A): Pick “best variant” per template
For each template, choose one variant to represent it:
- Prefer “first possible variant” logic if you already trust it
- Or choose the first active variant in the filtered set

Return one item per template, but set:
- `first_variant_id = chosen_variant.id`
- `image_url` uses chosen variant image if present

### Step 4: Pricing decision
Choose one:
- Keep template pricing (stable; easiest).
- Or compute pricing based on the chosen variant (more accurate; extra work).

### Step 5: Filters in response (brands/tags/attributes)
Keep the current behavior:
- filters are computed from the “visible set”

In variant mode (Option A), “visible set” should still represent templates (not raw variants) so the UI filters do not explode.

### Step 6: Regression test checklist (manual)
- Product grid loads same as before in template mode.
- Variant mode returns same JSON keys and renders without frontend changes.
- Category/brand/tag/attrs filters still work.
- Images load for variants and fall back to template.
- Pagination still works.


## 9) Recommended decision summary
- Implement `list_mode` switch in backend.
- Start with variant mode Option A (variant-powered template cards).
- Keep response structure stable by keeping `product_id` as template id and using `first_variant_id` as the chosen variant id.
- Add true variant grid (Option B) later only if UX requires it, because it will need coordinated frontend updates.


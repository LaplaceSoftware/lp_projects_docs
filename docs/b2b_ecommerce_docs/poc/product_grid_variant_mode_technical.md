# Product Grid Variant Mode (Technical Notes)

## Problem & Target Solution
### Problem
The portal product grid was listing `product.template` only. In B2B, this creates UX issues because:
- Users often buy a specific variant (size/color/etc.), not just the template.
- Variants can differ in display name, SKU/barcode, image, and pricing rules.
- Showing only templates hides the “real purchasable item”.

### Target Solution
Keep the same endpoint and response structure, but allow listing **one card per variant**.
- Endpoint stays: `POST /ecommerce/api/products`
- Add request parameter: `list_mode`
  - `template` (default): existing behavior
  - `variant`: new behavior (Option B) — list from `product.product`


## Response Structure Field Mapping (Template vs Variant)
Rule in `list_mode="variant"`:
- Read variant fields first.
- If a value is not available on the variant, fallback to `product_tmpl_id`.
- Keep `product_id` as the template id for compatibility with existing `/products/[id]` pages.

| Response Key | Template Mode Source (`product.template`) | Variant Mode Source (`product.product`) | Variant Fallback | Notes |
|---|---|---|---|---|
| `product_id` | `id` | `product_tmpl_id.id` | N/A | Keeps existing routing `/products/${product_id}` |
| `slug` | slug(template) | slug(template) | N/A | Uses template slug |
| `name` | `name` | `display_name` | `product_tmpl_id.name` | Variant name includes attributes |
| `display_name` | `display_name` | `display_name` | `product_tmpl_id.display_name` | Same idea |
| `is_published` | `is_published` | `product_tmpl_id.is_published` | N/A | Template-level |
| `is_featured_product` | `is_featured_product` | `product_tmpl_id.is_featured_product` | N/A | Template-level |
| `need_call` | `need_call` | `product_tmpl_id.need_call` | N/A | Template-level |
| `website_sequence` | `website_sequence` | `product_tmpl_id.website_sequence` | N/A | Template-level ordering |
| `image_url` | template image | variant image (if used) | template image | Served via `/ecommerce/api/image/...` |
| `public_categ_ids` | `public_categ_ids.ids` | `product_tmpl_id.public_categ_ids.ids` | N/A | Template-level |
| `tags` | `product_tag_ids.ids` | `product_tmpl_id.product_tag_ids.ids` | N/A | Template-level |
| `description_ecommerce` | `description_ecommerce` | `product_tmpl_id.description_ecommerce` | N/A | Template-level |
| `description_sale` | `description_sale` | `product_tmpl_id.description_sale` | N/A | Template-level |
| `first_variant_id` | `_get_first_possible_variant_id()` | `id` | N/A | In variant mode this is the variant record id |
| `variant_count` | `len(product_variant_ids)` | `len(product_tmpl_id.product_variant_ids)` | N/A | Template-level |
| `currency` | computed | computed | N/A | Same currency rules |
| `list_price` | computed | computed from `variant.lst_price` | N/A | Variant-aware |
| `price` | computed | computed from pricelist (variant) | N/A | Variant-aware |
| `discount_percent` | computed | computed | N/A | Variant-aware |
| `ribbon` | `website_ribbon_id.name` | `product_tmpl_id.website_ribbon_id.name` | N/A | Template-level |


## Backend Changes (Odoo)
### Key idea
Variant-specific logic is moved into the `product.product` model (clean separation and DRY).

### Method Mapping (New / Refactored)
| Method | Model | Purpose |
|---|---|---|
| `_public_variant_base_domain()` | `product.product` | Base visibility rules for variant listing (active + template sale_ok + published + tracking types). |
| `_build_products_domain_variant(...)` | `product.product` | Apply filters (category/brand/tag/attrs/product_ids) in variant terms using `product_tmpl_id.*` relations. |
| `_restricted_variant_domain(base_domain, partner_pl, restrict)` | `product.product` | Pricelist restriction for variants (supports rules applied to templates, variants, and categories). |
| `_compute_variant_prices(variants, currency, pricelist)` | `product.product` | Compute `price`, `list_price`, `discount_percent` per variant. |
| `_prepare_variant_product_dict(variant, currency, pricing)` | `product.product` | Build the API response item in the same structure expected by the frontend grid. |

### Where it is used
`product.template.get_products_payload()` decides the mode:
- If `list_mode="template"`: uses existing template search flow.
- If `list_mode="variant"`: uses `product.product` helpers for domain, restriction, pricing, and response mapping.

### Important consideration: ordering
Odoo ORM does not support `order='product_tmpl_id.website_sequence'` on `product.product`.
For B2B catalogs under ~1000 items, we sort in Python using:
- template `website_sequence`
- template id
- variant id


## Key Considerations / Challenges
| Issue | What we did |
|---|---|
| Duplicate React keys in grid/search | Use `first_variant_id` as React key (unique per variant). |
| Image endpoint 500 (mimetype detection) | Updated `/ecommerce/api/image/...` controller to use `ir.binary._get_image_stream_from(...)` so `download_name`/`mimetype` are set and placeholder images work. |
| Pricelist restrictions in variant mode | Build allowed variants from pricelist items (variant rules + template rules + category rules). |
| Keeping existing product details route | Keep `product_id` as template id; variant id is returned in `first_variant_id`. |


## Frontend Changes
| File | Change |
|---|---|
| `products.service.ts` | Send `list_mode: "variant"` in body when loading the grid list. |
| `ProductGrid.tsx` | Use `key={product.first_variant_id ?? product.product_id}` for list rendering. |
| `ProductSearch.tsx` | Same key fix for dropdown results. |


## Postman Update
Collection updated to V11.0 and “Products List” request changed to:
- Method: `POST`
- Body includes: `"list_mode": "variant"`


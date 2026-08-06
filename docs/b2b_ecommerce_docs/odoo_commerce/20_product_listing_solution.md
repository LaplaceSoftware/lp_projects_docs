# Product Listing REST API (Technical Proposal)

## Objective
- Define REST endpoints and parameters for Next.js product listing.
- Implementation strictly uses existing Odoo functions, fields, and session objects referenced below.

## Endpoint: GET /api/shop
- Method: GET
- Query Params
  - `search`: string (full-text search)
  - `category_id`: integer (website public category id)
  - `attribute_values[]`: list of strings (ids as strings; mirrors session use)
  - `tags`: comma-separated slugs (customer-visible product tags)
  - `min_price`: float (converted from website currency context)
  - `max_price`: float (converted from website currency context)
  - `order`: string (uses website default if absent)
  - `page`: integer
  - `page_size`: integer (ppg; falls back to `website.shop_ppg`)
  - `display_currency`: id (optional; otherwise uses `website.currency_id`)
- Session Context
  - `request.cart`, `request.pricelist`, `request.fiscal_position` established by website layer `addons/website_sale/models/ir_http.py:32`
- Processing Steps
  - Determine sort order via `_get_search_order(post)` `addons/website_sale/controllers/main.py:148`
  - Build product domain via `_get_shop_domain(search, category, attribute_value_dict)` `addons/website_sale/controllers/main.py:157`
  - Perform fuzzy product lookup via `website._search_with_fuzzy("products_only", search, order, options)` `addons/website_sale/controllers/main.py:243`
  - Compute available min/max list prices on current domain using `_search(domain)` and SQL `MIN/MAX(list_price)` `addons/website_sale/controllers/main.py:386`
  - Aggregate visible attribute groups using `_read_group` on `product.template.attribute.line` `addons/website_sale/controllers/main.py:462`
  - Filter customer-visible tags via `product.tag.search_fetch` domain `visible_to_customers` and published products `addons/website_sale/controllers/main.py:408`
  - Map templates to first variant ids via `_get_first_possible_variant_id()` `addons/website_sale/controllers/main.py:454`
  - Compute display price per product with taxes mapped via `_get_configurator_display_price` `addons/website_sale/models/product_template.py:985`
- Response
  - `products`: array of items with fields below
  - `pager`: `{ page, page_size, total }`
  - `filters`: `{ min_price, max_price, attributes, tags, categories }`
  - `sort`: `{ order_key }`
  - `currency`: `website.currency_id`

### Product Item Fields
- Identity
  - `product_id`: `product.template.id`
  - `slug`: `ir.http._slug(product)`
  - `product_type`: `product.template.type`
- Display
  - `name`: `product.template.name`
  - `display_name`: `product.template.display_name`
  - `is_published`: `product.template.is_published`
  - `website_sequence`: `product.template.website_sequence`
  - `ribbon_id`: `product.template.website_ribbon_id`
  - `image_url`: `/web/image/product.template/<id>/image_1920`
- Categories & Tags
  - `public_categ_ids`: `product.template.public_categ_ids`
  - `tags`: `product.template.product_tag_ids`
- Variants & Attributes
  - `first_variant_id`: result of `_get_first_possible_variant_id()` `addons/website_sale/controllers/main.py:454`
  - `variant_count`: length of `product.product_variant_ids`
  - `visible_attributes`: grouped from `_read_group` `addons/website_sale/controllers/main.py:462`
- Pricing
  - `currency`: `website.currency_id`
  - `price`: `_get_configurator_display_price(product_or_template, quantity=1, date, currency, pricelist)` `addons/website_sale/models/product_template.py:985`
  - `list_price`: `product.template.list_price` (converted to `currency` if needed)
  - `has_discounted_price`: determined by comparing base price and display price when pricelist rule shows discount, following listing logic analogous to `sale.order.line._get_display_price_ignore_combo` and `_compute_discount` `addons/sale/models/sale_order_line.py:656`, `addons/sale/models/sale_order_line.py:784`

## Options Construction
- Build `options` for fuzzy search using `_get_search_options(...)` `addons/website_sale/controllers/main.py:218`
  - `displayDescription`, `displayDetail`, `displayExtraDetail`, `displayExtraLink`, `displayImage`
  - `allowFuzzy`: inverse of `noFuzzy`
  - `category`: category id as string
  - `tags`: parsed from query
  - `min_price` and `max_price`: normalized by `conversion_rate`
  - `attribute_value_dict`: parsed from `attribute_values[]`
  - `display_currency`: forwarded to pricing

## Filtering Data
- Price range
  - Compute available min/max list_price via query on `_search(domain)` `addons/website_sale/controllers/main.py:386`
  - Convert using `res.currency._get_conversion_rate` to `website.currency_id` `addons/website_sale/controllers/main.py:353`
- Attributes
  - Group attribute lines using `_read_group` over search results `addons/website_sale/controllers/main.py:462`
- Tags
  - Domain includes `visible_to_customers` and published products with `website_domain` `addons/website_sale/controllers/main.py:408`
- Categories
  - Derive visible categories via `product.public.category.search_fetch` with `website_domain` and published flag for non-internal users `addons/website_sale/controllers/main.py:424-446`

## Sorting & Pagination
- Sort order from `_get_search_order(post)` and website `shop_default_sort` `addons/website_sale/controllers/main.py:148`
- Page size from `website.shop_ppg` and columns per row `website.shop_ppr` `addons/website_sale/controllers/main.py:316-318`
- Pager construction via `website.pager(...)` to compute offsets `addons/website_sale/controllers/main.py:449-451`

## Tax Display Alignment
- For listing, align price display with website preference by computing mapped taxes on configurator price `addons/website_sale/models/product_template.py:985`, consistent with line-level display mapping `addons/website_sale/models/sale_order_line.py:52`

## Session & Context
- Use `request.cart`, `request.pricelist`, `request.fiscal_position` provided lazily `addons/website_sale/models/ir_http.py:32`
- Refresh cached pricelist periodically and when promo changes as in `_apply_pricelist` `addons/website_sale/controllers/main.py:968`

## Implementation in New Module
- Module: `addons_lp_ecommerce/ecommerce`
- Endpoint: `GET /ecommerce/api/shop`
- Depends: `website_sale`
- Behavior:
  - Builds domain with `request.website.sale_product_domain()`, search terms, category child-of, and `product.template._get_attribute_value_domain(attribute_value_dict)`.
  - Orders with `is_published desc, <order>, id desc` aligned with website default sort.
  - Computes prices via `product.template._get_configurator_display_price(product_or_template, quantity=1, date, currency, pricelist)` with `currency=website.currency_id` and `pricelist=request.pricelist`.
  - Converts `list_price` using `product.currency_id._convert(..., website.currency_id, website.company_id, fields.Date.today(), round=False)`.
  - Aggregates visible attributes via `_read_group` on `product.template.attribute.line`.

### Usage from Browser
- Example:
  - `/ecommerce/api/shop?search=desk&category_id=12&page=0&page_size=21&order=name&attribute_value_dict={"34":["101","102"]}`
- Response:
  - JSON containing `products`, `pager`, `filters` (min/max, attributes), `sort`, `currency`.

## Simplified Endpoint for External Integration
- Endpoint: `GET /ecommerce/api/product_list`
- Purpose: provide a minimal product list for external Next.js portal, returning published products with pricing and basic fields.
- Params:
  - `page`: integer, default `0`
  - `page_size`: integer, default from `website.shop_ppg`
  - `display_currency`: currency id; defaults to `website.currency_id`
  - `pricelist_id`: product pricelist id; defaults to `request.pricelist`
- Data Source:
  - Domain: `request.website.sale_product_domain()`
  - Pricing: `product_template._get_configurator_display_price(product_or_template, 1, date, currency, pricelist)`
  - Base price: `product.template.list_price` converted using `currency._convert`
- Response Item Fields:
  - `product_id`, `slug`, `name`, `display_name`, `is_published`, `website_sequence`
  - `image_url`, `public_categ_ids`, `tags`
  - `description_ecommerce`, `description_sale`
  - `first_variant_id`, `variant_count`
  - `currency_id`, `list_price`, `price`, `discount_percent`
- Example:
  - `/ecommerce/api/product_list?page=0&page_size=21&pricelist_id=1&display_currency=1`

## Implementation (New Module: ecommerce)
- Location: `addons_lp_ecommerce/ecommerce`
- Dependencies: `website_sale`
- Endpoint: `GET /ecommerce/api/shop`
- Controller: `ecommerce.controllers.api.EcommerceApi.shop`
- Behavior:
  - Builds domain with website sale domain, search string (`name`, `variants_default_code`, `website_description`, `description_sale`), optional `category_id` child-of and `attribute_value_dict` via `product.template._get_attribute_value_domain`.
  - Orders by website default sort using `'is_published desc, <order>, id desc'`.
  - Paginates using `page` and `page_size` (defaults from website).
  - Computes per-product price via `product_template._get_configurator_display_price(product_or_template, quantity=1, date, currency, pricelist)` and converted `list_price`.
  - Returns JSON: products, pager, filters (min/max price, attributes), sort and currency.

### Usage (Browser)
- Example:
  - `/ecommerce/api/shop?search=chair&category_id=12&page=0&page_size=21&order=list_price%20asc`
  - With attribute filters: `/ecommerce/api/shop?attribute_value_dict={"10":["45","46"]}`
  - Specify currency: `/ecommerce/api/shop?display_currency=1`
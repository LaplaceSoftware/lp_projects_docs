# Shop Product Listing (Data & API Analysis)

## Goal
- Define the data required to implement Next.js shop listing equivalent to Odoo’s `/shop`.
- Focus on what to fetch and how to compute it using existing Python logic.
- Deliver an API-oriented plan to prepare all data (no QWeb details).

## Core Listing Data
- Product identity
  - `id`, `product_tmpl_id`, `slug` (build via `ir.http._slug`), `type` (`product`, `service`, `combo`)
- Display fields
  - `name`, `display_name`, `website_description` excerpt, `website_sequence`, `is_published`, `website_ribbon_id`
  - Main image URL (`/web/image/product.template/<id>/image_1920`) and gallery if needed
- Categorization
  - `public_categ_ids` (website categories), `categ_id` (backend category)
  - Breadcrumb/meta: parent/child categories
- Tags
  - `product_tag_ids` visible to customers
- Variant info
  - First possible variant id, number of variants, attribute lines (visible only)
  - No-variant and custom attribute support
- Pricing
  - Final unit price (currency-aware), list price for strikethrough when discounted
  - Currency and website tax display preference (excluded/included)
  - Discount percent when rule shows discount
- Filters/meta
  - Available min/max price range for current domain (converted to website currency)
  - Attribute filter groups and values for the current product set
  - Sorting key (default from website), page/page size

## How To Fetch (Python Logic)
- Domain construction
  - Use `WebsiteSale._get_shop_domain(search, category, attribute_value_dict)` to combine:
    - Website sale product domain `addons/website_sale/controllers/main.py:157`
    - Search text across `name`, `variants_default_code`, optionally `website_description` and `description_sale` `addons/website_sale/controllers/main.py:161-169`
    - Category filter via `public_categ_ids` child-of `addons/website_sale/controllers/main.py:175-177`
    - Attribute filters via `_get_attribute_value_domain` `addons/website_sale/controllers/main.py:178-181`
- Product search & ordering
  - Perform fuzzy-aware product lookup via `website._search_with_fuzzy("products_only", search, order, options)` `addons/website_sale/controllers/main.py:243-251`
  - Order from `_get_search_order(post)` which uses website’s `shop_default_sort` `addons/website_sale/controllers/main.py:148-153`
- Price range (filters UI)
  - Compute min/max available prices with a single SQL on `_search(domain)` and `MIN/MAX(list_price)` converted to website currency `addons/website_sale/controllers/main.py:386-393`
- Attributes for filtering
  - Read visible attribute groups using `_read_group` on `product.template.attribute.line` over the full result set `addons/website_sale/controllers/main.py:462-471`
- Tags for filtering
  - `product.tag.search_fetch` with domain `visible_to_customers` and having published products `addons/website_sale/controllers/main.py:408-417`
- Variants and first variant mapping
  - Map `product.template` to first possible `product.product` id via `_get_first_possible_variant_id()` and prefetch them for performance `addons/website_sale/controllers/main.py:454-458`
- Pricing per card (tax-aware)
  - Use `product_template._get_configurator_display_price(product_or_template, quantity, date, currency, pricelist)` which applies fiscal position tax mapping and returns priced amount plus the applied rule id `addons/website_sale/models/product_template.py:985-1013`
  - For strikethrough price and discount visibility, rely on pricelist rule behavior (show discount) and compute list price vs discounted price similar to `sale.order.line._get_display_price_ignore_combo` and `_compute_discount` when needed `addons/sale/models/sale_order_line.py:656-675`, `addons/sale/models/sale_order_line.py:784-815`
- Tax display preference
  - Align unit price with website setting `show_line_subtotals_tax_selection` (tax excluded/included) as in line-level method; for listing, apply the configurator price with mapped taxes to produce either excluded or included amount per the preference `addons/website_sale/models/sale_order_line.py:52-60`

## API Controller: GET /api/shop
- Query params
  - `search`, `category_id`, `attribute_values[]`, `tags`, `min_price`, `max_price`, `order`, `page`, `page_size`, `display_currency`
- Steps
  - Resolve session context: `request.pricelist` and `request.fiscal_position` (website-layer caching)
  - Build domain using `_get_shop_domain`
  - Lookup products with fuzzy search and requested order via `_search_with_fuzzy`
  - Compute available min/max price via SQL on the current domain and convert to `display_currency`
  - Read visible attribute groups for filters via `_read_group`
  - Fetch tags domain for the current website and search set
  - Prefetch first variant ids to enrich listing items
  - For each product:
    - Identify: `id`, `slug`, `type`, `is_published`, `website_sequence`, `website_ribbon_id`
    - Display: `name`, `display_name`, image URL(s), short description excerpt
    - Categories: `public_categ_ids`, hierarchy (parent/child) for breadcrumbs
    - Tags: `product_tag_ids`
    - Pricing:
      - `price`: configurator display price (quantity=1) with taxes mapped per website preference
      - `list_price`: base/list price in the same currency
      - `has_discounted_price`: boolean (when pricelist rule reduces price and rule indicates discount visibility)
      - `currency`: `website.currency_id`
    - Variants:
      - `first_variant_id`, `variant_count`
      - Visible attribute lines/values for UI filters
- Response
  - `{ products: [...], pager: { page, page_size, total }, filters: { min_price, max_price, attributes, tags, categories }, sort: { order_key }, currency }`

## Data Field Map (Product Item)
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
  - `first_variant_id`: via `_get_first_possible_variant_id()` `addons/website_sale/controllers/main.py:454-458`
  - `variant_count`: `len(product.product_variant_ids)`
  - `visible_attributes`: `_read_group` aggregation result `addons/website_sale/controllers/main.py:462-471`
- Pricing
  - `currency`: `website.currency_id`
  - `price`: `_get_configurator_display_price(..., pricelist=request.pricelist)` `addons/website_sale/models/product_template.py:985-1013`
  - `list_price`: `product.template.list_price` converted to `currency` if needed
  - `has_discounted_price`: compare list price vs display price when pricelist rule shows discount

## Notes
- Always apply website’s ecommerce access and publish flags through `request.website.sale_product_domain()` `addons/website_sale/controllers/main.py:158`.
- When `prevent_zero_price_sale` is enabled, hide products with contextual price of zero unless product type is allowed (service types) `addons/website_sale/models/product_template.py:978-983`.
- For performance, use `with_context(bin_size=True)` when fetching binary image fields `addons/website_sale/controllers/main.py:249-251`.
# B2B Product Listing — Scalability Feature Map

## Scope
- Document features to scale a basic product_list endpoint into a robust B2B e-commerce shop listing.
- Uses existing Odoo constructs only (fields, methods, controllers, models).
- No implementation; feature checklist with references.

## Pricing & Currency
- Pricelist-driven pricing per session or explicit parameter
  - Use `request.pricelist` caching `addons/website_sale/models/website.py:699` and partner default `property_product_pricelist` `addons/website_sale/models/website.py:730`.
  - Compute UI price via `_get_configurator_display_price` `addons/website_sale/models/product_template.py:985-1013`.
- Currency normalization
  - Default to `website.currency_id`; support `display_currency` conversion `addons/website_sale/controllers/main.py:353`.
- Discount visibility
  - Compare `list_price` vs configurator price for rule-based discounts `addons/sale/models/sale_order_line.py:656`, `addons/sale/models/sale_order_line.py:784`.
- Tax display alignment
  - Map product taxes through fiscal position (`request.fiscal_position`) while computing display price `addons/website_sale/models/product_template.py:1005-1012`, `addons/website_sale/models/website.py:739`.

## Catalog Visibility
- Base saleable domain
  - `('sale_ok', '=', True)` `_product_domain()` `addons/website_sale/models/website.py:663-665`.
- Public/portal publish constraint
  - `('is_published', '=', True)` included in public user domain `addons/website_sale/models/website.py:657-661`.
- Service tracking gate
  - `('service_tracking', 'in', env['product.template']._get_saleable_tracking_types())` `addons/website_sale/models/website.py:657-661`, base types via `addons/sale/models/product_template.py:225-232`.
- Multi-website scoping (optional)
  - `website_domain()` for per-website visibility `addons/website_sale/models/website.py:653`.

## Variants & Attributes
- First possible variant id
  - `_get_first_possible_variant_id()` `addons/website_sale/controllers/main.py:454-458`.
- Attribute filters and visibility groups
  - `_get_attribute_value_domain` and `_read_group` on `product.template.attribute.line` `addons/website_sale/controllers/main.py:178-181`, `addons/website_sale/controllers/main.py:462-471`.
- Attribute extras in price context
  - `_get_product_price_context` and contextual pricing for variant/template `addons/product/models/product_product.py:785`, `addons/product/models/product_template.py:648`.

## Media & Content
- Images
  - `/web/image/product.template/<id>/image_1920` with `bin_size=True` for performance `addons/website_sale/controllers/main.py:249-251`.
- Descriptions
  - `description_ecommerce` (long), `description_sale` (quotation line default) `addons/website_sale/models/product_template.py:1040-1044`, `addons/product/models/product_product.py:852`.
- Ribbons
  - `website_ribbon_id` and auto-assign ribbons via applicability `addons/website_sale/models/product_template.py:1044-1073`.

## Tags & Categories
- Website categories
  - `public_categ_ids` for breadcrumbs and filtering `addons/website_sale/controllers/main.py:274`, `addons/website_sale/controllers/main.py:421`.
- Product tags (customer-visible)
  - `product_tag_ids` with tag search filtering `addons/website_sale/controllers/main.py:408-417`.

## Filtering & Sorting
- Simple search
  - Text search across `name`, `variants_default_code`, `website_description`, `description_sale` `addons/website_sale/controllers/main.py:161-169`.
- Ordering defaults
  - `website.shop_default_sort` via `_get_search_order` `addons/website_sale/controllers/main.py:148-153`.
- Price range filters
  - Min/max `list_price` derived from current domain, converted to display currency `addons/website_sale/controllers/main.py:386-393`.

## Pagination & Pager
- Page size defaults
  - `website.shop_ppg` and `website.shop_ppr` `addons/website_sale/controllers/main.py:316-318`.
- Pager offsets
  - `website.pager(...)` `addons/website_sale/controllers/main.py:449-451`.

## Security & Access Control
- eCommerce access gate
  - `has_ecommerce_access()` for anonymous vs logged-in access `addons/website_sale/models/website.py:1012-1015`.
- Partner-specific catalog restrictions
  - Implement record rules for `product.template`/`product.product` to limit by partner or group; endpoint must honor record rules consistently.

## Stock & Availability (Optional Integration)
- Base shop does not hard-block by stock; integrate availability from stock modules later as needed.
- Use `qty_available`, `virtual_available` via stock models; keep outside core listing for performance.

## B2B Enhancements (Progressive)
- Partner-based pricing defaults
  - `res.partner.property_product_pricelist` `addons/website_sale/models/website.py:730`.
- Contract/milestone services via `service_tracking`
  - Respect service variants requiring project/task/event flows `addons/sale_project/models/product_template.py:22-32`, `addons/event_product/models/product_template.py:7`, `addons/website_sale_slides/models/product_template.py:10`.
- Minimum order quantities, pack sizes
  - Use UoM and packaging (`uom_id`, `uom_ids`) `addons/product/models/product_template.py:117-121`.
- Multi-company constraints
  - Avoid cross-company product restrictions when historically sold elsewhere `addons/sale/models/product_template.py:108-133`.

## Performance & Caching
- Fuzzy search and options
  - `_search_with_fuzzy("products_only", ...)` and `_get_search_options` `addons/website_sale/controllers/main.py:243-251`, `addons/website_sale/controllers/main.py:218`.
- Prefetch + bin_size
  - Use `with_context(bin_size=True)` for images and prefetch variant relations `addons/website_sale/controllers/main.py:249-251`.
- SQL-derived aggregates
  - Compute price bounds from `_search(domain)` with SQL `MIN/MAX(list_price)` `addons/website_sale/controllers/main.py:386-393`.

## Data Shape (Listing Item)
- Identity
  - `id`, `slug` `addons_lp_ecommerce/ecommerce/controllers/api.py:131-135`.
- Publish & sequence
  - `is_published`, `website_sequence` `addons/website_sale/models/website.py:657-661`.
- Display
  - `name`, `display_name`, `image_url`, `description_ecommerce`, `description_sale` `addons/website_sale/models/product_template.py:1040-1044`.
- Categorization & tags
  - `public_categ_ids`, `product_tag_ids` `addons/website_sale/controllers/main.py:408-417`, `addons/website_sale/controllers/main.py:421`.
- Variants
  - `first_variant_id`, `variant_count`, visible attributes `addons/website_sale/controllers/main.py:454-471`.
- Pricing
  - `list_price`, `price`, `discount_percent`, `currency` `addons/website_sale/models/product_template.py:985-1013`.

## Progressive Roadmap
- Phase 1: Basic listing (published, saleable, pricing, images, descriptions).
- Phase 2: Filters (categories, attributes, tags) and sorting.
- Phase 3: Partner-specific catalog fencing via record rules; explicit pricelist selection.
- Phase 4: Tax display control and stock availability indicators.
- Phase 5: Service flows enablement (project/task/event/course) with dedicated endpoints.


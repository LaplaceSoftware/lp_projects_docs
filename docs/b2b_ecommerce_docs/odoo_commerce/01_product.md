# Product Model (Analysis)

## Purpose
- Provides an organized, abstract overview of Odoo product models and their ecommerce-related fields for B2B portal integration.
- Covers core fields, types, relations, and shop/media features including upsell/cross-sell.

## Models Overview
- `product.template`
  - Master product entity; holds generic data, list price, website attributes, categories.
- `product.product`
  - Variant entity; holds variant-specific data (barcode, reference, cost, attributes).
- Supporting models
  - `product.category` (backend categorization)
  - `product.public.category` (website categories)
  - `product.tag` (customer-visible product tags)
  - `product.pricelist`, `product.pricelist.item` (pricing rules)
  - `account.tax`, `account.fiscal.position` (taxes and mapping)

## Upsell & Cross‑Sell
- Optional Products
  - Field: `optional_product_ids`
  - Type: Many2many
  - Relation: `product.template`
  - Purpose: propose additional, optional items on product page/cart.
- Accessory Products
  - Field: `accessory_product_ids`
  - Type: Many2many
  - Relation: `product.product` (variants)
  - Purpose: suggest accessories; filtered for website sellability and availability.
- Alternative Products
  - Field: `alternative_product_ids`
  - Type: Many2many
  - Relation: `product.template`
  - Purpose: suggest similar/alternative items.

## Ecommerce Shop
- Tags
  - Field: `product_tag_ids`
  - Type: Many2many
  - Relation: `product.tag`
  - Notes: visible to customers; used for filtering `addons/website_sale/controllers/main.py:408`.
- Is Published
  - Field: `is_published`
  - Type: Boolean
  - Model: `product.template` and `product.product`
  - Notes: required for public users to view products `addons/website_sale/models/website.py:652`.
- Website Sequence
  - Field: `website_sequence`
  - Type: Integer
  - Model: `product.template`
  - Notes: ordering in website listings.
- Categories (Website)
  - Field: `public_categ_ids`
  - Type: Many2many
  - Relation: `product.public.category`
  - Notes: used for `/shop` category navigation.
- Ribbon
  - Field: `website_ribbon_id` (or text-based ribbon field depending on edition)
  - Type: Many2one
  - Relation: `website.ribbon`
  - Notes: display ribbon on product cards.

## eCommerce Media & Descriptions
- Ecommerce Description
  - Field: `website_description`
  - Type: Html/Text
  - Model: `product.template`
  - Notes: long-form description for product page.
- Quotation Description
  - Field: `description_sale`
  - Type: Text
  - Model: `product.template`
  - Notes: default line description in quotations/orders `addons/product/models/product_product.py:852`.

## Product Type & Invoicing
- Product Type
  - Field: `type`
  - Type: Selection
  - Values: `product` (Goods), `service` (Service), `combo` (Combo)
  - Model: `product.template` / `product.product`
  - Notes: combo products split pricing into combo items on lines `addons/sale/models/sale_order_line.py:732`.
- Invoicing Policy
  - Field: `invoice_policy`
  - Type: Selection
  - Values: e.g., `order`, `delivery` (depends on edition/config)
  - Model: `product.template`
  - Notes: influences when lines become invoiceable.

## Pricing & Taxes
- Sales Price
  - Field: `list_price`
  - Type: Monetary
  - Model: `product.template`
  - Currency: `currency_id` (Many2one `res.currency`)
  - Notes: contextual price computed via pricelist `addons/product/models/product_template.py:1442`.
- Sales Taxes
  - Field: `taxes_id`
  - Type: Many2many
  - Relation: `account.tax`
  - Notes: mapped via fiscal position for display and line computation.
- Cost
  - Field: `standard_price`
  - Type: Monetary
  - Model: primarily `product.product`
  - Currency: `cost_currency_id` (Many2one `res.currency`)
- Purchase Taxes
  - Field: `supplier_taxes_id`
  - Type: Many2many
  - Relation: `account.tax`
- Category (Backend)
  - Field: `categ_id`
  - Type: Many2one
  - Relation: `product.category`
- Reference
  - Field: `default_code`
  - Type: Char
  - Model: `product.product`
- Barcode
  - Field: `barcode`
  - Type: Char
  - Model: `product.product`

## Relations Matrix (Quick Reference)
- `product.template.optional_product_ids`: M2M → `product.template`
- `product.template.accessory_product_ids`: M2M → `product.product`
- `product.template.alternative_product_ids`: M2M → `product.template`
- `product.template.product_tag_ids`: M2M → `product.tag`
- `product.template.public_categ_ids`: M2M → `product.public.category`
- `product.template.categ_id`: M2O → `product.category`
- `product.template.website_ribbon_id`: M2O → `website.ribbon`
- `product.template.taxes_id`: M2M → `account.tax`
- `product.template.supplier_taxes_id`: M2M → `account.tax`
- `product.template.currency_id`: M2O → `res.currency`
- `product.product.product_tmpl_id`: M2O → `product.template`
- `product.product.cost_currency_id`: M2O → `res.currency`

## Price Computation Pointers
- Template contextual price
  - `product.template._get_contextual_price(product=None)` `addons/product/models/product_template.py:1442`
- Variant contextual price
  - `product.product._get_contextual_price()` `addons/product/models/product_product.py:882`
- Attribute extras in price context
  - `product.product._get_product_price_context(combination)` `addons/product/models/product_product.py:785`
  - `product.template._get_product_price_context(combination)` `addons/product/models/product_template.py:648`
- Line price/tax mapping for display alignment
  - `sale.order.line._reset_price_unit()` `addons/sale/models/sale_order_line.py:619`

## Notes for Integration
- Use website domain and publish flags to filter catalog for public/portal users.
- Compute display prices through pricelists and fiscal positions to match tax inclusion behavior.
- For upsell/cross‑sell, load optional/accessory/alternative relations and filter by website visibility.
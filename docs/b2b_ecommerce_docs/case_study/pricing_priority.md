# Odoo 19 Pricing Priority Case Study

## Partner Pricelist Resolution

- `addons/product/models/res_partner.py:31-37`: Computes `property_product_pricelist` via `_get_partner_pricelist_multi`.
- `addons/product/models/product_pricelist.py:288-356`: Determines partner pricelist with order: specific property → country group → company default → global default → first available.

## Rule Collection

- `addons/product/models/product_pricelist.py:238-246`: Fetches applicable rules for the pricelist.
- `addons/product/models/product_pricelist.py:248-264`: Builds domain combining product template/variant, category (parent_of), and validity dates.

## Rule Selection Priority

- `addons/product/models/product_pricelist_item.py:11`: Rules ordered by `applied_on`, `min_quantity` desc, `categ_id` desc, `id` desc.
- `addons/product/models/product_pricelist.py:206-235`: Iterates rules in order and picks the first applicable via `_is_applicable_for`.
- `addons/product/models/product_pricelist_item.py:503-545`: Applicability checks min quantity, product/category matching, and variant/template alignment.

### Effective Priority (examples)

- Variant-specific (`applied_on='0_product_variant'`) overrides template and category due to string sort and loop order.
- Template-specific (`'1_product'`) overrides category and global.
- Category (`'2_product_category'`) overrides global.
- Global (`'3_global'`) applies when no more specific rule matches.
- Within same `applied_on`, higher `min_quantity` has priority.

## Price Computation

- `addons/product/models/product_pricelist_item.py:547-603`: Computes price based on rule (`fixed`, `percentage`, `formula`).
- `addons/product/models/product_pricelist_item.py:605-636`: Base price source: list price, standard cost, or chained pricelist; includes currency conversion.
- `addons/product/models/product_pricelist_item.py:638-661`: Resolves displayed base price considering chained pricelists when showing discount.

## Controller Integration (Evidence)

- `addons_lp_ecommerce/ecommerce/controllers/ecommerce_api.py:28-29`: Products endpoint.
- `addons_lp_ecommerce/ecommerce/controllers/ecommerce_api.py:33-41`: Currency and pricelist resolution.
- `addons_lp_ecommerce/ecommerce/controllers/ecommerce_api.py:52-73`: Domain restriction by portal company pricelist (template, variant, and category), with global-rule fallback.

## Example Scenario

Given partner `ACME` with pricelist `PL-ACME`:

- Rule A: Variant X at fixed price — `applied_on='0_product_variant'`, `min_quantity=1`.
- Rule B: Category Electronics 10% discount — `applied_on='2_product_category'`.
- Rule C: Global 5% discount — `applied_on='3_global'`.

For product template `Phone` (variant X in Electronics):

- Selection: Rule A applies first (variant specific).
- Price: Computed by Rule A (`fixed`).

For product template `TV` (no variant-specific rule, Electronics):

- Selection: Rule B applies (category).
- Price: 10% off base.

For product template `Chair` (not Electronics):

- Selection: Rule C applies (global).
- Price: 5% off base.

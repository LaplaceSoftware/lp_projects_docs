product =>

Upsell & Cross-Sell
Optional Products? product.template
Recommend when 'Adding to Cart' or quotation
Accessory Products?
Suggested accessories in the eCommerce cart
Alternative Products?



```
- product: `product.template` record.
- product_variant: `product.product` record.
```



```
_get_configurator_display_price
_get_configurator_price
pricelist._get_product_price_rule


```


```
product._get_product_url(category, product_query_params, grouped_attributes_values)
```


API:
product detail: http://localhost:8019/website_sale/get_combination_info

http://localhost:8019/website_payment/snippet/supported_payment_methods?limit=8

http://localhost:8019/shop/products/recently_viewed_update

http://localhost:8019/shop/wishlist/add

http://localhost:8019/shop/cart/add

Prices:
/Users/abadr/Documents/Laplace/Projects/odoo19/addons/partnership/models/product_pricelist.py
/Users/abadr/Documents/Laplace/Projects/odoo19/addons/product/models/product_pricelist.py
/Users/abadr/Documents/Laplace/Projects/odoo19/addons/product/models/product_template.py
pricelist_rule_ids

Membership
/Users/abadr/Documents/Laplace/Projects/odoo19/addons/partnership/models/res_company.py
/Users/abadr/Documents/Laplace/Projects/odoo19/addons/partnership/models/res_partner_grade.py



signup | Authenticate
/Users/abadr/Documents/Laplace/Projects/odoo19e/odoo/addons/auth_signup/models/res_users.py
/Users/abadr/Documents/Laplace/Projects/odoo19/odoo/addons/base/models/res_users.py



/Users/abadr/Documents/Laplace/Projects/odoo19/addons/survey/wizard/survey_invite.py


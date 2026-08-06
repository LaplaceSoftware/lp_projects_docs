
i need to refactor logic in this endpoint so based on params filter  company_id:portal_company_partner_id field in 
and params flag pricelist_restrict by default true
pricelist_restrict by default true
i need to load products only related to  portal_company_partner_id pricelist not all prodcuts

make analysis odoo19 code base first to build domain filter correct way
files maybe help you
/Users/abadr/Documents/Laplace/Projects/odoo19/addons/partnership/models/product_pricelist.py
/Users/abadr/Documents/Laplace/Projects/odoo19/addons/product/models/product_pricelist.py

very important files:
/Users/abadr/Documents/Laplace/Projects/odoo19/addons/product/models/product_template.py
pricelist_rule_ids

by the end make case study and  give me documentation about how odoo determine sale pricing level priority  steps save ouput in folder
by example and evidence code reference

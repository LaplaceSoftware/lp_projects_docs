from odoo.http import Controller, request, route
from odoo import fields
from odoo.osv import expression
import json

class EcommerceApi(Controller):
    @route('/ecommerce/api/shop_test', type='http', auth='public', methods=['GET'], website=True, csrf=False)
    def shop(self, **kwargs):
        website = request.env['website'].get_current_website()
        search = kwargs.get('search') or ''
        category_id = kwargs.get('category_id')
        order_key = kwargs.get('order') or website.shop_default_sort
        page = int(kwargs.get('page') or 0)
        page_size = int(kwargs.get('page_size') or (website.shop_ppg or 21))
        display_currency_id = kwargs.get('display_currency')
        attribute_value_dict = kwargs.get('attribute_value_dict')
        try:
            attribute_value_dict = json.loads(attribute_value_dict) if attribute_value_dict else {}
        except Exception:
            attribute_value_dict = {}
        order_by = 'is_published desc, %s, id desc' % order_key
        domains = [request.website.sale_product_domain()]
        if search:
            terms = search.split(' ')
            term_domains = []
            for srch in terms:
                or_domain = ['|', '|', '|',
                             ('name', 'ilike', srch),
                             ('variants_default_code', 'ilike', srch),
                             ('website_description', 'ilike', srch),
                             ('description_sale', 'ilike', srch)]
                term_domains.append(or_domain)
            if term_domains:
                domains.append(expression.AND(term_domains))
        if category_id:
            domains.append(('public_categ_ids', 'child_of', int(category_id)))
        if attribute_value_dict:
            # Reuse website_sale controller semantics via the same domain shape
            # attribute_value_dict: {attribute_id: [value_id, ...]}
            # Match templates having at least one of the selected values per attribute
            for _attr_id, val_ids in attribute_value_dict.items():
                domains.append(('attribute_line_ids.value_ids', 'in', [int(v) for v in val_ids]))
        domain_expr = expression.AND(domains)
        Product = request.env['product.template'].with_context(bin_size=True)
        all_products = Product.search(domain_expr, order=order_by)
        total = len(all_products)
        offset = page * page_size
        products = all_products[offset:offset + page_size]
        currency = request.env['res.currency'].browse(int(display_currency_id)) if display_currency_id else website.currency_id
        items = []
        for p in products:
            price, _rule_id = p._get_configurator_display_price(p, 1, fields.Datetime.now(), currency, request.pricelist)
            list_price = p.currency_id._convert(p.list_price, currency, website.company_id, fields.Date.today(), round=False)
            has_discounted_price = price < list_price
            items.append({
                'product_id': p.id,
                'slug': request.env['ir.http']._slug(p),
                'product_type': p.type,
                'name': p.name,
                'display_name': p.display_name,
                'is_published': p.is_published,
                'website_sequence': p.website_sequence,
                'ribbon_id': p.website_ribbon_id.id if p.website_ribbon_id else False,
                'image_url': f'/web/image/product.template/{p.id}/image_1920',
                'public_categ_ids': p.public_categ_ids.ids,
                'tags': p.product_tag_ids.ids,
                'first_variant_id': p._get_first_possible_variant_id(),
                'variant_count': len(p.product_variant_ids),
                'currency_id': currency.id,
                'price': price,
                'list_price': list_price,
                'has_discounted_price': has_discounted_price,
            })
        attr_groups = []
        if all_products:
            AttributeLine = request.env['product.template.attribute.line']
            grouped = AttributeLine._read_group(
                domain=[('product_tmpl_id', 'in', all_products.ids), ('attribute_id.visibility', '=', 'visible')],
                groupby=['attribute_id'],
                order='attribute_id'
            )
            attr_ids = [attr.id for attr, in grouped]
            attr_groups = request.env['product.attribute'].browse(attr_ids).read(['id', 'name'])
        min_price = 0.0
        max_price = 0.0
        if all_products:
            lp = [p.currency_id._convert(p.list_price, currency, website.company_id, fields.Date.today(), round=False) for p in all_products]
            if lp:
                min_price = min(lp)
                max_price = max(lp)
        payload = {
            'products': items,
            'pager': {'page': page, 'page_size': page_size, 'total': total},
            'filters': {'min_price': min_price, 'max_price': max_price, 'attributes': attr_groups},
            'sort': {'order_key': order_key},
            'currency': {'id': currency.id, 'name': currency.name},
        }
        return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])

    @route('/ecommerce/api/product_list_test', type='http', auth='public', methods=['GET'], website=True, csrf=False)
    def product_list(self, **kwargs):
        website_id = kwargs.get('website_id')
        website = request.env['website'].browse(int(website_id)) if website_id else request.env['website'].get_current_website()
        page = int(kwargs.get('page') or 0)
        page_size = int(kwargs.get('page_size') or (website.shop_ppg or 21))
        currency_id = kwargs.get('display_currency')
        pricelist_id = kwargs.get('pricelist_id')
        currency =  self.env.company.currency_id
        if currency_id:
            currency = request.env['res.currency'].browse(int(currency_id))
        elif website:
            currency = website.currency_id
        pricelist = request.env['product.pricelist'].browse(int(pricelist_id)) if pricelist_id else (request.pricelist if website else None)
        if not currency and pricelist:
            currency = pricelist.currency_id
        if not currency:
            currency = request.env.company.currency_id
        # Static public domain (no website preferences): saleable + published + allowed service tracking
        base_domain = [
            ('sale_ok', '=', True),
            ('is_published', '=', True),
            ('service_tracking', 'in', request.env['product.template']._get_saleable_tracking_types()),
        ]
        domain_expr = expression.AND([base_domain])
        Product = request.env['product.template'].with_context(bin_size=True)
        all_products = Product.search(domain_expr, order='website_sequence, id desc')
        total = len(all_products)
        offset = page * page_size
        products = all_products[offset:offset + page_size]
        items = []
        for p in products:
            if pricelist:
                price, _rule_id = p._get_configurator_display_price(p, 1, fields.Datetime.now(), currency, pricelist)
            else:
                price = p.currency_id._convert(p.list_price, currency, request.env.company, fields.Date.today(), round=False)
            list_price = p.currency_id._convert(p.list_price, currency, (website.company_id if website else request.env.company), fields.Date.today(), round=False)
            discount_pct = ((list_price - price) / list_price * 100.0) if list_price else 0.0
            items.append({
                'product_id': p.id,
                'slug': request.env['ir.http']._slug(p),
                'name': p.name,
                'display_name': p.display_name,
                'is_published': p.is_published,
                'website_sequence': p.website_sequence,
                'image_url': f'/web/image/product.template/{p.id}/image_1920',
                'public_categ_ids': p.public_categ_ids.ids,
                'tags': p.product_tag_ids.ids,
                'description_ecommerce': p.description_ecommerce or '',
                'description_sale': p.description_sale or '',
                'first_variant_id': p._get_first_possible_variant_id(),
                'variant_count': len(p.product_variant_ids),
                'currency_id': currency.id,
                'list_price': list_price,
                'price': price,
                'discount_percent': discount_pct,
            })
        payload = {
            'products': items,
            'pager': {'page': page, 'page_size': page_size, 'total': total},
            'currency': {'id': currency.id, 'name': currency.name},
        }
        return request.make_response(json.dumps(payload), headers=[('Content-Type', 'application/json')])
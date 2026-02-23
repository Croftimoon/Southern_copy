from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    applied_on = fields.Selection(
        selection_add=[('4_vendor', 'Vendor')],
        ondelete={'4_vendor': 'cascade'}
    )

    vendor_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        domain=[('is_company', '=', True), ('supplier_rank', '>', 0)],
        help='Apply rule to products with vendor'
    )

    def _compute_name_and_price(self):
        """Compute name and price display for pricelist items"""
        # Call parent method first
        super()._compute_name_and_price()

        # Override name for vendor option
        for item in self:
            if item.applied_on == '4_vendor':
                if item.vendor_id:
                    item.name = "Vendor: %s" % item.vendor_id.name
                else:
                    item.name = "Vendor"

    def _is_applicable_for(self, product, qty_in_product_uom):
        """Check if pricelist item is applicable for the given product"""
        # Call parent method first for standard checks
        res = super()._is_applicable_for(product, qty_in_product_uom)

        # Additional check for vendor
        if res and self.applied_on == '4_vendor':
            # Check if the vendor is in the product's seller_ids
            if self.vendor_id and product.seller_ids:
                return any(seller.partner_id == self.vendor_id for seller in product.seller_ids)
            return False

        return res

    def _check_product_consistency(self):
        """Check product consistency for pricelist items"""
        for item in self:
            if item.applied_on == '4_vendor':
                if not item.vendor_id:
                    raise ValidationError("Vendor must be set when Applied On is 'Vendor'")
            else:
                # Call parent method for other cases
                super(ProductPricelistItem, item)._check_product_consistency()

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if not values.get('applied_on'):
                values['applied_on'] = (
                    '0_product_variant' if values.get('product_id') else
                    '1_product' if values.get('product_tmpl_id') else
                    '2_product_category' if values.get('categ_id') else
                    '4_vendor' if values.get('vendor_id') else
                    '3_global'
                )

            # Ensure item consistency for later searches.
            applied_on = values['applied_on']
            if applied_on == '3_global':
                values.update(dict(product_id=None, product_tmpl_id=None, categ_id=None, vendor_id=None))
            elif applied_on == '2_product_category':
                values.update(dict(product_id=None, product_tmpl_id=None, vendor_id=None))
            elif applied_on == '1_product':
                values.update(dict(product_id=None, categ_id=None, vendor_id=None))
            elif applied_on == '0_product_variant':
                values.update(dict(categ_id=None, vendor_id=None))
            elif applied_on == '4_vendor':
                values.update(dict(product_id=None, product_tmpl_id=None, categ_id=None))
        return super().create(vals_list)

    def write(self, values):
        if values.get('applied_on', False):
            applied_on = values['applied_on']
            if applied_on == '3_global':
                values.update(dict(product_id=None, product_tmpl_id=None, categ_id=None, vendor_id=None))
            elif applied_on == '2_product_category':
                values.update(dict(product_id=None, product_tmpl_id=None, vendor_id=None))
            elif applied_on == '1_product':
                values.update(dict(product_id=None, categ_id=None, vendor_id=None))
            elif applied_on == '0_product_variant':
                values.update(dict(categ_id=None, vendor_id=None))
            elif applied_on == '4_vendor':
                values.update(dict(product_id=None, product_tmpl_id=None, categ_id=None))
        return super().write(values)
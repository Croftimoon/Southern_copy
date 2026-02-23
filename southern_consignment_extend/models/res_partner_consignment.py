from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ResPartnerConsignment(models.Model):
    _name = 'res.partner.consignment'
    _description = 'Master Record'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain="[('property_is_consignment_product', '=', True)]"
    )
    quantity = fields.Float(string='Quantity', required=True)

    @api.constrains('product_id')
    def _check_product_template(self):
        for record in self:
            if not record.product_id.property_is_consignment_product:
                raise ValidationError(_('Product is not a consignment product.'))

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than zero.'))
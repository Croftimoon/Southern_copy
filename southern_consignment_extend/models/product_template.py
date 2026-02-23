from odoo import fields, models, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_is_consignment_product = fields.Boolean(default=True)
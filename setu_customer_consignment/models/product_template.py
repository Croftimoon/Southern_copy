from odoo import fields, models, api, _
from odoo.osv import expression


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_is_consignment_product = fields.Boolean(string="Is Consignment Product", company_dependent=True)

    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)
        if self.env.context.get('property_is_consignment_product', False) and not self:
            res['property_is_consignment_product'] = True
            res['detailed_type'] = 'product'
        return res



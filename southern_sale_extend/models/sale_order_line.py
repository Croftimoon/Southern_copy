from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    discount_readonly = fields.Boolean(
        compute='_compute_discount_readonly',
        store=False,
        default=lambda self: not self.env.user.has_group('southern_sale_extend.group_sale_discount_edit')
    )

    @api.depends_context('uid')
    def _compute_discount_readonly(self):
        """Compute if discount should be readonly"""
        has_permission = self.env.user.has_group('southern_sale_extend.group_sale_discount_edit')
        for record in self:
            record.discount_readonly = not has_permission
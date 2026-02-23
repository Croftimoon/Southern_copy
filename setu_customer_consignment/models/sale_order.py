from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class SaleOrer(models.Model):
    _inherit = 'sale.order'

    property_is_consignment_order = fields.Boolean(string="Is Consignment Order")
    transfer_id = fields.Many2one('stock.picking', string="Transfer")

    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)
        if self.env.context.get('property_is_consignment_order', False) and not self:
            res['property_is_consignment_order'] = True
        return res

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrer, self)._prepare_invoice()
        if self.property_is_consignment_order:
            invoice_vals['property_is_consignment_invoice'] = True
        return invoice_vals

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if self.property_is_consignment_order:
            raise ValidationError("You can't duplicate consignment sale order.")
        return super().copy()


    def _action_confirm(self):
        super(SaleOrer, self.with_context(confirm_sale_order=True))._action_confirm()

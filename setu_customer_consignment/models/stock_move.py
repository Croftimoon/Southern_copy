from odoo import fields, models, api, _, Command

from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model_create_multi
    def create(self, values):
        for record in values:
            if 'sale_line_id' in record and self._context.get('confirm_sale_order', False):
                line = self.env['sale.order.line'].sudo().browse(record['sale_line_id'])
                if line.location_id:
                    record.update({'location_id': line.location_id.id})
                else:
                    order_id = line.order_id
                    location_id = order_id.partner_id.property_is_consignment_customer and order_id.partner_id.property_consignment_location_id or False
                    if order_id.property_is_consignment_order and location_id:
                        record.update({'location_id': location_id.id})
        return super(StockMove, self).create(values)

    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)
        res['company_id'] = self.env.company.id
        return res

    product_id = fields.Many2one(
        'product.product', 'Product',
        check_company=True,
        index=True, required=True)

    def _update_reserved_quantity(self, need, location_id, quant_ids=None, lot_id=None, package_id=None,
                                  owner_id=None, strict=True):
        self.ensure_one()
        order_id = self.sale_line_id and self.sale_line_id.order_id or False
        lots = order_id and order_id.transfer_id and order_id.transfer_id.move_line_ids.mapped('lot_id.id') or False
        if order_id and order_id.property_is_consignment_order and order_id.transfer_id and lots:
            context = self._context.copy() or {}
            context.update({'property_is_consignment_order': True, 'consignment_lots': lots})
            return super(StockMove, self.with_context(context))._update_reserved_quantity(need=need,
                                                                                          location_id=location_id, quant_ids=quant_ids, lot_id=lot_id,
                                                                                          package_id=package_id, owner_id=owner_id, strict=strict)
        else:
            return super(StockMove, self)._update_reserved_quantity(need=need,
                                                                  location_id=location_id, quant_ids=quant_ids, lot_id=lot_id,
                                                                  package_id=package_id, owner_id=owner_id, strict=strict)

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    product_id = fields.Many2one('product.product', 'Product', ondelete="cascade", check_company=True, index=True)
    is_consignment = fields.Boolean(string="Is Consignment")

    @api.model_create_multi
    def create(self, values):
        if self._context.get('property_is_consignment_order', False):
            for d in values:
                d.update({'is_consignment': True})
        res = super(StockMoveLine, self).create(values)
        return res

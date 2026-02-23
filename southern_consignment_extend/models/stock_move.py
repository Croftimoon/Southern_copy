from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(quantity, reserved_quant)

        if self._context.get('confirm_sale_order', False):
            if self.sale_line_id and self.sale_line_id.lot_id:
                vals['lot_id'] = self.sale_line_id.lot_id.id

            if self.sale_line_id and self.sale_line_id.location_id:
                if self.sale_line_id.product_uom_qty > 0:
                    vals['location_id'] = self.sale_line_id.location_id.id
                else:
                    vals['location_dest_id'] = self.sale_line_id.location_id.id

        return vals
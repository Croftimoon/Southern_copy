from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    is_consignment_picking = fields.Boolean(
        related='picking_id.is_consignment_picking', store=True
)
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    warehouse_note = fields.Text(
        string='Sales Note',
        compute='_compute_warehouse_note',
        store=True,
        help='Note from the related sales order'
    )

    @api.depends('sale_id.warehouse_note')
    def _compute_warehouse_note(self):
        for picking in self:
            if picking.sale_id:
                picking.warehouse_note = picking.sale_id.warehouse_note
            else:
                picking.warehouse_note = False

    def send_message_to_sales(self):
        """Open wizard to send message to sales team"""
        return {
            'name': 'Send Message to Sales Team',
            'type': 'ir.actions.act_window',
            'res_model': 'send.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_sale_order_id': self.sale_id.id,
                'default_message_type': 'warehouse_to_sale',
            }
        }
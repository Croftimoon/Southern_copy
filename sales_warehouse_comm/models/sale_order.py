from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    warehouse_note = fields.Text(
        string='Warehouse Note',
        help='Note that will be displayed on picking orders'
    )

    def send_message_to_warehouse(self):
        """Open wizard to send message to warehouse team"""
        return {
            'name': 'Send Message to Warehouse',
            'type': 'ir.actions.act_window',
            'res_model': 'send.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_message_type': 'sale_to_warehouse',
            }
        }
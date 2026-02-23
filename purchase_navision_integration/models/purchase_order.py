from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_send_to_navision(self):
        """Open wizard to send email to contacts with Excel attachment"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Send to SI Navision',
            'res_model': 'purchase.navision.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_order_id': self.id,
            }
        }
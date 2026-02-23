from odoo import fields, models, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    property_is_consignment_invoice = fields.Boolean(string="Is Consignment Invoice")

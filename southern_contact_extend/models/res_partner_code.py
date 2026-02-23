from odoo import models, fields


class PartnerCode(models.Model):
    _name = 'res.partner.code'
    _description = 'Partner Alternate Code'

    name = fields.Char(required=True, index=True, string="Code")
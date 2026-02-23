from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    alternate_code_ids = fields.Many2many('res.partner.code', string="Alternate Codes")

    @api.model
    def create(self, vals):
        if not vals.get('ref') and vals['is_company']:
            vals['ref'] = self.env['ir.sequence'].next_by_code('res.partner.ref') or '/'
        return super().create(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('ref') and vals.get('is_company'):
                vals['ref'] = self.env['ir.sequence'].next_by_code('res.partner.ref') or '/'
        return super().create(vals_list)
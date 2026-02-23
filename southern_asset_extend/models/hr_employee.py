from odoo import models, fields, api, _


class HREmployee(models.Model):
    _inherit = "hr.employee"

    asset_ids = fields.One2many('account.asset', 'employee_id', string="Assigned Assets")
    asset_count = fields.Integer(compute='_compute_asset_count', string="Assigned Assets")

    @api.depends('asset_ids')
    def _compute_asset_count(self):
        for employee in self:
            employee.asset_count = len(employee.asset_ids)
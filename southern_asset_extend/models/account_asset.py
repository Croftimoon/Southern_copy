from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountAsset(models.Model):
    _inherit = "account.asset"

    employee_id = fields.Many2one(
        'hr.employee',
        string="Assigned Employee",
        tracking=True,
        domain="[('active', '=', True)]"
    )
    employee_name = fields.Char(compute='_compute_employee_name', string='Employee Name')
    serial_numbers = fields.Char(string='Serial Numbers')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id and not self.employee_id.active:
            raise ValidationError(_("Assigned Employee must be active."))

    @api.depends('employee_id')
    def _compute_employee_name(self):
        for record in self:
            record.employee_name = record.employee_id.name if record.employee_id else ""

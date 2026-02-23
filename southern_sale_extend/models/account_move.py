from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    partner_id = fields.Many2one(
        check_company=True,
        domain=[('is_company', '=', True)],
    )
    client_id = fields.Many2one(
        comodel_name='res.partner',
        string="Contact",
        change_default=True,
        index=True,
        tracking=1,
        domain=[('is_company', '=', False)],
    )
    patient_name = fields.Char(string='Patient Name')
    surgery_date = fields.Date(string='Surgery Date')
    sales_team_member = fields.Char(
        string='Sales Team Member',
        compute='_compute_sales_team_member',
        store=True
    )

    non_service_total = fields.Monetary(
        string='Non-Service Total',
        compute='_compute_non_service_total',
        store=True,
        help="Signed total of move lines for non-service products"
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for order in self:
            if order.client_id and order.partner_id and order.client_id.parent_id != order.partner_id:
                order.client_id = False

    @api.onchange('client_id')
    def _onchange_client_id(self):
        for order in self:
            if order.client_id and (not order.partner_id or order.client_id.parent_id != order.partner_id):
                order.partner_id = order.client_id.parent_id

    @api.depends('team_id.member_ids.name')
    def _compute_sales_team_member(self):
        for move in self:
            move.sales_team_member = ''
            if move.team_id:
                names = move.team_id.member_ids.mapped('name')
                move.sales_team_member = names[0] if names else ''

    @api.depends('line_ids.balance', 'line_ids.product_id.detailed_type', 'line_ids.display_type')
    def _compute_non_service_total(self):
        for move in self:
            total = 0.0
            for line in move.line_ids:
                if line.product_id and line.product_id.detailed_type != 'service' and line.display_type == 'product':
                    total += -line.balance

            move.non_service_total = total

    def action_send_and_print(self):
        action = super().action_send_and_print()
        ctx = dict(action.get('context') or {})
        ctx['default_checkbox_download'] = False
        action['context'] = ctx
        return action
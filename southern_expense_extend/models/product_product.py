from odoo import models, fields, api, _


class Product(models.Model):
    _inherit = "product.product"

    required_group_id = fields.Many2one(
        'res.groups',
        string="Required Group",
        help="Only users in this group can see this record."
    )

    can_access_product = fields.Boolean(compute='_compute_can_access_product', store=False)

    @api.depends('required_group_id')
    def _compute_can_access_product(self):
        user_groups = self.env.user.groups_id
        for product in self:
            product.can_access_product = (
                not product.required_group_id or
                product.required_group_id in user_groups or
                self.env.user.has_group('hr_expense.group_hr_expense_manager')
            )
from odoo import models, fields, _
from odoo.osv import expression


class HrExpense(models.Model):
    _inherit = "hr.expense"

    product_id = fields.Many2one(
        domain=lambda self: str(self._domain_product_id())
    )

    def _domain_product_id(self):
        if self.env.ref('hr_expense.group_hr_expense_manager').id in self.env.user.groups_id.ids:
            return [('can_be_expensed', '=', True)]

        return [
            '&',
            ('can_be_expensed', '=', True),
            '|',
            ('required_group_id', '=', False),
            ('required_group_id', 'in', self.env.user.groups_id.ids)
        ]

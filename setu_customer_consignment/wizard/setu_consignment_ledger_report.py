from datetime import datetime

from odoo import fields, models, api, _

from odoo.exceptions import ValidationError


class SetuConsignmentLedgerReport(models.TransientModel):
    _name = 'setu.consignment.ledger.report'
    _description = "Setu Consignment Ledger Report"

    start_date = fields.Date(string="Start Date", default=datetime.today().replace(day=1))
    end_date = fields.Date(string="End Date", default=datetime.today())
    product_category_ids = fields.Many2many("product.category", string="Product Categories")
    product_ids = fields.Many2many("product.product", string="Products")
    consignee_ids = fields.Many2many("res.partner", string="Consignee")
    company_ids = fields.Many2many("res.company", string="Companies")

    @api.onchange('start_date', 'end_date')
    def _compute_date_open(self):
        if self.start_date > fields.date.today() or self.end_date > fields.date.today():
            raise ValidationError("You cant't select date of future")
        elif self.start_date > self.end_date:
            raise ValidationError("Please select start date smaller then end date")


    def download_report_in_listview(self):
        self.get_consignment_movements_for_inventory_ledger()
        tree_view_id = self.env.ref('setu_customer_consignment.setu_consignment_ledger_bi_report_tree').id
        form_view_id = self.env.ref('setu_customer_consignment.setu_consignment_ledger_bi_report_form').id
        report_display_views = []

        report_display_views.append((tree_view_id, 'tree'))
        report_display_views.append((form_view_id, 'form'))
        viewmode = "tree,form"
        return {
            'name': _('Consignment Ledger Report - %s to %s' % (self.start_date, self.end_date)),
            'domain': [('wizard_id', '=', self.id)],
            'res_model': 'setu.consignment.ledger.bi.report',
            'view_mode': viewmode,
            'type': 'ir.actions.act_window',
            'views': report_display_views,
            'context': {'search_default_product_groupby': 1},
            'help': """
                <p class="o_view_nocontent_smiling_face">
                    No data found.
                </p>
            """
        }

    def get_consignment_movements_for_inventory_ledger(self):
        start_date = self.start_date
        end_date = self.end_date
        category_ids = company_ids = {}
        if self.product_category_ids:
            categories = self.env['product.category'].search([('id', 'child_of', self.product_category_ids.ids)])
            category_ids = set(categories.ids) or {}

        products = self.product_ids and set(self.product_ids.ids) or {}

        if self.company_ids:
            companies = self.env['res.company'].search([('id', 'child_of', self.company_ids.ids)])
            company_ids = set(companies.ids) or {}
        else:
            company_ids = set(self.env.context.get('allowed_company_ids', False) or self.env.user.company_ids.ids) or {}

        consignee_ids = self.consignee_ids and set(self.consignee_ids.ids) or {}
        query = """
                Select * from consignment_ledger_analysis('%s','%s','%s','%s', '%s','%s', '%d')
            """ % (company_ids, products, category_ids, consignee_ids, start_date, end_date, self.id)
        self._cr.execute(query)
        stock_data = self._cr.dictfetchall()
        return stock_data


class SetuConsignmentLedgerBIReport(models.TransientModel):
    _name = 'setu.consignment.ledger.bi.report'
    _rec_name = "consignee_id"

    date_order = fields.Date("Date")
    consignee_id = fields.Many2one("res.partner", "Consignee")
    company_id = fields.Many2one("res.company", "Company")
    warehouse_id = fields.Many2one("stock.warehouse", "Warehouse")
    product_id = fields.Many2one("product.product", "Product")
    product_category_id = fields.Many2one("product.category", "Category")
    opening_stock = fields.Float("Opening Stock", default=0)
    wizard_id = fields.Many2one("setu.consignment.ledger.report")
    transferred_qty = fields.Float("Transferred Quantity", default=0)
    sold_qty = fields.Float("Sold Quantity", default=0)
    returned_qty = fields.Float("Transferred Returned Quantity", default=0)
    closing = fields.Float("Closing", default=0)
    sold_return_quantity = fields.Float("Sold Return Quantity")
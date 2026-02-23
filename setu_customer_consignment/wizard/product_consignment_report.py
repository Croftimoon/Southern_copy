from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class ProductConsignmentReport(models.TransientModel):
    _name = 'product.consignment.report'
    _description = "Product Consignment Report"

    start_date = fields.Date('Start Date', default=datetime.today().replace(day=1))
    end_date = fields.Date('End Date', default=datetime.today())
    company_ids = fields.Many2many("res.company", string="Companies")
    product_category_ids = fields.Many2many("product.category", string="Product Categories")
    product_ids = fields.Many2many("product.product", string="Products")
    products_ids = fields.Many2many("product.product", 'product_consignment_report_product_rel',
                                    'product_consignment_report_id',
                                    'products_id',
                                    string="Products",
                                    compute="_compute_products_ids")
    consignee_ids = fields.Many2many("res.partner", string="Consignee")

    def view_product_report(self):
        stock_data = self.get_consignment_product_data()
        # print (stock_data)
        for turnover_data_value in stock_data:
            turnover_data_value['wizard_id'] = self.id
            self.create_data(turnover_data_value)

        return {
            'name': _('Product Consignment Analysis Report'),
            'domain': [('wizard_id', '=', self.id)],
            'res_model': 'product.consignment.analysis.report',
            'view_mode': 'tree,graph,pivot,form',
            'type': 'ir.actions.act_window',
            'context': {'search_default_product_id_groupby': 1},
            'help': """
                        <p class="o_view_nocontent_smiling_face">
                            No data found.
                        </p>
                    """
        }

    # @api.onchange('product_category_ids')
    # def onchange_product_category_id(self):
    #     if self.product_category_ids:
    #         return {'domain': {'product_ids': [('categ_id', 'child_of', self.product_category_ids.ids)]}}

    @api.depends('product_category_ids')
    def _compute_products_ids(self):
        for record in self:
            if record.product_category_ids:
                products = self.env['product.product'].search(
                    [('categ_id', 'child_of', record.product_category_ids.ids)])
                record.products_ids = products if products else False
            else:
                products = self.env['product.product'].search([])
                record.products_ids = products if products else False

    @api.onchange('start_date', 'end_date')
    def _compute_date_open(self):
        if self.start_date > fields.date.today() or self.end_date > fields.date.today():
            raise ValidationError("You cant't select date of future")
        elif self.start_date > self.end_date:
            raise ValidationError("Please select start date smaller then end date")

    def get_consignment_product_data(self):
        """

        :return:
        """

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

        if self.consignee_ids:
            consignees = self.env['res.partner'].search([('id', 'in', self.consignee_ids.ids)])
            consignee_ids = set(self.consignee_ids.ids) or {}
        else:
            consignee_ids = set(self.env['res.partner'].search([('property_is_consignment_customer', '=', True)]).ids) or {}

        query = """
                Select * from get_consignment_product_data('%s','%s','%s','%s','%s','%s')
            """ % (company_ids, products, category_ids, consignee_ids, start_date, end_date)

        try:
            self._cr.execute(query)
            stock_data = self._cr.dictfetchall()
        except Exception:
            raise ValidationError("Something went wrong")
        return stock_data

    def create_data(self, data):
        return self.env['product.consignment.analysis.report'].create(data)

class CustomerConsignmentAnalysisReport(models.TransientModel):
    _name = 'product.consignment.analysis.report'
    _description = """Product Consignment Analysis Report"""

    company_id = fields.Many2one("res.company", "Company")
    product_id = fields.Many2one("product.product", "Product")
    sold_amount = fields.Float("Sold Amount")
    sold_quantity = fields.Float("Sold Quantity")
    returned_qty = fields.Float("Transferred Return Quantity")
    trans_quantity = fields.Float("Transferred Quantity")
    wizard_id = fields.Many2one("product.consignment.report")
    sold_pr = fields.Float("Sold Percentage")
    returned_pr = fields.Float("Transferred Return Percentage")
    sold_return_quantity = fields.Float("Sold Return Quantity")
    sold_return_amount = fields.Float("Sold Return Amount")
    trans_amount = fields.Float("Transferred Amount")
    return_amount = fields.Float("Transferred Return Amount")
    sold_return_pr = fields.Float("Sold Return Percentage")

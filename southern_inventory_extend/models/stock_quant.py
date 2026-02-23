from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Company Currency',
        readonly=True,
        store=True
    )

    valuation_adjustment = fields.Monetary(
        string='Valuation Adjustment',
        compute='_compute_valuation_adjustment',
        store=True,
        currency_field='company_currency_id',
        help='Write-off or write-on value based on inventory difference'
    )

    @api.depends('inventory_diff_quantity', 'product_id', 'location_id')
    def _compute_valuation_adjustment(self):
        for quant in self:
            if quant.inventory_diff_quantity and quant.product_id:
                # Get the product cost
                product_cost = quant.product_id.standard_price

                # Calculate valuation adjustment (positive = write-on, negative = write-off)
                quant.valuation_adjustment = quant.inventory_diff_quantity * product_cost
            else:
                quant.valuation_adjustment = 0.0
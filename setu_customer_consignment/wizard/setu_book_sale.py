from odoo import fields, models, api, _


class SetuBookSaleLine(models.TransientModel):
    _name = 'setu.book.sale.line'
    _description = "Setu Book Sale Line"

    sale_id = fields.Many2one("setu.book.sale", string="Sale")
    product_id = fields.Many2one("product.product", string="Product")
    product_uom_qty = fields.Integer(string="Quantity")


class SetuBookSale(models.TransientModel):
    _name = 'setu.book.sale'
    _description = "Setu Book Sale"

    partner_id = fields.Many2one("res.partner", string="Customer")
    transfer_id = fields.Many2one('stock.picking', string="Transfer")
    order_line = fields.One2many('setu.book.sale.line','sale_id', string="Order lines")

    @api.model
    def default_get(self, default_fields):

        res = super().default_get(default_fields)
        if self._context.get('partner_id', False):
            res['partner_id'] = self._context.get('partner_id', False)
        if self._context.get('transfer_id', False):
            res['transfer_id'] = self._context.get('transfer_id', False)
        if self._context.get('order_line', False):
            res['order_line'] = self._context.get('order_line', False)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(SetuBookSale, self).create(vals_list)
        for vals in vals_list:
            vals.update({"property_is_consignment_order": "True", 'partner_id': res.partner_id.id, 'transfer_id': res.transfer_id.id})
        context = self._context.copy() or {}
        context.update({'consignment_book_sale': True})
        sale_order = self.env['sale.order'].with_context(context).create(vals_list)
        return res

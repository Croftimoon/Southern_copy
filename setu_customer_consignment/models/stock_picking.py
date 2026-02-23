from odoo import fields, models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    partner_id = fields.Many2one(
        'res.partner', 'Contact',
        check_company=True)

    order_count = fields.Integer(
        "Order Count",
        compute='_compute_order_count',
    )

    is_clear = fields.Boolean(string="Consignment Order is Clear", compute='_compute_is_clear',
                              help="This transfer is fully clear.")
    done_order = fields.Boolean(string="Consignment Order is Clear", compute='_compute_is_clear',
                                help="there is no product for sale order")
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type', index=True)
    picking_type_ids = fields.Many2many('stock.picking.type', 'consi_picking_type_rel', 'picking_id', 'picking_type_id',
                                        string="Operation Types", compute="_compute_picking_type_ids")
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        check_company=True, required=True)
    location_ids = fields.Many2many('stock.location', 'consi_picking_location_rel', 'picking_id', 'location_id',
                                    string="Locations", compute="_compute_location_ids")

    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)
        if self.env.context.get('is_consignment_picking', False) and not self:
            res['is_consignment_picking'] = True
            res['picking_type_id'] = self.env['stock.picking.type'].search(
                [('code', '=', 'internal'), ('company_id', '=', self.env.company.id),
                 ('warehouse_id.is_consignment_warehouse', '=', False)]).ids
        return res

    is_consignment_picking = fields.Boolean(string="Is Consignment Transfer")

    @api.depends('picking_type_id', 'partner_id')
    def _compute_location_id(self):
        res = super()._compute_location_id()
        for transfer in self:
            if transfer.is_consignment_picking:
                transfer.location_dest_id = transfer.partner_id.property_consignment_location_id.id

    @api.depends('is_consignment_picking')
    def _compute_picking_type_ids(self):
        for record in self:
            picking_types = self.env['stock.picking.type'].search(
                [('code', '=', 'internal'), ('warehouse_id.is_consignment_warehouse', '=', True)])
            record.picking_type_ids = picking_types if picking_types else False

    @api.depends('is_consignment_picking')
    def _compute_location_ids(self):
        for record in self:
            locations = self.env['stock.location'].search([('usage', '=', 'internal')])
            record.location_ids = locations if locations else False

    def action_book_sale(self):
        self.ensure_one()
        products = []
        if self:
            for line in self.move_ids:
                qty = line.product_uom_qty
                return_moves = line.move_dest_ids.filtered(lambda x: x.picking_id.state != 'cancel')
                if return_moves:
                    qty -= sum(return_moves.mapped('quantity_done'))

                sale_order_line = self.env['sale.order.line'].search([('product_id', '=', line.product_id.id),
                                                                      ('order_id.state', '!=', 'cancel'),
                                                                      ('order_id.transfer_id', '=', self.id),
                                                                      ('order_id.property_is_consignment_order', '=', True)])
                if sale_order_line:
                    qty -= sum(sale_order_line.mapped('product_uom_qty'))

                products.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': qty}))
        return {
            'name': 'Book Sale',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'setu.book.sale',
            'type': 'ir.actions.act_window',
            'view_id': self.env.ref('setu_customer_consignment.setu_book_sale_form').id,
            'context': {'consignment_book_sale': True,
                        'partner_id': self.partner_id.id,
                        'transfer_id': self.id,
                        'order_line': products},
            'target': 'new',
        }

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'name': 'Book Sale',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'domain': [('transfer_id', '=', self.id), ('state', '!=', 'cancel'),
                       ('property_is_consignment_order', '=', True)],
            'res_model': 'sale.order',
            'context': {'create': False, 'is_consignment_picking': False},
        }

    def _compute_order_count(self):
        for transfer in self:
            order = transfer.env['sale.order'].search(
                [('transfer_id', '=', transfer.id), ('property_is_consignment_order', '=', True),
                 ('state', '!=', 'cancel')])
            transfer.order_count = len(order)

    def _compute_is_clear(self):
        for transfer in self:
            transfer.is_clear = False
            transfer.done_order = False
            products = []
            if transfer.is_consignment_picking == True:
                transfer.done_order = True
            if transfer.location_id.is_consignment_location != True:
                transfer.is_clear = False
                transfer.done_order = True
                for line in transfer.move_line_ids:
                    qty = line.move_id.product_qty
                    return_moves = line.move_id.move_dest_ids.filtered(lambda x: x.picking_id.state != 'cancel')
                    if return_moves:
                        qty -= sum(return_moves.mapped('quantity'))
                    sale_order_line = transfer.env['sale.order.line'].search([('product_id', '=', line.product_id.id),
                                                                              ('order_id.state', '!=', 'cancel'),
                                                                              ('order_id.transfer_id', '=', transfer.id),
                                                                              ('order_id.property_is_consignment_order', '=', True)])
                    if sale_order_line:
                        qty -= sum(sale_order_line.mapped('product_uom_qty'))
                    products.append({'product_uom_qty': qty})

                for p in products:
                    if p['product_uom_qty'] == 0:
                        transfer.is_clear = True
                    if not p['product_uom_qty'] < 1:
                        transfer.done_order = False

    @api.model_create_multi
    def create(self, vals_list):
        for record in vals_list:
            if 'sale_id' in record:
                order_id = self.env['sale.order'].sudo().browse(record['sale_id'])
                location_id = order_id.partner_id.property_is_consignment_customer and order_id.partner_id.property_consignment_location_id or False
                if order_id.property_is_consignment_order and location_id:
                    record['location_id'] = location_id.id
        res = super(StockPicking, self).create(vals_list)
        return res

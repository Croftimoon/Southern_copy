from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lot_id = fields.Many2one(
        'stock.lot', 'Lot/Serial Number',
        domain="[('product_id', '=', product_id), ('location_id', '=', location_id)]", check_company=True)
    lot_name = fields.Char('Lot/Serial Number Name')

    location_id = fields.Many2one(
        'stock.location', "Source Location",
        compute="_compute_location_id", store=True, precompute=True, readonly=False,
        check_company=True, domain="[('warehouse_id', '=', order_warehouse_id)]")
    order_warehouse_id = fields.Many2one(
        related='order_id.warehouse_id',
        string="Warehouse",
        store=True, precompute=True)

    lots_visible = fields.Boolean(compute='_compute_lots_visible')

    replenish_stock = fields.Boolean("Replenish Stock", default=lambda self: self._default_replenish_stock())

    @api.model
    def _default_replenish_stock(self):
        return self.order_id.property_is_consignment_order

    @api.depends('product_id.tracking', 'product_id.property_is_consignment_product')
    def _compute_lots_visible(self):
        for line in self:
            line.lots_visible = line.product_id.tracking != 'none' and line.product_id.property_is_consignment_product

    @api.depends('order_partner_id', 'order_warehouse_id')
    def _compute_location_id(self):
        for line in self:
            location_id = line.order_partner_id.property_is_consignment_customer and line.order_partner_id.property_consignment_location_id
            if location_id:
                line.location_id = location_id
                continue

            picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('warehouse_id', '=', line.order_warehouse_id.id)], limit=1)
            line = line.with_company(line.company_id)
            if picking_type:
                if picking_type.default_location_src_id:
                    location_id = picking_type.default_location_src_id.id
                elif line.order_partner_id:
                    location_id = line.order_partner_id.property_stock_supplier.id
                else:
                    _customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

                line.location_id = location_id
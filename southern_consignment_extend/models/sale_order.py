from odoo import models, SUPERUSER_ID


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        super()._action_confirm()
        Picking = self.env['stock.picking'].with_user(SUPERUSER_ID).sudo()
        PickingType = self.env['stock.picking.type']
        StockMove = self.env['stock.move']

        note_subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')
        for order in self:
            for location, location_lines in order.order_line.filtered('replenish_stock').filtered('product_id').grouped('location_id').items():
                picking_type = PickingType.search([('warehouse_id', '=', location.warehouse_id.id), ('sequence_code', '=', 'CONSIGN')])
                new_picking = Picking.create({
                    'location_id': picking_type.default_location_src_id.id,
                    'location_dest_id': location.id,
                    'picking_type_id': picking_type.id,
                    'partner_id': order.partner_id.id,
                    'origin': f"{order.name} - Replenishment",
                    'is_locked': True,
                    'scheduled_date': order.date_order,
                    'date': order.date_order,
                    'is_consignment_picking': True,
                })
                new_picking.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': new_picking, 'origin': order},
                    subtype_id=note_subtype_id,
                )

                for key, lines in location_lines.grouped(lambda l: (l.product_id, l.product_uom)).items():
                    product_id, product_uom = key
                    uom_quantity = sum(lines.mapped('product_uom_qty'))
                    StockMove.create({
                        'sequence': 10,
                        'product_id': product_id.id,
                        'product_uom': product_uom.id,
                        'location_id': picking_type.default_location_src_id.id,
                        'location_dest_id': location.id,
                        'partner_id': order.partner_id.id,
                        'picking_id': new_picking.id,
                        'picking_type_id': picking_type.id,
                        'name': product_id.name,
                        'procure_method': 'make_to_stock',
                        'reference': new_picking.name,
                        'description_picking': product_id.name,
                        'product_uom_qty': uom_quantity,
                        'date': order.date_order,
                        'manual_consumption': True,
                    })


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    consignment_ids = fields.One2many('res.partner.consignment', string='Master Records', inverse_name='partner_id')

    _sql_constraints = [
        ('unique_ref', 'unique(ref)', 'The reference field must be unique.')
    ]

    @api.constrains('ref', 'property_is_consignment_customer')
    def _check_consignment_ref(self):
        for record in self:
            if record.property_is_consignment_customer and not record.ref:
                raise ValidationError(_('Reference is required for consignment customers.'))

    @api.onchange('ref')
    def _onchange_ref(self):
        for record in self:
            if record.property_is_consignment_customer and record.ref:
                self._update_consignment_location(record)

    def _update_consignment_location(self, record):
        if record.property_consignment_location_id:
            record.property_consignment_location_id.name = record.ref
        else:
            parent_location = self.env['stock.location'].search(
                [('usage', '=', 'view'), ('company_id', '=', self.env.company.id),
                 ('is_consignment_location', '=', True), ('partner_id', '=', False)])
            record.property_consignment_location_id = self.env['stock.location'].create(
                {'company_id': self.env.company.id,
                 'name': record.ref,
                 'usage': 'internal',
                 'location_id': parent_location.id,
                 'is_consignment_location': True,
                 'partner_id': record.id})

    def write(self, vals):
        if 'consignment_ids' in vals:
            for record in self:
                for child in vals['consignment_ids']:
                    command = child[0]
                    if command == fields.Command.DELETE:
                        consignment_id = child[1]
                        for consignment in record.consignment_ids:
                            if consignment.id == consignment_id:
                                product_id = consignment.product_id
                                rule = self.env['stock.warehouse.orderpoint'].search([
                                    ('product_id', '=', product_id.id),
                                    ('location_id', '=', record.property_consignment_location_id.id)
                                ])
                                if rule:
                                    rule.unlink()

        result = super().write(vals)
        if 'consignment_ids' not in vals:
            return result

        route_id = self.env['ir.config_parameter'].sudo().get_param('stock.consignment_default_route')

        for record in self:
            for consignment in record.consignment_ids:
                rule = self.env['stock.warehouse.orderpoint'].search([
                    ('product_id', '=', consignment.product_id.id),
                    ('location_id', '=', record.property_consignment_location_id.id)
                ])
                if rule:
                    rule.product_min_qty = consignment.quantity
                    rule.product_max_qty = consignment.quantity
                    rule.product_id = consignment.product_id
                else:
                    self.env['stock.warehouse.orderpoint'].create({
                        'location_id': record.property_consignment_location_id.id,
                        'route_id': int(route_id) if route_id else None,
                        'product_id': consignment.product_id.id,
                        'product_min_qty': consignment.quantity,
                        'product_max_qty': consignment.quantity,
                    })

        return result
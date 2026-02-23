# File: models/stock_location.py
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class StockLocation(models.Model):
    _inherit = 'stock.location'

    # Replace the old partner_id field with Many2many for multiple customers
    consignment_partner_ids = fields.Many2many(
        'res.partner',
        'location_consignment_partner_rel',
        'location_id',
        'partner_id',
        string="Consignment Customers",
        compute='_compute_consignment_partner_ids',
        store=True,
        help="Partners who have this location assigned as their consignment location"
    )

    is_consignment_location = fields.Boolean(
        string="Is Consignment Location",
        default=False,
        help="Mark this location as used for consignment inventory"
    )

    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)
        if self.env.context.get('is_consignment_location', False):
            res['is_consignment_location'] = True
        return res

    @api.depends('is_consignment_location')
    def _compute_consignment_partner_ids(self):
        """Compute which partners are using this location"""
        for location in self:
            if not location.is_consignment_location:
                location.consignment_partner_ids = False
                continue

            # Find all partners who have this location as their consignment location
            partners = self.env['res.partner'].search([
                ('property_is_consignment_customer', '=', True),
            ])

            # Filter partners who actually have this location assigned
            assigned_partners = self.env['res.partner']
            for partner in partners:
                try:
                    if partner.property_consignment_location_id.id == location.id:
                        assigned_partners |= partner
                except:
                    continue

            location.consignment_partner_ids = assigned_partners
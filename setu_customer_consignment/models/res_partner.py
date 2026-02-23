# File: models/res_partner.py (Updated to trigger location recomputation)
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_is_consignment_customer = fields.Boolean(
        string="Is Consignment Customer",
        company_dependent=True,
        default=False,
        help="Check this to enable consignment functionality for this customer"
    )

    property_consignment_location_id = fields.Many2one(
        'stock.location',
        string="Consignment Location",
        company_dependent=True,
        domain="[('is_consignment_location', '=', True), ('usage', '=', 'internal'), ('company_id', '=', current_company_id)]",
        help="Stock location where consignment products for this customer are stored",
        context={'default_is_consignment_location': True, 'default_usage': 'internal'}
    )

    @api.model
    def default_get(self, default_fields):
        res = super().default_get(default_fields)
        if self.env.context.get('property_is_consignment_customer', False):
            res['property_is_consignment_customer'] = True
        return res

    @api.onchange('property_is_consignment_customer')
    def _onchange_consignment_customer(self):
        """Handle consignment customer flag changes"""
        if self.property_is_consignment_customer and not self.property_consignment_location_id:
            return {
                'warning': {
                    'title': _('Consignment Location Required'),
                    'message': _(
                        'A consignment location will be created automatically when you save this record, or you can select an existing one.')
                }
            }
        elif not self.property_is_consignment_customer:
            self.property_consignment_location_id = False

    def create_consignment_location(self):
        """Create consignment location for this partner"""
        self.ensure_one()

        if not self.property_is_consignment_customer:
            raise UserError(_("This partner is not marked as a consignment customer."))

        if self.property_consignment_location_id:
            return self.property_consignment_location_id

        try:
            parent_location = self._get_or_create_consignment_parent()
            location_name = self._generate_location_name()

            location = self.env['stock.location'].create({
                'name': location_name,
                'usage': 'internal',
                'location_id': parent_location.id,
                'is_consignment_location': True,
                'company_id': self.env.company.id,
            })

            self.property_consignment_location_id = location.id
            return location

        except Exception as e:
            _logger.error(f"Failed to create consignment location for {self.name}: {str(e)}")
            raise UserError(_(
                "Failed to create consignment location for %s. Error: %s"
            ) % (self.name, str(e)))

    def _get_or_create_consignment_parent(self):
        """Get or create the parent consignment location for current company"""
        parent_location = self.env['stock.location'].search([
            ('usage', '=', 'view'),
            ('company_id', '=', self.env.company.id),
            ('is_consignment_location', '=', True),
            ('name', 'like', 'Consignment%')
        ], limit=1)

        if not parent_location:
            parent_location = self.env['stock.location'].create({
                'name': f"Consignment Locations - {self.env.company.name}",
                'usage': 'view',
                'location_id': self.env.ref('stock.stock_location_locations').id,
                'is_consignment_location': True,
                'company_id': self.env.company.id,
            })

        return parent_location

    def _generate_location_name(self):
        """Generate unique location name for the partner"""
        base_name = f"Consignment - {self.name}"
        if self.ref:
            base_name = f"Consignment - {self.ref} ({self.name})"

        existing = self.env['stock.location'].search([
            ('name', '=like', f"{base_name}%"),
            ('company_id', '=', self.env.company.id)
        ])

        if not existing:
            return base_name

        counter = 1
        while True:
            new_name = f"{base_name} ({counter})"
            if not self.env['stock.location'].search([
                ('name', '=', new_name),
                ('company_id', '=', self.env.company.id)
            ]):
                return new_name
            counter += 1

    def action_create_consignment_location(self):
        """Action to manually create consignment location"""
        for record in self:
            if record.property_is_consignment_customer:
                record.create_consignment_location()

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-create consignment locations for new consignment customers"""
        records = super(ResPartner, self).create(vals_list)

        consignment_partners = records.filtered('property_is_consignment_customer')
        for partner in consignment_partners:
            if not partner.property_consignment_location_id:
                try:
                    partner.create_consignment_location()
                except Exception as e:
                    _logger.warning(f"Could not auto-create consignment location for {partner.name}: {str(e)}")

        return records

    def write(self, vals):
        """Handle consignment customer updates and trigger location recomputation"""
        # Store locations that need recomputation
        locations_to_update = self.env['stock.location']

        # Collect old locations
        if 'property_consignment_location_id' in vals:
            for partner in self:
                if partner.property_consignment_location_id:
                    locations_to_update |= partner.property_consignment_location_id

        result = super(ResPartner, self).write(vals)

        # Handle consignment location creation
        if vals.get('property_is_consignment_customer'):
            for partner in self.filtered(
                    lambda p: p.property_is_consignment_customer and not p.property_consignment_location_id):
                try:
                    partner.create_consignment_location()
                except Exception as e:
                    _logger.warning(f"Could not auto-create consignment location for {partner.name}: {str(e)}")

        # Add new locations and trigger recomputation
        if 'property_consignment_location_id' in vals:
            for partner in self:
                if partner.property_consignment_location_id:
                    locations_to_update |= partner.property_consignment_location_id

            # Recompute affected locations
            if locations_to_update:
                locations_to_update._compute_consignment_partner_ids()

        return result

    def unlink(self):
        """Handle partner deletion - trigger location recomputation"""
        locations_to_update = self.env['stock.location']

        for record in self:
            if record.property_consignment_location_id:
                locations_to_update |= record.property_consignment_location_id

        result = super(ResPartner, self).unlink()

        # Update location relationships after deletion
        if locations_to_update:
            locations_to_update._compute_consignment_partner_ids()

        return result
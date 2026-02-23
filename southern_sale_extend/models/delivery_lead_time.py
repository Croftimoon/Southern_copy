# models/delivery_lead_time.py
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class DeliveryLeadTime(models.Model):
    _name = 'delivery.lead.time'
    _description = 'Delivery Lead Times'
    _order = 'country_id, state_id, start_postcode, end_postcode'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        required=True,
        default=lambda self: self.env.company.country_id
    )
    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        domain="[('country_id', '=', country_id)]"
    )
    start_postcode = fields.Char(string='Start Postcode')
    end_postcode = fields.Char(string='End Postcode')
    lead_days = fields.Integer(string='Lead Days', required=True, default=1)
    active = fields.Boolean(string='Active', default=True)

    @api.depends('country_id', 'state_id', 'start_postcode', 'end_postcode')
    def _compute_name(self):
        for record in self:
            name_parts = []
            if record.country_id:
                name_parts.append(record.country_id.name)
            if record.state_id:
                name_parts.append(record.state_id.name)
            if record.start_postcode and record.end_postcode:
                name_parts.append(f"{record.start_postcode}-{record.end_postcode}")
            elif record.start_postcode:
                name_parts.append(record.start_postcode)

            record.name = ' - '.join(name_parts) if name_parts else 'New Lead Time'

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            self.state_id = False

    @api.constrains('start_postcode', 'end_postcode', 'country_id', 'state_id')
    def _check_postcode_range_overlap(self):
        """Prevent overlapping postcode ranges for the same country/state"""
        for record in self:
            if record.start_postcode and record.end_postcode:
                # Check for overlapping ranges with specific postcodes
                domain = [
                    ('id', '!=', record.id),
                    ('country_id', '=', record.country_id.id if record.country_id else False),
                    ('state_id', '=', record.state_id.id if record.state_id else False),
                    ('start_postcode', '!=', False),
                    ('end_postcode', '!=', False),
                    ('active', '=', True)
                ]

                existing_ranges = self.search(domain)

                for existing in existing_ranges:
                    # Check if ranges overlap
                    if self._ranges_overlap(
                            record.start_postcode, record.end_postcode,
                            existing.start_postcode, existing.end_postcode
                    ):
                        location = f"{record.country_id.name}"
                        if record.state_id:
                            location += f", {record.state_id.name}"

                        raise ValidationError(_(
                            "Postcode range %s-%s overlaps with existing range %s-%s for %s."
                        ) % (
                                                  record.start_postcode, record.end_postcode,
                                                  existing.start_postcode, existing.end_postcode,
                                                  location
                                              ))

            elif not record.start_postcode and not record.end_postcode:
                # Check for duplicate default entries (blank postcodes)
                domain = [
                    ('id', '!=', record.id),
                    ('country_id', '=', record.country_id.id if record.country_id else False),
                    ('state_id', '=', record.state_id.id if record.state_id else False),
                    ('start_postcode', '=', False),
                    ('end_postcode', '=', False),
                    ('active', '=', True)
                ]

                if self.search_count(domain) > 0:
                    location = f"{record.country_id.name}"
                    if record.state_id:
                        location += f", {record.state_id.name}"
                    else:
                        location += " (default)"

                    raise ValidationError(_(
                        "A default lead time (without postcode range) already exists for %s."
                    ) % location)

    @api.constrains('start_postcode', 'end_postcode')
    def _check_postcode_range_validity(self):
        """Ensure start postcode is not greater than end postcode"""
        for record in self:
            if record.start_postcode and record.end_postcode:
                if record.start_postcode > record.end_postcode:
                    raise ValidationError(_(
                        "Start postcode (%s) cannot be greater than end postcode (%s)."
                    ) % (record.start_postcode, record.end_postcode))
            elif (record.start_postcode and not record.end_postcode) or (
                    record.end_postcode and not record.start_postcode):
                raise ValidationError(_(
                    "Both start and end postcodes must be filled for a postcode range, or both left blank for a default rule."
                ))

    def _ranges_overlap(self, start1, end1, start2, end2):
        """Check if two postcode ranges overlap"""
        # Convert to strings for comparison if needed
        start1, end1, start2, end2 = str(start1), str(end1), str(start2), str(end2)

        # Ranges overlap if: start1 <= end2 and start2 <= end1
        return start1 <= end2 and start2 <= end1

    @api.model
    def get_lead_days(self, partner_id, country_id=None, state_id=None, zip_code=None):
        """
        Get lead days for delivery based on partner shipping address
        """
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            country_id = partner.country_id.id if partner.country_id else country_id
            state_id = partner.state_id.id if partner.state_id else state_id
            zip_code = partner.zip or zip_code

        if not country_id:
            return 1  # Default lead time

        domain = [('country_id', '=', country_id), ('active', '=', True)]

        if state_id:
            domain.append(('state_id', '=', state_id))

        # First try to find exact postcode match
        if zip_code:
            postcode_domain = domain + [
                ('start_postcode', '!=', False),
                ('end_postcode', '!=', False),
                ('start_postcode', '<=', zip_code),
                ('end_postcode', '>=', zip_code)
            ]
            lead_time = self.search(postcode_domain, limit=1)
            if lead_time:
                return lead_time.lead_days

        # If no postcode match, try country and state with blank postcodes
        fallback_domain = domain + [
            ('start_postcode', '=', False),
            ('end_postcode', '=', False)
        ]
        lead_time = self.search(fallback_domain, limit=1)
        if lead_time:
            return lead_time.lead_days

        # Final fallback - just country match with blank postcodes
        country_domain = [
            ('country_id', '=', country_id),
            ('state_id', '=', False),
            ('start_postcode', '=', False),
            ('end_postcode', '=', False),
            ('active', '=', True)
        ]
        lead_time = self.search(country_domain, limit=1)
        if lead_time:
            return lead_time.lead_days

        return 1  # Ultimate fallback
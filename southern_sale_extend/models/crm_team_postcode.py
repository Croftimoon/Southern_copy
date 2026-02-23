# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class CrmTeamPostcode(models.Model):
    _name = 'crm.team.postcode'
    _description = 'Sales Team Postcode Range'
    _order = 'start_postcode'

    team_id = fields.Many2one(
        'crm.team',
        string='Sales Team',
        required=True,
        ondelete='cascade'
    )
    start_postcode = fields.Char(
        string='Start Postcode',
        required=True,
        help='Start postcode of the range (or single postcode)'
    )
    end_postcode = fields.Char(
        string='End Postcode',
        required=True,
        help='End postcode of the range'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default end_postcode to start_postcode value"""
        defaults = super().default_get(fields_list)
        if 'start_postcode' in defaults and 'end_postcode' not in defaults:
            defaults['end_postcode'] = defaults['start_postcode']
        return defaults

    @api.constrains('start_postcode', 'end_postcode')
    def _check_postcode_values(self):
        """Validate postcode entries"""
        for record in self:
            if not record.start_postcode:
                raise ValidationError(_('Start postcode is required.'))
            if not record.end_postcode:
                record.end_postcode = record.start_postcode
            if record.start_postcode > record.end_postcode:
                raise ValidationError(_('Start postcode must be less than or equal to end postcode.'))

    @api.constrains('start_postcode', 'end_postcode', 'team_id')
    def _check_postcode_overlap(self):
        """Ensure no postcode overlaps between teams"""
        for record in self:
            # Ensure end_postcode is set
            if not record.end_postcode:
                record.end_postcode = record.start_postcode

            domain = [
                ('id', '!=', record.id),
                ('team_id', '!=', record.team_id.id),
            ]

            existing_postcodes = self.search(domain)

            start, end = record.start_postcode, record.end_postcode
            for existing in existing_postcodes:
                # Ensure existing end_postcode is set
                existing_end = existing.end_postcode or existing.start_postcode

                # Check range overlap
                if not (end < existing.start_postcode or start > existing_end):
                    if existing.start_postcode == existing_end:
                        # Existing is single postcode
                        raise ValidationError(_(
                            'Postcode range %s-%s contains existing postcode %s for team %s'
                        ) % (start, end, existing.start_postcode, existing.team_id.name))
                    else:
                        # Existing is range
                        raise ValidationError(_(
                            'Postcode range %s-%s overlaps with existing range %s-%s for team %s'
                        ) % (start, end, existing.start_postcode, existing_end, existing.team_id.name))

    @api.onchange('start_postcode')
    def _onchange_start_postcode(self):
        """Auto-fill end_postcode when start_postcode changes"""
        if self.start_postcode and not self.end_postcode:
            self.end_postcode = self.start_postcode

    def write(self, vals):
        """Ensure end_postcode is set and trigger recalculation when postcodes change"""
        # Ensure end_postcode is always set
        if 'start_postcode' in vals and 'end_postcode' not in vals:
            vals['end_postcode'] = vals['start_postcode']
        elif 'end_postcode' in vals and not vals['end_postcode']:
            vals['end_postcode'] = vals.get('start_postcode', self.start_postcode)

        result = super().write(vals)
        if any(field in vals for field in ['start_postcode', 'end_postcode']):
            self.team_id.recalculate_all_sales_teams()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-set end_postcode and trigger recalculation when postcodes are created"""
        for vals in vals_list:
            if 'start_postcode' in vals and 'end_postcode' not in vals:
                vals['end_postcode'] = vals['start_postcode']
            elif 'end_postcode' in vals and not vals['end_postcode']:
                vals['end_postcode'] = vals.get('start_postcode', '')

        records = super().create(vals_list)
        for record in records:
            record.team_id.recalculate_all_sales_teams()
        return records

    def unlink(self):
        """Trigger recalculation when postcodes are deleted"""
        teams = self.mapped('team_id')
        result = super().unlink()
        for team in teams:
            team.recalculate_all_sales_teams()
        return result
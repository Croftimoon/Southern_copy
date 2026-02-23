from odoo import models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _prepare_customer_statement_values(self, options=None):
        """Override to add patient_name to statement lines"""
        # Get the original values
        values = super()._prepare_customer_statement_values(options)

        # Add patient_name to each line by looking up the move_id
        lines = values.get('lines', {})

        for partner_id, partner_lines in lines.items():
            for line in partner_lines:
                # Skip initial balance line
                if line.get('activity') == 'Initial Balance':
                    line['patient_name'] = ''
                    continue

                # For other lines, try to get patient_name from the move
                patient_name = ''
                activity = line.get('activity', '')

                # Find the move by name/reference
                if activity:
                    moves = self.env['account.move'].search([
                        ('name', '=', activity),
                        ('partner_id', '=', int(partner_id))
                    ], limit=1)

                    if moves and hasattr(moves, 'patient_name'):
                        patient_name = moves.patient_name or ''

                line['patient_name'] = patient_name

        return values

    @api.constrains('zip', 'country_id')
    def _check_required_fields(self):
        """Make postcode and country mandatory for customers and addresses"""
        for partner in self:
            if partner.is_company or partner.parent_id or partner.type != 'contact':
                if not partner.zip:
                    raise ValidationError(_('Postcode is mandatory for customers and addresses.'))
                if not partner.state_id:
                    raise ValidationError(_('State is mandatory for customers and addresses.'))
                if not partner.country_id:
                    raise ValidationError(_('Country is mandatory for customers and addresses.'))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.zip and record.country_id and not record.team_id and not self.env.context.get('skip_team_recalc'):
                team = self.env['crm.team']._get_team_by_postcode(
                    record.zip,
                    record.country_id.id,
                    record.state_id.id if record.state_id else False
                )
                if team:
                    record.with_context(skip_team_recalc=True).team_id = team
                    record.with_context(skip_team_recalc=True).child_ids.filtered(lambda x: x.type == "contact").team_id = team
        return records

    def write(self, vals):
        result = super().write(vals)

        if any(field in vals for field in ['zip', 'country_id', 'state_id']) and not self.env.context.get('skip_team_recalc'):
            for partner in self:
                if partner.zip and partner.country_id:
                    team = self.env['crm.team']._get_team_by_postcode(
                        partner.zip,
                        partner.country_id.id,
                        partner.state_id.id if partner.state_id else False
                    )
                    if team and team:
                        partner.with_context(skip_team_recalc=True).team_id = team
                        partner.with_context(skip_team_recalc=True).child_ids.filtered(lambda x: x.type == "contact").team_id = team

        return result
from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = "crm.team"

    code = fields.Char(string='Code', required=False)
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        required=True,
        default=lambda self: self.env.company.country_id,
        help='Country for this sales team'
    )
    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        domain="[('country_id', '=', country_id)]",
        help='State for this sales team'
    )
    postcode_ids = fields.One2many(
        'crm.team.postcode',
        'team_id',
        string='Postcodes',
        help='Postcode ranges assigned to this sales team'
    )

    @api.onchange('country_id')
    def _onchange_country_id(self):
        """Clear state when country changes"""
        if self.country_id != self.state_id.country_id:
            self.state_id = False

    def _get_team_by_postcode(self, postcode, country_id=False, state_id=False):
        """Find sales team with hierarchical fallback logic"""
        if not postcode or not country_id:
            return self.env['crm.team']

        # Step 1: Try to find by postcode only (ignore country and state)
        domain = [
            ('start_postcode', '<=', postcode),
            ('end_postcode', '>=', postcode),
        ]
        team_postcode = self.env['crm.team.postcode'].search(domain, limit=1)
        if team_postcode:
            return team_postcode.team_id

        # Step 2: Try to find by country and state (no postcode restriction)
        if state_id:
            domain = [
                ('country_id', '=', country_id),
                ('state_id', '=', state_id),
                ('postcode_ids', '=', False),  # Teams without specific postcodes
            ]
            teams = self.search(domain, limit=1)
            if teams:
                return teams

        # Step 3: Finally, try to find by country only (no postcode or state restriction)
        domain = [
            ('country_id', '=', country_id),
            ('state_id', '=', False),  # Teams without specific state
            ('postcode_ids', '=', False),  # Teams without specific postcodes
        ]
        teams = self.search(domain, limit=1)
        return teams

    def recalculate_all_sales_teams(self):
        """Recalculate sales teams for all partners when postcodes change"""
        partners = self.env['res.partner'].search([
            ('zip', '!=', False),
            ('zip', '!=', ''),
            ('country_id', '!=', False),
        ])

        for partner in partners:
            team = self._get_team_by_postcode(
                partner.zip,
                partner.country_id.id,
                partner.state_id.id if partner.state_id else False
            )
            if team:
                partner.with_context(skip_team_recalc=True).team_id = team
                partner.with_context(skip_team_recalc=True).child_ids.filtered(lambda x: x.type == "contact").team_id = team
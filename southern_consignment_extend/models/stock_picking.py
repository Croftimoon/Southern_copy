import logging
from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def auto_validate_delivery_orders(self):
         # Auto-validate delivery orders for consignment customers and locations
        pickings = self.search([
            ('state', 'in', ['assigned', 'confirmed']),
            ('picking_type_code', '=', 'outgoing'),
            ('partner_id.property_is_consignment_customer', '=', True),
            ('location_id.is_consignment_location', '=', True)
        ])

        for picking in pickings:
            try:
                picking.with_context(is_auto_validate=True).button_validate()
            except Exception as e:
                _logger.error(f"Auto-validation failed for picking {picking.name}: {str(e)}")

    def _sanity_check(self, separate_pickings=True):
        """ Sanity check for `button_validate()`
            :param separate_pickings: Indicates if pickings should be checked independently for lot/serial numbers or not.
        """
        if not self._context.get('is_auto_validate', False):
            pickings_without_tracking_numbers = self.browse()
            for picking in self:
                if picking.picking_type_code == 'outgoing' and not picking.carrier_tracking_ref:
                    pickings_without_tracking_numbers |= picking

            if pickings_without_tracking_numbers:
                if not self._should_show_transfers():
                    raise UserError(_("You need to supply a tracking reference."))
                else:
                    raise UserError(_('Transfers %s: You need to supply a tracking reference.',
                                      ', '.join(pickings_without_tracking_numbers.mapped('name'))).lstrip())

        super()._sanity_check(separate_pickings)

    def _is_to_external_location(self):
        self.ensure_one()
        return super()._is_to_external_location() or self.is_consignment_picking
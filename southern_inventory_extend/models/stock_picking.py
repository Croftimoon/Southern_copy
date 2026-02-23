from odoo import models, fields, api
import re
import logging

_logger = logging.getLogger(__name__)
class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('carrier_tracking_ref')
    def _onchange_carrier_tracking_ref(self):
        """Apply carrier-specific regex to extract tracking number from barcode"""
        if self.carrier_tracking_ref and self.carrier_id and self.carrier_id.tracking_ref_regex:
            processed_value = self.carrier_id._apply_tracking_regex(self.carrier_tracking_ref)
            if processed_value != self.carrier_tracking_ref:
                self.carrier_tracking_ref = processed_value

    @api.onchange('carrier_id')
    def _onchange_carrier_id(self):
        """When carrier changes, reprocess the tracking reference if it exists"""
        if self.carrier_tracking_ref and self.carrier_id and self.carrier_id.tracking_ref_regex:
            processed_value = self.carrier_id._apply_tracking_regex(self.carrier_tracking_ref)
            if processed_value != self.carrier_tracking_ref:
                self.carrier_tracking_ref = processed_value
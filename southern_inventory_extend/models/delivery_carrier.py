from odoo import models, fields, api
import re
import logging

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    tracking_ref_regex = fields.Char(
        string='Tracking Reference Regex',
        help='Regular expression to extract tracking number from scanned barcode. '
             'Use capturing groups to specify which part to extract. '
             'Leave empty to use the full scanned value.'
    )

    def _apply_tracking_regex(self, value):
        """Apply the regex pattern to extract tracking reference"""
        if not self.tracking_ref_regex or not value:
            return value

        try:
            match = re.search(self.tracking_ref_regex, value)
            if match:
                # If there are capturing groups, use the first one
                if match.groups():
                    return match.group(1)
                # Otherwise use the full match
                else:
                    return match.group(0)
            else:
                # If no match, return original value
                return value
        except re.error as e:
            _logger.warning(f"Invalid regex pattern '{self.tracking_ref_regex}': {e}")
            return value
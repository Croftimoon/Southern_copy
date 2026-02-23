import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    set_consignment_default_route = fields.Boolean(config_parameter='stock.set_consignment_default_route')
    consignment_default_route = fields.Many2one('stock.route', config_parameter='stock.consignment_default_route',
                                                 help="This determines what will be the default route for consignment rules")
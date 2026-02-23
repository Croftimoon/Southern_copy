from odoo import models, fields

class ImportScriptLine(models.TransientModel):
    _name = 'import.script.wizard.line'
    _description = 'Single Script Upload Line'

    wizard_id = fields.Many2one('import.script.wizard', required=True, ondelete='cascade')
    name = fields.Char()
    file = fields.Binary(required=True)
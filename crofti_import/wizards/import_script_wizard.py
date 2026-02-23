import base64
import io
import zipfile
from odoo import models, fields

class ImportScriptWizard(models.TransientModel):
    _name = 'import.script.wizard'
    _description = 'Multi-Script Upload Wizard'

    script_line_ids = fields.One2many('import.script.wizard.line', 'wizard_id', string="Files")

    def action_upload_scripts(self):
        import_scripts = self.env['import.script']
        for line in self.script_line_ids:
            if line.name.endswith('.zip'):
                file_data = base64.b64decode(line.file)
                with zipfile.ZipFile(io.BytesIO(file_data), 'r') as zip_file:
                    for zip_info in zip_file.infolist():
                        if zip_info.is_dir():
                            continue
                        filename = zip_info.filename
                        content = zip_file.read(zip_info)
                        if filename.endswith('.sql') or filename.endswith('.py'):
                            existing = import_scripts.search([('name', '=', filename)], limit=1)
                            encoded_content = base64.b64encode(content)
                            if existing:
                                existing.write({ 'file': encoded_content})
                            else:
                                import_scripts.create({
                                    'name': filename,
                                    'file': encoded_content,
                                })
            else:
                import_scripts.create({
                    'name': line.name,
                    'file': line.file,
                })
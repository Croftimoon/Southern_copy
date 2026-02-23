import base64
import csv
import io

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class QueryCSVWizard(models.TransientModel):
    _name = 'query.csv.wizard'
    _description = 'SQL Query to CSV Export'

    query = fields.Text(string="SQL Query", required=True)
    file = fields.Binary(readonly=True)
    filename = fields.Char(readonly=True)

    def action_run_query(self):
        self.ensure_one()
        query = self.query.strip().rstrip(';')

        try:
            self.env.cr.execute(query)
            headers = [desc[0] for desc in self.env.cr.description]
            rows = self.env.cr.fetchall()

            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(headers)
            writer.writerows(rows)

            csv_data = buffer.getvalue().encode('utf-8')
            buffer.close()

            self.write({
                'file': base64.b64encode(csv_data),
                'filename': 'query_results.csv',
            })

            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/?model={self._name}&id={self.id}&field=file&download=true&filename={self.filename}',
                'target': 'self',
            }

        except Exception as e:
            raise UserError(f"Query failed:\n{e}")
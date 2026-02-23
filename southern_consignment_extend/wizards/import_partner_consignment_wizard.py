import base64
import io
import openpyxl

from odoo import models, fields
from odoo.exceptions import UserError

class ImportPartnerConsignmentWizard(models.TransientModel):
    _name = 'import.partner.consignment.wizard'
    _description = 'Master Record Import Wizard'

    file = fields.Binary(string='Excel File', required=True)
    filename = fields.Char()

    def action_import_excel(self):
        if not self.file:
            raise UserError("Please upload an Excel file.")

        partner_id = self.env.context.get('active_id')
        if not partner_id:
            raise UserError("Missing partner context.")

        content = base64.b64decode(self.file)
        workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheet = workbook.active

        created = 0
        product_ids = []
        for row in sheet.iter_rows(min_row=2, values_only=True):  # skip header
            product_code_or_name, qty = row[:2]
            if not product_code_or_name:
                continue

            try:
                qty = float(qty)
            except (TypeError, ValueError):
                raise UserError(f"Invalid quantity for product '{product_code_or_name}': not a number")

            if qty <= 0:
                raise UserError(f"Invalid quantity for product '{product_code_or_name}': must be greater than 0")

            product = self.env['product.product'].search([
                '|', ('default_code', '=', product_code_or_name), ('name', '=', product_code_or_name)
            ], limit=1)

            if not product:
                raise UserError(f"Product not found: {product_code_or_name}")

            if product.id in product_ids:
                raise UserError(f"Product {product_code_or_name} was specified multiple times")

            product_ids.append(product.id)

            self.env['res.partner.consignment'].create({
                'partner_id': partner_id,
                'product_id': product.id,
                'quantity': qty,
            })
            created += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'{created} records imported successfully.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
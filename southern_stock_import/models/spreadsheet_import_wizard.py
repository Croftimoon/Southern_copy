import base64
import io
import csv
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    import xlrd
    import openpyxl
except ImportError:
    xlrd = None
    openpyxl = None

_logger = logging.getLogger(__name__)


class SpreadsheetImportWizard(models.TransientModel):
    _name = 'spreadsheet.import.wizard'
    _description = 'Spreadsheet Import Wizard'

    # Basic fields
    file_data = fields.Binary(string='Spreadsheet File', required=True)
    file_name = fields.Char(string='File Name')
    order_type = fields.Selection([
        ('sale', 'Sales Order'),
        ('purchase', 'Purchase Order'),
        ('stock', 'Stock Transfer')
    ], string='Order Type', required=True)
    order_id = fields.Integer(string='Order ID')

    # Configuration fields
    first_row_is_header = fields.Boolean(string='First row contains headers', default=True)
    first_row_preview = fields.Html(string='First Row Preview', readonly=True)

    # Column selection fields - will be populated by custom dropdown widget
    product_column_index = fields.Char(string='Product Code Column', required=True)
    quantity_column_index = fields.Char(string='Quantity Column', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if active_model == 'sale.order':
            res['order_type'] = 'sale'
            res['order_id'] = active_id
        elif active_model == 'purchase.order':
            res['order_type'] = 'purchase'
            res['order_id'] = active_id
        elif active_model == 'stock.picking':
            res['order_type'] = 'stock'
            res['order_id'] = active_id

        return res

    @api.model
    def parse_file_preview(self, file_data, file_name):
        """RPC endpoint to parse file and return preview data with column options"""
        try:
            # Decode the base64 file data
            file_content = base64.b64decode(file_data)
            file_ext = file_name.lower().split('.')[-1]

            # Parse the file
            if file_ext == 'csv':
                data = self._read_csv(file_content)
            elif file_ext in ['xlsx', 'xls']:
                data = self._read_excel(file_content)
            else:
                return {
                    'success': False,
                    'error': f"Unsupported file format: {file_ext}"
                }

            if not data:
                return {
                    'success': False,
                    'error': "No data found in file"
                }

            # Generate column options for dropdown
            first_row = data[0] if data else []
            column_options = []
            for i, header in enumerate(first_row, 1):
                clean_header = (header or '').strip() or f'Column {i}'
                column_options.append({
                    'value': str(i),
                    'label': f'{i}: {clean_header}'
                })

            # Generate preview HTML
            preview_html = self._generate_preview_html(data)

            return {
                'success': True,
                'data': data[:10],  # First 10 rows for reference
                'column_options': column_options,
                'preview_html': preview_html,
                'total_rows': len(data)
            }

        except Exception as e:
            _logger.error(f"Error parsing file {file_name}: {str(e)}")
            return {
                'success': False,
                'error': f"Error parsing file: {str(e)}"
            }

    def _generate_preview_html(self, data):
        """Generate HTML preview of the data"""
        if not data:
            return "<p>No data to preview</p>"

        preview_rows = data[:5]  # Show first 5 rows
        html = '<table class="table table-bordered table-sm" style="font-size: 12px; margin-top: 10px;">'

        # Show column numbers and headers
        html += '<thead class="table-light"><tr>'
        for i, header in enumerate(data[0], 1):
            clean_header = (header or '').strip() or f'Column {i}'
            html += f'<th style="text-align: center; padding: 4px; font-size: 11px;">{i}: {clean_header}</th>'
        html += '</tr></thead><tbody>'

        # Show data rows (skip header if configured)
        for row in data[1:6]:  # Show next 5 rows after header
            html += '<tr>'
            for cell in row:
                clean_cell = (cell or '').strip() or '(empty)'
                if len(clean_cell) > 20:
                    clean_cell = clean_cell[:20] + '...'
                html += f'<td style="padding: 3px; text-align: center; font-size: 11px;">{clean_cell}</td>'
            html += '</tr>'

        html += '</tbody></table>'

        if len(data) > 6:
            html += f'<p class="text-muted" style="margin-top: 5px;"><small>Showing first 5 rows of {len(data)} total rows</small></p>'

        return html

    def _read_csv(self, file_data):
        """Read CSV file data"""
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                content = file_data.decode(encoding)
                for delimiter in [',', ';', '\t', '|']:
                    try:
                        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
                        data = []
                        for row in reader:
                            if any(cell.strip() for cell in row):
                                data.append([cell.strip() for cell in row])
                        if len(data) > 0 and len(data[0]) > 1:
                            return data
                    except:
                        continue
            except UnicodeDecodeError:
                continue
        raise UserError(_("Cannot read CSV file - unable to detect encoding or delimiter"))

    def _read_excel(self, file_data):
        """Read Excel file data"""
        data = []

        # Try openpyxl first (for .xlsx)
        if openpyxl:
            try:
                workbook = openpyxl.load_workbook(io.BytesIO(file_data), data_only=True)
                sheet = workbook.active

                for row in sheet.iter_rows(values_only=True):
                    if any(cell is not None and str(cell).strip() for cell in row):
                        clean_row = []
                        for cell in row:
                            if cell is None:
                                clean_row.append('')
                            else:
                                clean_row.append(str(cell).strip())
                        data.append(clean_row)

                if data:
                    return data
            except Exception as e:
                _logger.warning(f"openpyxl failed: {str(e)}")

        # Try xlrd as fallback (for .xls)
        if xlrd:
            try:
                workbook = xlrd.open_workbook(file_contents=file_data)
                sheet = workbook.sheet_by_index(0)

                for row_idx in range(sheet.nrows):
                    row = []
                    has_data = False
                    for col_idx in range(sheet.ncols):
                        cell_value = sheet.cell_value(row_idx, col_idx)
                        if isinstance(cell_value, float) and cell_value.is_integer():
                            cell_value = int(cell_value)
                        cell_str = str(cell_value).strip()
                        row.append(cell_str)
                        if cell_str:
                            has_data = True

                    if has_data:
                        data.append(row)

                if data:
                    return data
            except Exception as e:
                _logger.warning(f"xlrd failed: {str(e)}")

        raise UserError(_("Cannot read Excel file - please ensure openpyxl or xlrd is installed"))

    def action_import(self):
        """Import data into order"""
        if not self.product_column_index or not self.quantity_column_index:
            raise UserError(_("Please select columns"))

        if not self.file_data:
            raise UserError(_("No file data found. Please upload a file first."))

        try:
            data = []
            # Decode the base64 file data
            file_content = base64.b64decode(self.file_data)
            file_ext = self.file_name.lower().split('.')[-1]

            # Parse the file
            if file_ext == 'csv':
                data = self._read_csv(file_content)
            elif file_ext in ['xlsx', 'xls']:
                data = self._read_excel(file_content)
        except:
            raise UserError(_("Invalid file data. Please upload a file again."))

        if not data:
            raise UserError(_("No data to import"))

        # Get order/picking
        if self.order_type == 'sale':
            order = self.env['sale.order'].browse(self.order_id)
            line_model = 'sale.order.line'
        elif self.order_type == 'purchase':
            order = self.env['purchase.order'].browse(self.order_id)
            line_model = 'purchase.order.line'
        elif self.order_type == 'stock':
            picking = self.env['stock.picking'].browse(self.order_id)
            line_model = 'stock.move'

        # Skip header if needed
        start_row = 1 if self.first_row_is_header else 0
        rows = data[start_row:]

        product_col = int(self.product_column_index) - 1
        quantity_col = int(self.quantity_column_index) - 1

        created = 0
        errors = []

        for i, row in enumerate(rows, start_row + 1):
            try:
                if product_col >= len(row) or quantity_col >= len(row):
                    continue

                product_code = str(row[product_col]).strip()
                quantity_str = str(row[quantity_col]).strip()

                if not product_code:
                    continue

                quantity = float(quantity_str.replace(',', '.')) if quantity_str else 0.0

                # Find product
                product = self.env['product.product'].search([
                    '|', '|', '|',
                    ('default_code', '=', product_code),
                    ('barcode', '=', product_code),
                    ('name', '=', product_code),
                    ('name', 'ilike', product_code)
                ], limit=1)

                if not product:
                    errors.append(f"Row {i}: Product '{product_code}' not found")
                    continue

                # Create line
                if self.order_type == 'sale':
                    vals = {
                        'order_id': order.id,
                        'product_id': product.id,
                        'product_uom_qty': quantity,
                        'product_uom': product.uom_id.id,
                    }
                elif self.order_type == 'purchase':
                    # Create line and let onchange calculate price
                    line = self.env['purchase.order.line'].new({
                        'order_id': order.id,
                        'product_id': product.id,
                        'product_qty': quantity,
                        'product_uom': product.uom_id.id,
                    })
                    # Trigger onchange to calculate price, taxes, etc.
                    line._compute_price_unit_and_date_planned_and_name()

                    vals = {
                        'order_id': order.id,
                        'product_id': product.id,
                        'product_qty': quantity,
                        'product_uom': line.product_uom.id,
                        'price_unit': line.price_unit,
                        'date_planned': line.date_planned,
                        'taxes_id': [(6, 0, line.taxes_id.ids)],
                    }
                elif self.order_type == 'stock':
                    vals = {
                        'picking_id': picking.id,
                        'product_id': product.id,
                        'product_uom_qty': quantity,
                        'product_uom': product.uom_id.id,
                        'location_id': picking.location_id.id,
                        'location_dest_id': picking.location_dest_id.id,
                        'name': product.display_name,
                        'state': 'draft',
                    }

                self.env[line_model].create(vals)
                created += 1

            except Exception as e:
                errors.append(f"Row {i}: {str(e)}")

        # Prepare notification message
        message = f"{created} lines imported successfully"
        if errors:
            message += f"\n\nErrors:\n" + "\n".join(errors[:5])
            if len(errors) > 5:
                message += f"\n... and {len(errors) - 5} more errors"

        # Show notification and close wizard
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Complete',
                'message': message,
                'type': 'success' if created > 0 else 'warning',
                'sticky': False,
            }
        }

        # Return action to close wizard and refresh parent view
        return {
            'type': 'ir.actions.act_window_close',
            'infos': {
                'notification': notification
            }
        }
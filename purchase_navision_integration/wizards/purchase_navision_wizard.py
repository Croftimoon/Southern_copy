import base64
import io
from odoo import models, fields, api
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class PurchaseNavisionWizard(models.TransientModel):
    _name = 'purchase.navision.wizard'
    _description = 'Send Purchase Order to SI'

    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order', required=True)
    contact_ids = fields.Many2many(
        'res.partner',
        string='Recipients',
        domain=[('is_company', '=', False)],
        required=True
    )
    subject = fields.Char(string='Subject', required=True)
    body = fields.Html(string='Message Body')
    attachment_name = fields.Char(string='Attachment Name', default='purchase_order_lines.xlsx')

    @api.onchange('purchase_order_id')
    def _onchange_purchase_order_id(self):
        """Set default values when purchase order changes"""
        if self.purchase_order_id:
            self.subject = f'Purchase Order {self.purchase_order_id.name}'
            self.body = f'''
                <p>Dear Team,</p>
                <p>Please find attached the purchase order lines for {self.purchase_order_id.name} in for importing into Navision.</p>
                <p>Purchase Order Details:</p>
                <ul>
                    <li>Order Reference: {self.purchase_order_id.name}</li>
                    <li>Order Date: {self.purchase_order_id.date_order.strftime('%Y-%m-%d') if self.purchase_order_id.date_order else ''}</li>
                    <li>Total Lines: {len(self.purchase_order_id.order_line)}</li>
                </ul>
                <p>Best regards</p>
            '''

    def _generate_excel_file(self):
        """Generate Excel file with purchase order lines"""
        if not xlsxwriter:
            raise UserError('xlsxwriter library is not installed. Please install it using: pip install xlsxwriter')

        # Create Excel file in memory
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Purchase Order Lines')

        # Write data rows
        row = 0
        for line in self.purchase_order_id.order_line:
            if line.product_id.default_code == '':
                continue

            worksheet.write(row, 0, 'item')  # Type column always "item"
            worksheet.write(row, 1, line.product_id.default_code)  # Product code
            worksheet.write(row, 2, line.product_qty)  # Quantity
            row += 1

        # Auto-adjust column widths
        worksheet.set_column('A:A', 8)  # Type column
        worksheet.set_column('B:B', 20)  # Code column
        worksheet.set_column('C:C', 12)  # Quantity column

        workbook.close()
        output.seek(0)

        return output.getvalue()

    def action_send_email(self):
        """Send email with Excel attachment to selected contacts"""
        if not self.contact_ids:
            raise UserError('Please select at least one recipient.')

        # Generate Excel file
        excel_data = self._generate_excel_file()

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': self.attachment_name,
            'type': 'binary',
            'datas': base64.b64encode(excel_data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': 'purchase.order',
            'res_id': self.purchase_order_id.id,
        })

        # Prepare email values
        recipient_emails = self.contact_ids.mapped('email')
        recipient_names = ', '.join(self.contact_ids.mapped('name'))

        # Create mail message in chatter
        mail_values = {
            'subject': self.subject,
            'body': self.body,
            'message_type': 'email',
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'model': 'purchase.order',
            'res_id': self.purchase_order_id.id,
            'partner_ids': [(6, 0, self.contact_ids.ids)],
            'attachment_ids': [(6, 0, [attachment.id])],
            'email_from': self.env.user.email or self.env.company.email,
        }

        # Create message in chatter
        message = self.env['mail.message'].create(mail_values)

        # Also send actual email
        mail_values_send = {
            'subject': self.subject,
            'body_html': self.body,
            'email_to': ','.join(filter(None, recipient_emails)),
            'email_from': self.env.user.email or self.env.company.email,
            'attachment_ids': [(6, 0, [attachment.id])],
            'auto_delete': True,
        }

        # Create and send email
        mail = self.env['mail.mail'].create(mail_values_send)
        mail.send()

        # Return action to close wizard and show success message
        return {
            'type': 'ir.actions.act_window_close',
            'infos': {
                'title': 'Success!',
                'message': f'Email sent successfully to {len(self.contact_ids)} recipient(s) and logged in purchase order chatter.',
            }
        }
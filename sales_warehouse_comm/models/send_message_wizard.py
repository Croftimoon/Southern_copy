import logging
from datetime import timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SendMessageWizard(models.TransientModel):
    _name = 'send.message.wizard'
    _description = 'Send Message Between Sales and Warehouse'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True
    )

    picking_id = fields.Many2one(
        'stock.picking',
        string='Picking Order'
    )

    message_type = fields.Selection([
        ('sale_to_warehouse', 'Sales to Warehouse'),
        ('warehouse_to_sale', 'Warehouse to Sales')
    ], string='Message Type', required=True)

    subject = fields.Char(
        string='Subject',
        compute='_compute_subject',
        readonly=True
    )

    message = fields.Html(
        string='Message',
        required=True
    )

    recipient_ids = fields.Many2many(
        'res.users',
        string='Additional Recipients',
        help='Additional users to notify (relevant users will be notified automatically)'
    )

    @api.depends('message_type', 'sale_order_id', 'picking_id')
    def _compute_subject(self):
        for record in self:
            if record.message_type == 'sale_to_warehouse':
                record.subject = f'Sales message regarding {record.sale_order_id.name}'
            else:
                if record.picking_id:
                    record.subject = f'Warehouse message regarding {record.picking_id.name}'
                else:
                    record.subject = f'Warehouse message regarding {record.sale_order_id.name}'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Remove auto-generation since we use computed field now
        return res

    def send_message(self):
        """Send the message to both records and notify recipients"""
        self.ensure_one()

        # Get recipients based on message type
        recipients = self._get_recipients()

        # Post message on Sale Order
        self.sale_order_id.message_post(
            body=self.message,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            partner_ids=recipients.partner_id.ids,
            author_id=self.env.user.partner_id.id,
        )

        # Post message on Picking Order if exists
        if self.picking_id:
            self.picking_id.message_post(
                body=self.message,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                partner_ids=recipients.partner_id.ids,
                author_id=self.env.user.partner_id.id,
            )

        # If message is from warehouse to sales, also post on all related pickings
        elif self.message_type == 'warehouse_to_sale':
            related_pickings = self.env['stock.picking'].search([
                ('sale_id', '=', self.sale_order_id.id),
                ('state', 'not in', ['done', 'cancel'])
            ])

            for picking in related_pickings:
                picking.message_post(
                    body=self.message,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                    partner_ids=recipients.partner_id.ids,
                    author_id=self.env.user.partner_id.id,
                )

        return {'type': 'ir.actions.act_window_close'}

    def _get_recipients(self):
        """Get recipients based on message type"""
        recipients = self.env['res.users']

        if self.message_type == 'sale_to_warehouse':
            # Find users who have sent messages from picking orders related to this sale order
            related_pickings = self.env['stock.picking'].search([
                ('sale_id', '=', self.sale_order_id.id)
            ])

            if related_pickings:
                # Find messages sent on these picking orders
                recent_messages = self.env['mail.message'].search([
                    ('res_id', 'in', related_pickings.ids),
                    ('model', '=', 'stock.picking'),
                    ('message_type', '=', 'comment'),
                    ('create_date', '>=', fields.Datetime.now() - timedelta(days=30))  # Within last 30 days
                ])

                if recent_messages:
                    # Get users who authored these messages (actual warehouse staff who messaged)
                    message_authors = recent_messages.mapped('author_id')
                    # Convert partners to users
                    warehouse_users = self.env['res.users'].search([
                        ('partner_id', 'in', message_authors.ids)
                    ])
                    recipients = warehouse_users

            # If no warehouse users have messaged, don't notify anyone automatically
            # They can use additional recipients field if needed

        elif self.message_type == 'warehouse_to_sale':
            # Only notify the original sales order creator
            if self.sale_order_id.user_id:
                recipients |= self.sale_order_id.user_id

        # Add additional recipients
        recipients |= self.recipient_ids

        # Remove current user to avoid self-notification
        recipients = recipients.filtered(lambda u: u.id != self.env.user.id)

        return recipients
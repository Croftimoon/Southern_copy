from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
from datetime import datetime, timedelta, date


class SaleOrder(models.Model):
    _inherit = "sale.order"

    hospital_state = fields.Selection([
        ('new', 'New'),
        ('awaiting_return', 'Awaiting Return'),
        ('waiting_po', 'Waiting PO'),
        ('invoiced', 'Invoiced'),
    ], string='Hospital Status', default='new', tracking=True,
        help='Hospital consignment workflow status')

    partner_id = fields.Many2one(
        check_company=True,
        domain=[('is_company', '=', True)],
    )
    client_id = fields.Many2one(
        comodel_name='res.partner',
        string="Contact",
        change_default=True,
        index=True,
        tracking=1,
        domain=[('is_company', '=', False)],
    )
    patient_name = fields.Char(string='Patient Name')
    surgery_date = fields.Date(string='Surgery Date')
    sales_team_member = fields.Char(string='Sales Team Member', compute='_compute_sales_team_member', store=True, precompute=True)

    is_delivered = fields.Boolean(compute='_compute_is_delivered')

    # Tracking fields
    proforma_sent_date = fields.Datetime('Pro-forma Sent Date', tracking=True)
    po_requested_date = fields.Datetime('PO Requested Date', tracking=True)
    expected_stock_return_date = fields.Date('Expected Stock Return Date', tracking=True,
                                           help='Expected date when unused stock will be returned by hospital')

    hospital_order = fields.Boolean('Hospital Order',
                                   default=False,
                                   help='Check this for hospital orders requiring consignment workflow')

    pricelist_readonly = fields.Boolean(
        compute='_compute_pricelist_readonly',
        store=False,
        default=lambda self: not self.env.user.has_group('southern_sale_extend.group_sale_pricelist_edit')
    )

    @api.depends('order_line')
    def action_set_delivered(self):
        for order in self:
            for picking in order.picking_ids:
                picking.action_cancel()

            for line in order.order_line:
                line.qty_delivered = line.product_uom_qty

    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        if self.client_id:
            values['client_id'] = self.client_id.id
        if self.patient_name:
            values['patient_name'] = self.patient_name
        if self.surgery_date:
            values['surgery_date'] = self.surgery_date

        return values

    @api.depends('partner_id', 'partner_invoice_id', 'company_id')
    def _compute_pricelist_id(self):
        for order in self:
            if order.state != 'draft':
                continue
            if not order.partner_id:
                order.pricelist_id = False
                continue

            order = order.with_company(order.company_id)

            # Check invoice address contact first, then fall back to main partner
            if order.partner_invoice_id and order.partner_invoice_id.property_product_pricelist:
                order.pricelist_id = order.partner_invoice_id.property_product_pricelist
            else:
                order.pricelist_id = order.partner_id.property_product_pricelist

    @api.onchange('partner_invoice_id', 'partner_id', 'company_id')
    def _onchange_partner_invoice_id_payment_term(self):
        for order in self:
            if order.state != 'draft':
                continue

            if not order.partner_id:
                order.payment_term_id = False
                continue

            order = order.with_company(order.company_id)
            if order.partner_invoice_id and order.partner_invoice_id.property_payment_term_id:
                order.payment_term_id = order.partner_invoice_id.property_payment_term_id
            else:
                order.payment_term_id = order.partner_id.property_payment_term_id

    @api.depends('order_line')
    def _compute_is_delivered(self):
        for order in self:
            order.is_delivered = True
            for line in order.order_line:
                if line.product_uom_qty != line.qty_delivered:
                    order.is_delivered = False

    @api.depends('team_id.member_ids.name')
    def _compute_sales_team_member(self):
        for order in self:
            order.sales_team_member = ''
            if order.team_id:
                names = order.team_id.member_ids.mapped('name')
                order.sales_team_member = names[0] if names else ''

    @api.depends('surgery_date')
    def _compute_expected_date(self):
        for order in self:
            super(SaleOrder, order)._compute_expected_date()
            if order.surgery_date and order.expected_date and order.expected_date.date() > order.surgery_date:
                order.expected_date = order.surgery_date

    def action_print_proforma_confirm(self):
        """Print pro-forma and confirm order"""
        for order in self:
            if order.state in ['draft', 'sent']:
                # Confirm the order first
                super(SaleOrder, order).action_confirm()

            # Update hospital state and date
            if order.hospital_order:
                values = {'hospital_state': 'awaiting_return'}
                if not order.proforma_sent_date:
                    values['proforma_sent_date'] = fields.Datetime.now()
                order.write(values)

            # Return print action for pro-forma with correct context
            action = order.with_context(proforma=True, validate_analytic=True, hospital_call=True).action_quotation_send()
            return action

    def action_send_final_proforma_wait_po(self):
        """Send final pro-forma and wait for PO"""
        for order in self:
            if order.hospital_state == 'awaiting_return':
                values = {'hospital_state': 'waiting_po'}
                # Only set date if not already set
                if not order.po_requested_date:
                    values['po_requested_date'] = fields.Datetime.now()
                order.write(values)
                # Return send action for final pro-forma with correct context
                action = order.with_context(proforma=True, validate_analytic=True, hospital_call=True).action_quotation_send()
                return action
            else:
                raise ValidationError(_('Can only request PO from Awaiting Return state.'))

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Override to validate hospital orders before invoicing"""
        for order in self:
            if order.hospital_order:
                # For hospital orders, check if we're in waiting_po state without PO
                if order.hospital_state == 'waiting_po' and not order.client_order_ref:
                    raise ValidationError(
                        _('Customer PO number is required before invoicing hospital orders. Please enter it in the Customer Reference field.'))

        # Create invoices normally
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)

        # Update hospital state after successful invoice creation
        for order in self:
            if order.hospital_order and moves and order.hospital_state in ['waiting_po', 'awaiting_return']:
                order.hospital_state = 'invoiced'

        return moves

    def action_confirm(self):
        if self.hospital_order and self.hospital_state == 'new':
            return self.action_print_proforma_confirm()

        return super().action_confirm()

    def action_draft(self):
        if self.hospital_order:
            self.hospital_state = 'new'

        return super().action_draft()

    @api.depends('surgery_date', 'partner_shipping_id', 'partner_id')
    def _compute_commitment_date(self):
        """Override or extend commitment_date computation to include lead time calculation"""
        if hasattr(super(), '_compute_commitment_date'):
            super()._compute_commitment_date()

        for order in self:
            if not order.surgery_date:
                continue

            delivery_partner = order.partner_shipping_id or order.partner_id
            if not delivery_partner:
                continue

            lead_time_model = self.env['delivery.lead.time']
            lead_days = lead_time_model.get_lead_days(
                partner_id=delivery_partner.id,
                country_id=delivery_partner.country_id.id if delivery_partner.country_id else None,
                state_id=delivery_partner.state_id.id if delivery_partner.state_id else None,
                zip_code=delivery_partner.zip
            )

            calculated_delivery_date = order.surgery_date - timedelta(days=lead_days)

            today = fields.Date.today()
            if calculated_delivery_date < today:
                calculated_delivery_date = today

            order.commitment_date = datetime.combine(calculated_delivery_date, datetime.min.time())

    @api.onchange('surgery_date', 'partner_shipping_id', 'partner_id')
    def _onchange_delivery_calculation(self):
        """Trigger delivery date recalculation on relevant field changes"""
        self._compute_commitment_date()

    @api.depends_context('uid')
    def _compute_pricelist_readonly(self):
        """Compute if pricelist should be readonly"""
        has_permission = self.env.user.has_group('southern_sale_extend.group_sale_pricelist_edit')
        for record in self:
            record.pricelist_readonly = not has_permission

    @api.onchange('partner_shipping_id')
    def _onchange_partner_shipping_id(self):
        """Update sales team based on shipping address"""
        super()._onchange_partner_shipping_id()
        if self.partner_shipping_id and self.partner_shipping_id.team_id:
            self.team_id = self.partner_shipping_id.team_id

    @api.model_create_multi
    def create(self, vals_list):
        """Set sales team based on shipping address"""
        orders = super().create(vals_list)
        for order in orders:
            if order.partner_shipping_id and order.partner_shipping_id.team_id:
                order.team_id = order.partner_shipping_id.team_id
            elif not order.team_id and order.partner_id and order.partner_id.team_id:
                order.team_id = order.partner_id.team_id
        return orders

    def _get_report_filename(self):
        """Custom method to determine report filename"""
        if self.env.context.get('proforma'):
            return f'Pro-forma - {self.name}'
        elif self.state in ('draft', 'sent'):
            return f'Quotation - {self.name}'
        else:
            return f'Order - {self.name}'

    def action_open_discount_wizard(self):
        """Restrict access to the Discount wizard by custom group.

        Even if a conflicting view exposes the button, enforce permission here.
        """
        self.ensure_one()
        if not self.env.user.has_group('southern_sale_extend.group_sale_discount_edit'):
            raise AccessError(_("You are not allowed to apply discounts."))
        return super().action_open_discount_wizard()
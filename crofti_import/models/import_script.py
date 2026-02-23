import io
import logging
import time
import traceback
from datetime import datetime, timedelta

import base64
from odoo import models, fields, api, _

class ImportScript(models.Model):
    _name = 'import.script'
    _order = 'name'
    _description = 'Import Script'

    name = fields.Char(required=True)
    file = fields.Binary(required=True)
    state = fields.Selection([('new', 'New'), ('executed', 'Executed'), ('failed', 'Failed')], default='new', readonly=True)
    result_log = fields.Text(readonly=True)
    executed_at = fields.Datetime(readonly=True)
    duration = fields.Char(readonly=True)
    size = fields.Char(readonly=True)

    file_type = fields.Selection([
        ('sql', 'SQL'),
        ('python', 'Python'),
    ], compute="_compute_file_type", store=True, string="Type", readonly=True)

    @api.depends('name')
    def _compute_file_type(self):
        for rec in self:
            if rec.name and rec.name.lower().endswith('.py'):
                rec.file_type = 'python'
            elif rec.name and rec.name.lower().endswith('.sql'):
                rec.file_type = 'sql'
            else:
                rec.file_type = False

    def action_bulk_import(self):
        return {
            "name": _("Turns out you can't just drag a bunch of scripts onto here and have it work logically, isn't that neat?"),
            "type": "ir.actions.act_window",
            "res_model": "import.script.wizard",
            "target": "new",
            "views": [[False, "form"]],
            "context": {"is_modal": True},
        }

    def action_csv_export(self):
        return {
            "name": _("Ever wanted some bespoke CSV out of your Odoo models? The future is now."),
            "type": "ir.actions.act_window",
            "res_model": "query.csv.wizard",
            "target": "new",
            "views": [[False, "form"]],
            "context": {"is_modal": True},
        }

    @staticmethod
    def chunk_list(lst, chunk_size=1000):
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]

    def action_stupid(self):
        env = self.env
        log = logging.getLogger(f'dumb.stuff')

        env.cr.execute("""
                       SELECT coalesce(doco.id, open.partner_id) AS id,
                              refs.ref,
                              refs.alt_codes,
                              doco.move_type,
                              doco.total,
                              doco.docos,
                              doco.doco_ids,
                              coalesce(open.open_balance, 0)     AS open_balance,
                              array_length(doco.docos, 1)
                       FROM (SELECT rp.id,
                                    rp.ref,
                                    am.move_type,
                                    sum(am.amount_total_signed) AS total,
                                    array_agg(am.name)          AS docos,
                                    array_agg(am.id)            AS doco_ids
                             FROM account_move am
                                      INNER JOIN res_partner rp ON rp.id = am.partner_id
                             WHERE am.move_type IN ('out_invoice', 'out_refund')
                               AND am.date < '2025-07-01'
                               AND am.payment_state NOT IN ('paid', 'in_payment', 'reversed')
                             GROUP BY rp.id, rp.ref, am.move_type) AS doco
                                FULL OUTER JOIN (SELECT ap.partner_id,
                                                        rp.ref,
                                                        sum(ap.amount_company_currency_signed) AS open_balance
                                                 FROM account_payment ap
                                                          INNER JOIN account_move am ON am.id = ap.move_id
                                                          INNER JOIN res_partner rp ON rp.id = ap.partner_id
                                                 WHERE ap.partner_type = 'customer'
                                                   AND am.ref = 'Migration Balancing'
                                                   AND am.state = 'posted'
                                                   AND am.date < '2025-07-01'
                                                   AND NOT ap.is_reconciled
                                                 GROUP BY ap.partner_id, rp.ref) AS open ON (open.partner_id = doco.id)
                                INNER JOIN (SELECT rp.ref,
                                                   coalesce(array_agg(rpc.name) FILTER (WHERE rpc.name IS NOT NULL),
                                                            ARRAY []::TEXT[]) || rp.ref AS alt_codes
                                            FROM res_partner rp
                                                     LEFT JOIN res_partner_res_partner_code_rel rprpcr ON rp.id = rprpcr.res_partner_id
                                                     LEFT JOIN res_partner_code rpc ON rprpcr.res_partner_code_id = rpc.id
                                            GROUP BY rp.ref) AS refs ON (refs.ref IN (doco.ref, open.ref))
                       WHERE refs.ref = 'SIA2381'
                       ORDER BY doco.ref, doco, move_type;
                       """)

        rows = env.cr.fetchall()

        customers = {}

        for row in rows:
            id = row[0]
            ref = row[1]
            alt_codes = row[2]
            move_type = row[3]
            total = row[4]
            docos = row[5]
            doco_ids = row[6]
            open_balance = row[7]

            if id not in customers:
                customers[id] = {
                    'id': id,
                    'ref': ref,
                    'alt_codes': alt_codes,
                    'invoices': [],
                    'invoice_ids': [],
                    'invoice_total': 0,
                    'credits': [],
                    'credit_ids': [],
                    'credit_total': 0,
                    'open_balance': open_balance,
                    'open_moves': []
                }

            customer = customers[id]
            if move_type == 'out_invoice':
                customer['invoices'] = docos
                customer['invoice_ids'] = doco_ids
                customer['invoice_total'] = total
            elif move_type == 'out_refund':
                customer['credits'] = docos
                customer['credit_ids'] = doco_ids
                customer['credit_total'] = total

        env.cr.execute("""
                       SELECT rp.id,
                              refs.ref,
                              nb.entry_type,
                              nb.move_name,
                              am.id AS move_id,
                              nb.date,
                              nb.currency_code,
                              nb.amount,
                              nb.residual,
                              nb.amount_currency,
                              nb.residual_currency
                       FROM navision_balance nb
                                INNER JOIN (SELECT rp.ref,
                                                   coalesce(array_agg(rpc.name) FILTER (WHERE rpc.name IS NOT NULL),
                                                            ARRAY []::TEXT[]) || rp.ref AS alt_codes
                                            FROM res_partner rp
                                                     LEFT JOIN res_partner_res_partner_code_rel rprpcr ON rp.id = rprpcr.res_partner_id
                                                     LEFT JOIN res_partner_code rpc ON rprpcr.res_partner_code_id = rpc.id
                                            GROUP BY rp.ref) AS refs ON (nb.ref = ANY (refs.alt_codes))
                                INNER JOIN res_partner rp ON (rp.ref = refs.ref)
                                LEFT JOIN account_move am ON am.name = nb.move_name
                       WHERE refs.ref = 'SIA2381'
                       """)

        rows = env.cr.fetchall()

        bad_bois = {}
        chunk_size = 1000

        for row in rows:
            id = row[0]
            ref = row[1]
            entry_type = row[2]
            move_name = row[3]
            move_id = row[4]
            date = row[5]
            currency_code = row[6]
            amount = row[7]
            residual = row[8]
            amount_currency = row[9]
            residual_currency = row[10]

            customer = customers.get(id)
            if not customer:
                if ref in bad_bois:
                    bad_bois[ref]['amounts'].append(residual)
                else:
                    bad_bois[ref] = {
                        'id': id,
                        'amounts': [residual]
                    }
                continue

            is_real_document = entry_type == 'Invoice' or entry_type == 'Credit Memo'

            if is_real_document:
                customer['open_moves'].append({
                    'move_name': move_name,
                    'move_id': move_id,
                    'date': date,
                    'currency_code': currency_code,
                    'amount': amount,
                    'residual': residual,
                    'amount_currency': amount_currency,
                    'residual_currency': residual_currency,
                    'is_partial_apply': amount != residual,
                })
            else:
                customer['open_balance'] += residual

        for ref, record in bad_bois.items():
            balance = round(sum(record['amounts']), 2)
            if balance >= 0:
                continue  # already paid

            id = record['id']
            customers[id] = {
                'id': id,
                'ref': ref,
                'alt_codes': [],
                'invoices': [],
                'invoice_ids': [],
                'invoice_total': 0,
                'credits': [],
                'credit_ids': [],
                'credit_total': 0,
                'open_balance': balance,
                'open_moves': []
            }

        customer_count = len(customers)
        customer_index = 0
        for customer in customers.values():
            customer_index += 1

            open_move_ids = [x['move_id'] for x in customer['open_moves']]
            invoice_ids = [x for x in customer['invoice_ids']]
            credit_ids = [x for x in customer['credit_ids']]
            log.info(f'Processing {customer["ref"]} ({customer_index}/{customer_count}), {len(open_move_ids)} moves')

            closed_invoice_ids = [x for x in invoice_ids if x not in open_move_ids]
            if closed_invoice_ids:
                for chunk in self.chunk_list(closed_invoice_ids, chunk_size):
                    with env.registry.cursor() as new_cr:
                        customer_env = api.Environment(new_cr, env.uid, env.context)
                        AccountMove = customer_env['account.move']
                        AccountPaymentRegister = customer_env['account.payment.register']
                        AccountPayment = customer_env['account.payment']
                        closed_invoices = AccountMove.browse(chunk)
                        if customer['ref'] == 'SIA2381':
                            log.info(
                                f"thinking real hard about {len(closed_invoices)} invoices ({len(closed_invoices.line_ids)} lines) [{str(closed_invoices.mapped('name'))}]")

                        ctx = {
                            'active_model': 'account.move.line',
                            'active_ids': closed_invoices.line_ids.ids,  # list of line IDs
                        }

                        # Create the wizard record
                        wizard = AccountPaymentRegister.with_context(ctx).create({})

                        # Optionally set fields on the wizard (e.g., journal_id, amount)
                        wizard.group_payment = True
                        wizard.communication = 'Migration Balancing'
                        wizard.payment_date = datetime(2025, 6, 30)
                        wizard.journal_id = 17

                        # Execute the wizard action method
                        result = wizard.action_create_payments()
                        new_cr.commit()

                        log.info(f'Created payment for {len(closed_invoices)} invoices')

            closed_credit_ids = [x for x in credit_ids if x not in open_move_ids]
            if closed_credit_ids:
                for chunk in self.chunk_list(closed_credit_ids, chunk_size):
                    with env.registry.cursor() as new_cr:
                        customer_env = api.Environment(new_cr, env.uid, env.context)
                        AccountMove = customer_env['account.move']
                        AccountPaymentRegister = customer_env['account.payment.register']
                        closed_credits = AccountMove.browse(chunk)
                        if customer['ref'] == 'SIA2381':
                            log.info(
                                f"thinking real hard about {len(closed_credits)} credits ({len(closed_credits.line_ids)} lines) [{str(closed_credits.mapped('name'))}]")

                        ctx = {
                            'active_model': 'account.move.line',
                            'active_ids': closed_credits.line_ids.ids,  # list of line IDs
                        }

                        # Create the wizard record
                        wizard = AccountPaymentRegister.with_context(ctx).create({})

                        # Optionally set fields on the wizard (e.g., journal_id, amount)
                        wizard.group_payment = True
                        wizard.communication = 'Migration Balancing'
                        wizard.payment_date = datetime(2025, 6, 30)
                        wizard.journal_id = 17

                        # Execute the wizard action method
                        result = wizard.action_create_payments()
                        new_cr.commit()

                        log.info(f'Created "payment" for {len(closed_credits)} credits')

            partial_applies = [x for x in customer['open_moves'] if x['is_partial_apply']]
            if partial_applies:
                with env.registry.cursor() as new_cr:
                    customer_env = api.Environment(new_cr, env.uid, env.context)
                    AccountMove = customer_env['account.move']
                    AccountPaymentRegister = customer_env['account.payment.register']
                    for apply in partial_applies:
                        payment_amount = abs(apply['amount'] - apply['residual'])
                        move = AccountMove.browse(apply['move_id'])
                        if move.payment_state != 'not_paid':
                            log.info(f'Skipping payment for {move.name} ({move.payment_state})')
                            continue

                        ctx = {
                            'active_model': 'account.move.line',
                            'active_ids': move.line_ids.ids,  # list of line IDs
                        }

                        # Create the wizard record
                        wizard = AccountPaymentRegister.with_context(ctx).create({})

                        # Optionally set fields on the wizard (e.g., journal_id, amount)
                        wizard.group_payment = True
                        wizard.communication = 'Migration Balancing'
                        wizard.payment_date = datetime(2025, 6, 30)
                        wizard.amount = payment_amount
                        wizard.journal_id = 17

                        # Execute the wizard action method
                        result = wizard.action_create_payments()
                        new_cr.commit()

                        log.info(f'Created partial payment for ${payment_amount} on {move.name}')

                outstanding_balance = customer['open_balance']
                if abs(outstanding_balance) >= 0.01:
                    with env.registry.cursor() as new_cr:
                        customer_env = api.Environment(new_cr, env.uid, env.context)
                        AccountPayment = customer_env['account.payment']
                        log.info(f'Outstanding: {outstanding_balance}')
                        payment = AccountPayment.create({
                            'journal_id': 17,
                            'partner_id': customer['id'],
                            'date': datetime(2025, 6, 30),
                            'amount': abs(outstanding_balance),
                            'ref': 'Migration Balancing',
                            'payment_type': 'outbound' if outstanding_balance > 0 else 'inbound',
                        })
                        payment.action_post()
                        new_cr.commit()


    def action_execute(self):
        for record in self:
            if record.file_type == 'python':
                self._action_execute_python(record)
            elif record.file_type == 'sql':
                self._action_execute_sql(record)

    def _action_execute_sql(self, record):
        query = base64.b64decode(record.file).decode('utf-8')
        start = time.time()
        with self.env.registry.cursor() as new_cr:
            try:
                new_cr.execute(query)
                affected = new_cr.rowcount
                new_cr.commit()
                end = time.time()
                record.write({
                    'state': 'executed',
                    'result_log': f'Executed successfully. Rows affected: {affected}',
                    'executed_at': datetime.utcnow(),
                    'duration': str(timedelta(seconds=round(end - start, 3))),
                })
            except Exception as e:
                new_cr.rollback()
                record.write({
                    'state': 'failed',
                    'result_log': f'Error: {str(e)}',
                    'executed_at': datetime.utcnow(),
                })

    def _action_execute_python(self, record):
        code = base64.b64decode(record.file).decode('utf-8')
        start = time.time()
        with self.env.registry.cursor() as new_cr:
            isolated_env = api.Environment(new_cr, self.env.uid, self.env.context)

            log_buffer = io.StringIO()
            log_handler = logging.StreamHandler(log_buffer)
            log_handler.setLevel(logging.INFO)
            logger = logging.getLogger(f'import.script.{record.id}')
            logger.addHandler(log_handler)
            logger.setLevel(logging.INFO)

            local_env = {'env': isolated_env, 'self': self.with_env(isolated_env), 'log': logger}
            try:
                exec(code, {}, local_env)
                new_cr.commit()
                end = time.time()
                record.write({
                    'state': 'executed',
                    'result_log': log_buffer.getvalue().strip() or 'Python executed successfully',
                    'executed_at': datetime.utcnow(),
                    'duration': str(timedelta(seconds=round(end - start, 3))),
                })
            except Exception as e:
                new_cr.rollback()
                record.write({
                    'result_log': f"Python error: {''.join(traceback.format_exception(e))}\n\n{log_buffer.getvalue().strip()}",
                    'executed_at': datetime.utcnow()
                })

    @staticmethod
    def _format_file_size(bytes_val):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.2f} PB"

    def write(self, values):
        if 'file' in values:
            values['state'] = 'new'
            values['result_log'] = None
            values['executed_at'] = None
            values['duration'] = None
            values['size'] = self._format_file_size(len(values['file']) * 3 / 4)

        return super().write(values)
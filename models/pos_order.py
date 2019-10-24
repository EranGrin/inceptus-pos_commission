# -*- coding: utf-8 -*-
# Part of Inceptus ERP Solutions Pvt.ltd.
# See LICENSE file for copyright and licensing details.

import time
from datetime import datetime
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from operator import itemgetter
from itertools import groupby


class POSCommission(models.Model):
    _name = 'pos.commission'

    _description = 'Request for Commission Invoice'

    _inherit = ['mail.thread', 'ir.needaction_mixin', 'ies.base']

    _order = 'write_date desc'

    READONLY_STATES = {
        'draft': [('readonly', True)],
        'open': [('readonly', True)],
        'paid': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    READONLY_STATES_DUE = {
        'open': [('readonly', True)],
        'paid': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.multi
    @api.depends('line_ids', 'return_line_ids')
    def _amount_total(self):
        total = 0.0
        for line in self.line_ids:
            total += line.commission
        for line in self.return_line_ids:
            total += line.commission
        self.amount_total = total

    @api.depends('line_ids.commission_total', 'return_line_ids.commission_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.line_ids:
                unit_commission = line.commission / line.product_qty
                amount_untaxed += line.commission_subtotal
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    taxes = line.tax_ids.compute_all(unit_commission, line.currency_id, line.product_qty,
                                                     product=line.product_id, partner=order.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.commission_tax
            for line in order.return_line_ids:
                unit_commission = line.commission / line.product_qty
                amount_untaxed += line.commission_subtotal
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    taxes = line.tax_ids.compute_all(unit_commission, line.currency_id, line.product_qty,
                                                     product=line.product_id, partner=order.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.commission_tax

            order.update({
                'c_amount_untaxed': order.currency_id.round(amount_untaxed),
                'c_amount_tax': order.currency_id.round(amount_tax),
                'c_amount_total': amount_untaxed + amount_tax,
            })

    name = fields.Char('Name', default='New')
    partner_id = fields.Many2one('res.partner', "Vendor", required=1, states=READONLY_STATES, track_visibility="always")
    date_rfci = fields.Date("Create Date", default=fields.Date.context_today, states=READONLY_STATES_DUE)
    paid_date = fields.Date("Paid Date")
    line_ids = fields.One2many('pos.commission.line', 'commission_id',
                               "Commission Lines", copy=True, states=READONLY_STATES)
    return_line_ids = fields.One2many('pos.commission.line', 'ret_commission_id',
                                      "Return Commission Lines", copy=True, states=READONLY_STATES)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id,
                                  states=READONLY_STATES)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 index=True, default=lambda self: self.env.user.company_id.id,
                                 states=READONLY_STATES)
    state = fields.Selection([('rfi', 'RFCI'), ('rfis', "RFCI Sent"),
                              ('draft', 'Invoiced'), ('proforma', 'Pro-forma'),
                              ('proforma2', 'Pro-forma'), ('open', 'Open'),
                              ('paid', 'Paid'), ('cancel', 'Cancelled'),
                              ('refund', 'Refunded')
                              ], string="State", default='rfi', track_visibility='onchange', )
    amount_total = fields.Monetary(string='Commission Total', store=True,
                                   readonly=True, compute='_amount_total')

    c_amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                       track_visibility='always')
    c_amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    c_amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')

    refund_invoice = fields.Many2one('account.invoice', "Refund Invoice")
    refund_amount = fields.Monetary('Refund Amount')

    notes = fields.Text("Comments")
    invoice_id = fields.Many2one('account.invoice', 'Vendor Bill')

    # related fields of invoice
    invoice_line_ids = fields.One2many(related='invoice_id.invoice_line_ids', string="Invoice Lines")
    tax_line_ids = fields.One2many(related='invoice_id.tax_line_ids', string='Taxes')
    amount_untaxed = fields.Monetary(string='Untaxed Amount',
                                     related='invoice_id.amount_untaxed', track_visibility=False)
    amount_tax = fields.Monetary(string='Tax',
                                 related='invoice_id.amount_tax', )
    inv_amount_total = fields.Monetary(string='Total',
                                       related='invoice_id.amount_total', )
    payments_widget = fields.Text(related='invoice_id.payments_widget', )
    residual = fields.Monetary(string='Amount Due',
                               related='invoice_id.residual', )
    reconciled = fields.Boolean(string='Paid/Reconciled', related='invoice_id.reconciled', )
    outstanding_credits_debits_widget = fields.Text(related='invoice_id.outstanding_credits_debits_widget', )

    date_due = fields.Date(string='Due Date', states=READONLY_STATES_DUE, index=True, copy=False)

    journal_id = fields.Many2one(related='invoice_id.journal_id', string='Journal')
    user_id = fields.Many2one(related='invoice_id.user_id', string="Responsible")
    account_id = fields.Many2one(related='invoice_id.account_id', string="Account")
    payment_term_id = fields.Many2one(related='invoice_id.payment_term_id', string="Payment Term")
    move_id = fields.Many2one(related='invoice_id.move_id', string="Journal Entry")
    fiscal_position_id = fields.Many2one(related='invoice_id.fiscal_position_id', string="Fiscal Position")
    date = fields.Date(related='invoice_id.date', string="Accounting Date")

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('pos.commission.seq')
        res = super(POSCommission, self).create(vals)
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ['rfi', 'rfis', 'draft', 'cancel']:
                raise UserError(_('You cannot delete record which is not draft or cancelled!'))
            rec.copy(default={'invoice_id': False})
        return super(POSCommission, self).unlink()

    @api.onchange('date_due', 'date_rfci')
    def onchange_dates(self):
        if self.invoice_id:
            self.invoice_id.write({'date_due': self.date_due,
                                   'date_invoice': self.date_rfci})

    @api.multi
    def make_invoice(self):
        invoice_env = self.env['account.invoice']
        invoice_dict = {}
        line_list = []
        for rec in self:
            for line in rec.line_ids:
                account = self.env['account.invoice.line'].get_invoice_line_account('in_invoice', line.product_id,
                                                                                    False, self.company_id)
                line_list.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'quantity': line.product_qty,
                    'uom_id': line.product_uom.id,
                    'price_unit': line.commission / line.product_qty,
                    'account_id': account and account.id,
                    'invoice_line_tax_ids': [(4, x.id) for x in line.tax_ids]
                }))
            for line in rec.return_line_ids:
                account = self.env['account.invoice.line'].get_invoice_line_account('in_invoice', line.product_id,
                                                                                    False, self.company_id)
                line_list.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': "Return: %s" % (line.product_id.name),
                    'quantity': line.product_qty,
                    'uom_id': line.product_uom.id,
                    'price_unit': line.commission / line.product_qty,
                    'account_id': account and account.id,
                    'invoice_line_tax_ids': [(4, x.id) for x in line.tax_ids]
                }))

            invoice_dict.update({
                'partner_id': rec.partner_id.id,
                'journal_id': self.company_id.journal_id.id,
                'invoice_line_ids': line_list,
                'type': 'in_invoice',
                'commission_id': rec.id,
                'date_due': rec.date_due,
                'date_invoice': rec.date_rfci,
                'is_commission': True,
            })
            invoice = invoice_env.create(invoice_dict)
            rec.invoice_id = invoice.id
            rec.state = 'draft'
        return True

    @api.multi
    def validate_invoice(self):
        if self.invoice_id:
            self.invoice_id.action_invoice_open()
            self.state = 'open'
        return True

    @api.multi
    def validate_cancel(self):
        if self.invoice_id:
            self.invoice_id.action_invoice_cancel()
            self.invoice_id.unlink()
        self.state = 'cancel'
        return True

    @api.multi
    def validate_draft(self):
        self.state = 'rfis'
        return True

    @api.multi
    def unlink_invoice(self):
        if self.invoice_id:
            self.invoice_id.unlink()
        return True

    @api.multi
    def action_view_invoice(self):
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        result['domain'] = "[('id', '=', " + str(self.invoice_id.id) + ")]"
        return result

    @api.multi
    def action_rfi_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = self.env.ref('ies_pos_commission.email_template_edi_rfi').id
        except ValueError:
            template_id = False
        try:
            compose_form_id = self.env.ref('mail.email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'pos.commission',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def print_rfi(self):
        if self.state == 'rfi':
            self.write({'state': "rfis"})
        return self.env['report'].get_action(self, 'ies_pos_commission.report_vendor_commission')

    @api.multi
    def get_taxes_values(self):
        tax_val = {}
        tax_list = []
        for line in self.line_ids:
            unit_commission = line.commission / line.product_qty
            taxes = line.tax_ids.compute_all(unit_commission, self.currency_id, line.product_qty, line.product_id,
                                             self.partner_id)['taxes']
            for tax in taxes:
                tax_val = {
                    'base': tax['base'],
                    'amount': tax['amount'],
                    'id': tax['id'],
                    'name': tax['name']
                }
                tax_list.append(tax_val)
        for line in self.return_line_ids:
            unit_commission = line.commission / line.product_qty
            taxes = line.tax_ids.compute_all(unit_commission, self.currency_id, line.product_qty, line.product_id,
                                             self.partner_id)['taxes']
            for tax in taxes:
                tax_val = {
                    'base': tax['base'],
                    'amount': tax['amount'],
                    'id': tax['id'],
                    'name': tax['name']
                }
                tax_list.append(tax_val)
        tax_list.sort(key=itemgetter("id"))
        tax_res = []
        tax_dict = {}
        for tax in tax_list:
            if tax_dict.get('id') == tax['id']:
                tax_dict.update({
                    'amount': tax_dict['amount'] + tax['amount'],
                    'base': tax_dict['base'] + tax['base'],
                })
            else:
                tax_dict = {
                    'id': tax['id'],
                    'name': tax['name'],
                    'amount': tax['amount'],
                    'base': tax['base'],
                }
                tax_res.append(tax_dict)
        return tax_res


class POSCommissionLine(models.Model):
    _name = 'pos.commission.line'

    _inherit = ["ies.base"]

    _order = 'id desc'

    @api.depends('product_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.product_qty

    @api.depends('product_qty', 'commission', 'tax_ids')
    def _compute_commission(self):
        for line in self:
            unit_commission = line.commission / line.product_qty
            taxes = line.tax_ids.compute_all(unit_commission, line.currency_id, line.product_qty,
                                             product=line.product_id, partner=line.commission_id.partner_id)
            line.update({
                'commission_tax': taxes['total_included'] - taxes['total_excluded'],
                'commission_total': taxes['total_included'],
                'commission_subtotal': taxes['total_excluded'],
            })

    @api.multi
    @api.depends('product_id.standard_price')
    def _get_commission(self):
        for obj in self:
            if obj.product_id.standard_price:
                obj.commission_per = round(((obj.product_id.standard_price) / obj.price_unit) * 100, 2)
            obj.commission = obj.product_id.standard_price * obj.product_qty
            obj.unit_commission = obj.product_id.standard_price

    name = fields.Char('Ref', readonly=1)

    product_id = fields.Many2one('product.product', "Product", required=True)
    product_qty = fields.Float(string='Quantity',
                               digits=dp.get_precision('POS'), required=True)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure',
                                  required=True)
    price_unit = fields.Float(string='Unit Price', required=True,
                              digits=dp.get_precision('Product Price'))

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)

    commission_subtotal = fields.Monetary(compute='_compute_commission', string='Commission Subtotal', store=True)
    commission_total = fields.Monetary(compute='_compute_commission', string='Commission Total', store=True)
    commission_tax = fields.Monetary(compute='_compute_commission', string='Commission Tax', store=True)

    unit_commission = fields.Float(compute='_get_commission', string="Unit Commission",
                                   digits=dp.get_precision('Account'))

    commission = fields.Float(compute='_get_commission', string="Commission",
                              digits=dp.get_precision('Account'), store=True)

    commission_per = fields.Float(compute='_get_commission',
                                  string="Commission(%)", digits=dp.get_precision('Account'),
                                  store=True)
    is_return = fields.Boolean('Return', compute="_is_return", store=True)
    commission_id = fields.Many2one('pos.commission', 'Commission', ondelete='set null')
    ret_commission_id = fields.Many2one('pos.commission', 'Return Commission')
    currency_id = fields.Many2one(related='commission_id.currency_id',
                                  store=True, string='Currency', readonly=True)
    pos_line_id = fields.Many2one('pos.order.line', 'POS line Reference')
    so_line_id = fields.Many2one('sale.order.line', 'Sale line Reference')
    date = fields.Date('Date')
    tax_ids = fields.Many2many('account.tax', string='Taxes')

    @api.onchange('commission_per')
    def onchange_commission_per(self):
        if self.commission_per:
            self.commission = (self.price_subtotal * self.commission_per) / 100
            self.unit_commission = self.commission / self.product_qty

    @api.onchange('commission')
    def onchange_commission(self):
        if self.commission:
            self.commission_per = round((self.commission * 100) / self.price_subtotal, 2)
            self.unit_commission = self.commission / self.product_qty

    @api.multi
    def get_tax_names(self):
        tax_name = ""
        for rec in self:
            for tax in rec.tax_ids:
                tax_name += tax.description or tax.name + ", "
        return tax_name


class PosOrder(models.Model):
    _name = "pos.order"

    _inherit = ["pos.order", "ies.base"]

    def add_payment(self, data):
        res = super(PosOrder, self).add_payment(data)
        commission_env = self.env['pos.commission']
        commission_dict = {}
        for line in self.lines:
            if data.get('amount') < 0:
                continue
            commission_lines = []
            if line.supplier_id and line.product_id.commission_ok:
                ref_name = '%s-%s' % (self.session_id.name, self.name)
                commission_lines.append((0, 0, {
                    'name': ref_name,
                    'product_id': line.product_id.id,
                    'product_qty': line.qty or 0.0,
                    'product_uom': line.product_id.uom_po_id.id,
                    'price_unit': line.price_unit,
                    'pos_line_id': line.id,
                    'date': datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'tax_ids': [(4, x.id) for x in line.product_id.supplier_taxes_id]
                }))

                commission_rec = commission_env.search([('state', '=', 'rfi'),
                                                        ('partner_id', '=', line.supplier_id.id), ], limit=1)

                if line.qty > 0:
                    if len(commission_rec):
                        commission_rec.line_ids = commission_lines
                    else:
                        commission_dict.update({
                            'partner_id': line.supplier_id.id,
                            'line_ids': commission_lines,
                        })
                        commission_rec = commission_env.create(commission_dict)
                else:
                    if len(commission_rec):
                        commission_rec.return_line_ids = commission_lines
                    else:
                        commission_dict.update({
                            'partner_id': line.supplier_id.id,
                            'return_line_ids': commission_lines,
                        })
                        commission_rec = commission_env.create(commission_dict)
                line.commission_id = commission_rec.id
        return res


class pos_order_line(models.Model):
    _inherit = 'pos.order.line'

    @api.multi
    @api.depends('price_unit', 'qty')
    def _get_commission(self):
        comm_obj = self.env['product.supplierinfo']
        for obj in self:
            comm_id = comm_obj.search([('product_tmpl_id', '=', obj.product_id.product_tmpl_id.id), ], limit=1)
            if len(comm_id) and not obj.supplier_id:
                obj.supplier_id = comm_id.name.id
            obj.commission_per = round((obj.product_id.standard_price / obj.price_unit) * 100,
                                       2)  # comm_id.name.commission or 0.0
            obj.commission = obj.product_id.standard_price  # (obj.price_unit * obj.commission_per / 100) * obj.qty

    commission = fields.Float(compute=_get_commission, string="Commission Amt",
                              digits=dp.get_precision('Account'), multi="sum", store=True)
    supplier_id = fields.Many2one('res.partner', 'Supplier', compute=_get_commission, multi="sum", store=True)
    commission_per = fields.Float(compute=_get_commission,
                                  string="Commission(%)", digits=dp.get_precision('Account'), multi="sum")
    commission_id = fields.Many2one('pos.commission', 'Commission ', copy=False)


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):

        if self._context.get('default_model') == 'pos.commission' and self._context.get('default_res_id'):
            if not self.filtered('subtype_id.internal'):
                order = self.env['pos.commission'].browse([self._context['default_res_id']])
                if order.state == 'rfi':
                    order.state = 'rfis'
        return super(MailComposeMessage, self.with_context(mail_post_autofollow=True)).send_mail(
            auto_commit=auto_commit)

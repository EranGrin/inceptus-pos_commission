# -*- coding: utf-8 -*-
# Part of Inceptus ERP Solutions Pvt.ltd.
# See LICENSE file for copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Invoice(models.Model):

    _name = 'account.invoice'

    _inherit = ["account.invoice", "ies.base"]

    commission_id = fields.Many2one('pos.commission', 'POS Commission')
    is_commission = fields.Boolean('Is Commission')
    
    
    @api.onchange('date_due', 'date_invoice')
    def onchange_dates(self):
        if self.commission_id and self.type == 'in_invoice':
            self.commission_id.write({'date_due': self.date_due, 
                                      'date_rfci': self.date_invoice})
    
    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual',
        'move_id.line_ids.currency_id')
    def _compute_residual(self):
        if self.commission_id and self.commission_id.invoice_id and self.type == 'in_invoice':
            vals = {'state': self.state}
            if self.state == 'cancel':
                vals.update({'invoice_id': False})
                self.commission_id.write(vals)
        return super(Invoice, self)._compute_residual()

class InvoiceLine(models.Model):

    _inherit = 'account.invoice.line'
    
    commission_id = fields.Many2one('pos.commission', "Commission")

class InvoiceRefund(models.TransientModel):
    
    _inherit = 'account.invoice.refund'
    
    @api.multi
    def compute_refund(self, mode='refund'):
        res = super(InvoiceRefund, self).compute_refund(mode)
        created_invoice = []
        if res.get('domain'):
            for domain in res.get('domain'):
                if domain[0] == 'id':
                    created_invoice = domain[2]
        invoice_rec = self.env['account.invoice'].browse(created_invoice)
        invoice_rec.write({'commission_id' : self._context.get('commission_id'), 'is_commission': True})
        return res


class Payment(models.Model):
    
    _name = 'account.payment'

    _inherit = ["account.payment", "ies.base"]


    
    @api.model
    def default_get(self, fields):
        context = self._context.copy()
        if self._context.get('commission_inv'):
            context.update({
                    'default_invoice_ids':[[4, self._context.get('commission_inv'), None]],
                    'active_model': 'account.invoice',
                    'active_ids': [self._context.get('commission_inv')],
                    'active_id':self._context.get('commission_inv')
                })
        rec = super(Payment, self.with_context(context)).default_get(fields)
        return rec
    
    @api.multi
    def post(self):
        res = super(Payment, self).post()
        invoice_rec = self.env['account.invoice'].browse(self._context.get('active_id'))
        if self._context.get('commission_inv'):
            if self._context.get('commission_id'):
                commission_rec = self.env['pos.commission'].browse(self._context.get('commission_id'))
                commission_rec.state = 'paid'
        elif self._context.get('commission_id') and invoice_rec.type == 'in_refund':
            commission_rec = self.env['pos.commission'].browse(self._context.get('commission_id'))
            commission_rec.state = 'refund'
            commission_rec.refund_invoice = invoice_rec.id
            commission_rec.refund_amount = invoice_rec.amount_total - invoice_rec.residual
        return res

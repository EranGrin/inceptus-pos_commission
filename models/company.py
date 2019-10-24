# -*- coding: utf-8 -*-
# Part of Inceptus ERP Solutions Pvt.ltd.
# See LICENSE file for copyright and licensing details.

from odoo import api, fields, models, _


class Company(models.Model):

    _inherit = "res.company"

    journal_id = fields.Many2one('account.journal', 'Commission Journal')
    account_id = fields.Many2one(
        'account.account', 'Commission Expense Account')
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

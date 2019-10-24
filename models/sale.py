# -*- coding: utf-8 -*-
# Part of Inceptus ERP Solutions Pvt.ltd.
# See LICENSE file for copyright and licensing details.

import time
from datetime import datetime
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class SaleOrder(models.Model):

    _inherit = 'sale.order'
    
    commission_id = fields.Many2one('pos.commission', 'Commission', ondelete='set null')
    
    @api.multi
    def action_confirm(self):
        commission_env = self.env['pos.commission']
        commission_dict = {}
        commission_lines = []
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            for line in order.order_line:
                ref_name = '%s'% (order.name)
                commission_lines.append((0, 0, {
                    'name': ref_name,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_uom_qty or 0.0,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.price_unit,
                    'so_line_id': line.id,
                    'date': datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'tax_ids' : [(4, x.id) for x in line.product_id.supplier_taxes_id]
                }))
                
                if line.product_id.default_seller_id:
                    commission_rec = commission_env.search([('state', '=', 'rfi'),
                                    ('partner_id', '=', line.product_id.default_seller_id.id),], limit=1)
                    
                    if len(commission_rec):
                        commission_rec.line_ids = commission_lines
                    else:
                        commission_dict.update({
                            'partner_id': line.product_id.default_seller_id.id,
                            'line_ids': commission_lines,
                        })
                        commission_rec = commission_env.create(commission_dict)
                    line.commission_id = commission_rec.id
        return res
            
    
    
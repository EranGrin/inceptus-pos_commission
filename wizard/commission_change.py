# -*- coding: utf-8 -*-
# Part of Inceptus ERP Solutions Pvt.ltd.
# See LICENSE file for copyright and licensing details.

from odoo import fields, models, _, api
from odoo.exceptions import UserError

class CommissionChange(models.TransientModel):
    
    _name = 'commission.change'
    
    product_id = fields.Many2one('product.product', required=1)
    commission = fields.Float('Commission Amount', required=1)
    
    
    @api.multi
    def change_commission(self):
        line_env = self.env['pos.commission.line']
        commission_env = self.env['pos.commission'].browse(self._context.get('active_id'))
        if commission_env.state not in ('rfi', 'rfis'):
            raise UserError(_('Commission can only be changed in RFCI and RFCI sent stage!'))
        for rec in self:
            rec.product_id.standard_price = self.commission
            for seller in rec.product_id.seller_ids:
                if commission_env.partner_id.id == seller.name.id:
                    seller.price = self.commission
        return True 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- coding: utf-8 -*-
# Part of Inceptus ERP Solutions Pvt.ltd.
# See LICENSE file for copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):

    _inherit = 'product.template'

    @api.multi
    @api.depends('seller_ids.price', 'seller_ids.sequence')
    def get_seller(self):
        for seller in self.seller_ids.sorted('sequence'):
            self.default_seller_id = seller.name.id
            self.standard_price = seller.price
            break
        return True

    default_seller_id = fields.Many2one('res.partner', "Default Vendor",
                        compute=get_seller)
    commission_ok = fields.Boolean('Commission Product', help="Enable Commission on POS")

    @api.onchange('standard_price')
    def onchange_cost(self):
        if self.standard_price and self.seller_ids and self.default_seller_id:
            for seller in self.seller_ids:
                if self.default_seller_id.id == seller.name.id:
                    seller.price = self.standard_price

class Product(models.Model):

    _inherit = 'product.product'
    
    @api.multi
    @api.depends('seller_ids.price', 'seller_ids.sequence')
    def get_seller(self):
        for rec in self:
            for seller in rec.seller_ids.sorted('sequence'):
                rec.default_seller_id = seller.name.id
                rec.standard_price = seller.price
                break
        return True
    
    default_seller_id = fields.Many2one('res.partner', "Default Vendor",
                        compute=get_seller)
    
    @api.onchange('standard_price')
    def onchange_cost(self):
        if self.standard_price and self.seller_ids and self.default_seller_id:
            for seller in self.seller_ids:
                if self.default_seller_id.id == seller.name.id:
                    seller.price = self.standard_price
    
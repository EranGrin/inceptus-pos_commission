# -*- coding: utf-8 -*-
# Part of Inceptus ERP Solutions Pvt.ltd.
# See LICENSE file for copyright and licensing details.

from odoo import api, fields, models, _


class Users(models.Model):
    _inherit = 'res.users'

    pos_config = fields.Many2one('pos.config', 'Default Point of Sale', required=True,
                                 domain=[('state', '=', 'active')])

    # #Method for multi shop scenario
    # shop_id = fields.Many2one('sale.shop', 'Current Shop')

    # def get_selected_shop(self, cr, uid, context=None):
    #     shop_obj = self.pool.get('sale.shop')
    #     user_obj = self.pool.get('res.users')
    #     if context is None: context = {}
    #     shop = False
    #     if 'pos_shop_id' in context:
    #         shop = shop_obj.search(cr, uid, [('id', '=', context['pos_shop_id'])])
    #         if shop: shop = shop_obj.browse(cr, uid, shop[0])
    #     if not shop:
    #         user = user_obj.browse(cr, uid, uid)
    #         shop = user.shop_id or (user.pos_config and user.pos_config.shop_id)
    #     return shop or False

    # def get_default_shop_id(self, cr, uid, context={}):
    #     user_obj = self.pool.get('res.users').browse(cr, uid, uid)
    #     return user_obj.shop_id.id or (user_obj.pos_config and user_obj.pos_config.shop_id.id) or False
    #
    # def get_default_pos_stock_location_id(self, cr, uid, context={}):
    #     user_obj = self.pool.get('res.users').browse(cr, uid, uid)
    #     return (user_obj.shop_id and user_obj.shop_id.warehouse_id.lot_stock_id.id) or (
    #                 user_obj.pos_config and user_obj.pos_config.shop_id.warehouse_id.lot_stock_id.id) or False

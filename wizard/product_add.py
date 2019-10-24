# -*- coding: utf-8 -*-
# Part of Inceptus ERP Solutions Pvt.ltd.
# See LICENSE file for copyright and licensing details.

from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError


class ProductAdd(models.TransientModel):
    _name = 'product.add.wiz'

    @api.multi
    @api.depends('product_id', 'price_unit', 'product_qty', 'commission')
    def _get_commission(self):
        for obj in self:
            if obj.commission:
                obj.commission_per = (
                                             (obj.commission) / obj.price_unit) * 100
            obj.commission_total = obj.commission * obj.product_qty

    is_return = fields.Boolean('Is Return')
    name = fields.Char("Reference", required=1)
    product_id = fields.Many2one('product.product', required=1, string="Product")

    product_qty = fields.Float(string='Quantity',
                               digits=dp.get_precision('POS'), required=True)

    price_unit = fields.Float(string='Unit Price', required=True,
                              digits=dp.get_precision('Product Price'))

    commission = fields.Float(string="Commission",
                              digits=dp.get_precision('Account'), required=True, )

    commission_total = fields.Float(compute='_get_commission', string="Total Commission",
                                    digits=dp.get_precision('Account'), store=True)

    commission_per = fields.Float(compute='_get_commission',
                                  string="Commission(%)", digits=dp.get_precision('Account'),
                                  store=True)

    @api.onchange('product_id')
    def onchange_product(self):
        vals = {}
        if self.product_id:
            vals = {
                'product_qty': 1,
                'price_unit': self.product_id.lst_price,
                'commission': self.product_id.standard_price
            }
        self.update(vals)

    @api.multi
    def add_line(self):
        if len(self._context.get('active_ids')) > 1:
            raise UserError(_('Please select single record!'))
        model_rec = self.env[self._context.get('active_model')].browse(self._context.get('active_ids'))
        if model_rec.state not in ('rfi', 'rfis'):
            raise UserError(_('Product can only be added in RFCI and RFCI sent stage!'))
        for rec in self:
            vals = {
                'name': rec.name,
                'product_id': rec.product_id.id,
                'product_qty': rec.product_qty or 1,
                'product_uom': rec.product_id.uom_po_id.id,
                'price_unit': rec.price_unit,
                'date': datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT),
            }
            if not rec.is_return:
                model_rec.line_ids = [(0, 0, vals)]
            else:
                if rec.product_qty > 0:
                    raise UserError(_('Product return quantity should be negative!'))
                model_rec.return_line_ids = [(0, 0, vals)]
        return True

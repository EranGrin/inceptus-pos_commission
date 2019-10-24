# -*- coding: utf-8 -*-
# Part of Inceptus ERP Solutions Pvt.ltd.
# See LICENSE file for copyright and licensing details.

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
import time


class res_partner(models.Model):

	_inherit = "res.partner"

	rfci_ids = fields.One2many('pos.commission', 'partner_id', 'Commission History')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

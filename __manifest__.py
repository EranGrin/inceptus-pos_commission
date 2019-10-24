# -*- coding: utf-8 -*-
# Part of Inceptus ERP Solutions Pvt.ltd.
# See LICENSE file for copyright and licensing details.

# todo: check commission history

{
    'name' : 'Inceptus POS Commission',
    'version' : '2.4',
    'author' : 'Inceptus.io',
    'category' : 'Point of Sale',
    'summary': 'Supplier Commission for POS',
    'description' : """
        User can configure Supplier commission percentage, on sell of supplier
        product commission amount posted to related supplier .
        Also expenses chart updated based on posted supplier commission.
    """,
    'website': 'http://www.inceptus.io',
    'depends' : ['point_of_sale', 'purchase', 'account', 'ies_base'],
    'data': [
        'security/ir.model.access.csv',
        'report/commission_report.xml',
        'report/commission_report_vendor.xml',
        'data/pos_commission_data.xml',
        'wizard/commission_change_view.xml',
        'wizard/product_add_view.xml',
        'views/partner_view.xml',
        'views/company_view.xml',
        'views/product_view.xml',
        'views/pos_view.xml',
        'views/invoice_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,

    'price': 99.00,
    'currency': 'EUR',
    'license': 'OPL-1',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
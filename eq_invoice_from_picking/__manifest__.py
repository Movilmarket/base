# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################
{
    'name': "Invoice From Picking",
    'category': 'Accounting',
    'version': '1.0',
    'author': 'Equick ERP',
    'description': """
        This Module allows you to create invoice from picking.
    """,
    'summary': """
        This Module allows you to create invoice from picking.
    """,
    'depends': ['base', 'sale_management', 'stock', 'purchase'],
    'price': 25,
    'currency': 'EUR',
    'license': 'AGPL-3',
    'website': "",
    'data': [
        'views/stock_view.xml',
    ],
    'demo': [],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
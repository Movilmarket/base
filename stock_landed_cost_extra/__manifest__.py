# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'WMS Landed Costs Extra',
    'version': '1.0',
    'category' : 'Warehouse',
    'summary': 'Landed Costs Extra',
    'description': """
Landed Costs Extra
========================    
This module allows to purchase purchase order documents, inbound transfers and supplier invoices at a shipping cost.
    """,
    'author': 'DSA Software SG, C.A.',
    'website': 'http://dsasoftware.com.ve',
    'support': 'https://www.freelancer.es/get/dsasoftware?f=give',
    'depends': [
            'purchase',
            'stock',
            'account',
            'stock_landed_costs'
    ],
    'data':[
        'views/purchase_view.xml',
        'views/account_invoice_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_landed_cost_view.xml',
    ],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

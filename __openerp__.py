# -*- coding: utf-8 -*-
{
    'name': "unicornio",

    'summary': """
       Personalizaciones""",

    'description': """
   Personalizaciones
    """,

    'author': "Nayeli Valencia Díaz",
    'website': "http://www.xmarts.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','purchase','stock','delivery'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #
        'views/views.xml',
        'views/templates.xml',
        'views/quotation_menu.xml',
        'views/route_views.xml',
        'views/stock_location_informative.xml',
        'report/report_saleorder.xml',
        'report/layout.xml',
        'report/invoice_report.xml',
        'report/report_cotizador.xml',
        'report/report_ubication.xml',
        'report/delivery_slip.xml',
        'report/report_purchaseorder.xml',
        'report/report_stockpicking_operations.xml',
        'report/purchase_order_report_ing.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "auto_install": False,
    "installable": True,
}
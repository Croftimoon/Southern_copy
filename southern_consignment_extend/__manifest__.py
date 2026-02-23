{
    'name': 'Southern Implants Consignment Extend',
    'version': '17.0.7.0.4',
    'category': 'Invoice',
    'summary': """
        This module will allow creation of customer master product records
    """,
    'description': '',
    'author': 'Crofti Innovations',
    'website': "https://crofti.com",
    'depends': ['base', 'setu_customer_consignment'],
    'data': [
        'wizards/import_partner_consignment_wizard_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/sale_order_views.xml',
        'security/ir.model.access.csv',
    ],
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
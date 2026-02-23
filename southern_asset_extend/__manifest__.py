{
    'name': 'Southern Implants Asset Extend',
    'version': '17.0.1.0.0',
    'category': 'Invoice',
    'summary': """
        This module will allow mapping of assets to employees
    """,
    'description': '',
    'author': 'Crofti Innovations',
    'website': "https://crofti.com",
    'depends': ['base', 'account_asset', 'hr'],
    'data': [
        'views/account_asset_views.xml',
        'views/hr_employee_views.xml',
    ],
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
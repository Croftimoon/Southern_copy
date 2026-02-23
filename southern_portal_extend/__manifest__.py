{
    'name': 'Southern Implants Portal Extend',
    'version': '17.0.1.0.0',
    'category': 'Invoice',
    'summary': """
        Adds a Total column next to Amount Due in the portal invoices list
    """,
    'description': '',
    'author': 'Crofti Innovations',
    'website': "https://crofti.com",
    'depends': ['portal', 'account'],
    'data': [
        'views/account_portal_templates.xml',
    ],
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
{
    'name': 'Southern Implants Expense Extend',
    'version': '17.0.1.0.0',
    'category': 'Invoice',
    'summary': """
        This module will allow filtering of expense categories by group
    """,
    'description': '',
    'author': 'Crofti Innovations',
    'website': "https://crofti.com",
    'depends': ['base', 'hr_expense'],
    'data': [
        'views/product_views.xml',
    ],
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
{
    'name': 'Crofti Import Framework',
    'version': '17.0.2.0.3',
    'category': 'Invoice',
    'summary': """
        This module will allow bulk importing data
    """,
    'description': '',
    'author': 'Crofti Innovations',
    'website': "https://crofti.com",
    'depends': ['base'],
    'data': [
        'views/import_script_views.xml',
        'security/ir.model.access.csv',
        'wizards/import_script_wizard_views.xml',
        'wizards/query_csv_wizard_views.xml',
    ],
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
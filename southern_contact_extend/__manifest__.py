{
    'name': 'Southern Implants Contact Extend',
    'version': '17.0.0.1.0',
    'category': 'Invoice',
    'summary': """
        This module will allow creation of contact alternate codes
    """,
    'description': '',
    'author': 'Crofti Innovations',
    'website': "https://crofti.com",
    'depends': ['base'],
    'data': [
        'views/res_partner_views.xml',
        'data/res_partner_ref_sequence.xml',
        'security/ir.model.access.csv'
    ],
    'images': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
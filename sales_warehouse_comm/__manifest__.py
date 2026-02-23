{
    'name': 'Sales Warehouse Communication',
    'version': '17.0.2.0.0',
    'category': 'Sales/Inventory',
    'summary': 'Enable communication between sales team and warehouse staff via chatter',
    'description': """
        This module allows:
        - Adding notes on sales orders that appear on picking orders
        - Two-way messaging between sales team and warehouse staff using chatter
        - Automatic cross-posting of messages between related records
    """,
    'depends': ['sale', 'stock', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'wizards/send_message_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
{
    'name': 'Spreadsheet Import for Orders',
    'version': '17.0.5.0.0',
    'category': 'Sales/Purchase',
    'summary': 'Upload spreadsheets to add products to sales and purchase orders',
    'description': """
        This module adds the ability to upload spreadsheets (Excel, CSV) to both
        sales orders and purchase orders. It automatically detects product codes
        and quantities from various column formats and adds them to existing orders.

        Features:
        - Support for Excel (.xlsx, .xls) and CSV files
        - Flexible column detection (product codes, quantities, descriptions)
        - Handles unknown formats and additional columns
        - Smart mapping of product references
        - Validation and error reporting
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['sale_management', 'purchase', 'setu_customer_consignment'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/spreadsheet_import_wizard_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'southern_stock_import/static/src/js/spreadsheet_import.js',
            'southern_stock_import/static/src/scss/spreadsheet_import.scss',
            'southern_stock_import/static/src/xml/dropdown_template.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
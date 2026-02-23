{
    'name': 'Purchase Order SI Navision Integration',
    'version': '17.0.1.0.0',
    'category': 'Purchases',
    'summary': 'Send purchase order lines to SI Navision via email with Excel attachment',
    'description': """
        Purchase Order SI Navision Integration
        =====================================

        This module adds functionality to send purchase order line items to SI Navision contacts:

        Features:
        ---------
        * Add "Send to SI Navision" button on confirmed purchase orders
        * Email wizard to select recipients (contacts with is_company=False)
        * Automatic Excel file generation with purchase order lines
        * Excel format: Type (always "item"), Code (product default_code), Quantity
        * Customizable email subject and body
        * Email attachment with Excel spreadsheet

        Usage:
        ------
        1. Confirm a purchase order
        2. Click "Send to SI Navision" button
        3. Select recipients from contacts
        4. Customize email content if needed
        5. Send email with Excel attachment
    """,
    'depends': [
        'purchase',
        'mail',
    ],
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_navision_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
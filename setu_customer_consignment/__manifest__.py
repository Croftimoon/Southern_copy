# -*- coding: utf-8 -*-
{
    'name': "Consignment Management",
    'version': '17.0.0.2',
    'price': 149,
    'currency': 'EUR',
    'summary': """
        consignment management, customer consignment, consignment inventory management, consignment invoice,
        consignment analytics and reporting, 'consignment orders management, manage multiple consignees,
        import consignment transaction, minimize inventory risk by returning unsold products, reordering,
        manage inventory, product management,
       """,
    'description': """
        Consignment management is the process of managing goods that are held in stock by a third-party seller (consignee),
        but still owned by the original consignor or supplier. The consignee (the third-party seller) 
        agrees to sell the goods on behalf of the consignor, but the consignor retains ownership of the goods 
        until they are sold. 
        Setu's consignment management solution can help your business streamline the entire consignment process, 
        from managing consignment orders to monitoring consignment inventory, handling consignment returns, 
        and even analytical reports of the consignment process
    """,
    'website': 'https://www.setuconsulting.com',
    'support': 'support@setuconsulting.com',
    'author': 'Setu Consulting Services Pvt. Ltd.',
    'images': ['static/description/banner.gif'],
    #'category': '',
    'license': 'OPL-1',
    'sequence': 31,
    'depends': ['sale_stock', 'sale_management', 'stock'],
    'data': [
        'security/setu_consignment_group.xml',
        'data/create_warehouses.xml',
        'views/setu_consignment_ledger_report.xml',
        'views/stock_picking.xml',
        'views/stock_warehouse.xml',
        'views/res_partner.xml',
        'views/stock_location.xml',
        'views/product_product.xml',
        'views/sale_order_view.xml',
        'views/stock_move_line.xml',
        'views/account_move.xml',
        'wizard/customer_consignment_report_wizard.xml',
        'views/customer_consignment_report_view.xml',
        'wizard/product_consignment_report_wizard.xml',
        'views/product_consignment_report_view.xml',
        'wizard/setu_consignment_ledger_report.xml',
        'wizard/book_sale_wizard.xml',
        'security/ir.model.access.csv',
        'views/customer_consignment_menu.xml',
        'db_function/consignment_get_all_data.sql',
        'db_function/get_consignment_customer_data.sql',
        'db_function/get_consignment_product_data.sql',
        'db_function/consignment_ledger_analysis.sql'
    ],
    'application': True,
    #'live_test_url' : 'https://www.youtube.com/channel/UCUxH_derG7MpEhFbXwJ99jA/playlists',
}

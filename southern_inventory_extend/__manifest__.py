{
    'name': 'Southern Inventory Extend',
    'version': '17.0.2.0.0',
    'summary': 'Adds editable tracking number field to stock picking barcode view',
    'depends': ['stock_barcode', 'stock_delivery'],
    'data': [
        'views/barcode_picking_view.xml',
        'views/delivery_carrier_views.xml',
        'views/stock_inventory_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'your_module_name/static/src/js/barcode_scanner_tracking_ref.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'OEEL-1',
}

{
    'name': 'SanQua Stock Inventory Report Customization',
    'version': '1.0',
    'category': 'Warehouse',
    'summary': 'Custom stock inventory report with filters',
    'author': 'Oki Ramadani',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_inventory_wizard_view.xml',
        'views/stock_inventory_report_menu.xml',
        'views/stock_inventory_report_action.xml',
        'reports/stock_inventory_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

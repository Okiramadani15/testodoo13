{
    'name': 'SanQua Inventory Report',
    'version': '1.0',
    'category': 'inventory',
    'summary': 'Kustomisasi penjualan dan manajemen pelanggan untuk SanQua',
    'description': 'Modul untuk mengatur divisi, batas kredit, dan pelaporan penjualan khusus SanQua',
    'author': 'oki ramadani',
    'website': 'https://www.testsanquaoki.com',
    'depends': ['sale', 'stock', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_inventory_report_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
{
    'name': 'SanQua Sales Customization',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Kustomisasi penjualan dan manajemen pelanggan untuk SanQua',
    'description': 'Modul untuk mengatur divisi, batas kredit, dan pelaporan penjualan khusus SanQua',
    'author': 'oki ramadani',
    'depends': ['sale', 'stock', 'base', 'product', 'sale_management', 'sales_team',],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/sanqua_division_views.xml',
        'views/product_views.xml',
        'views/risk_tracking_views.xml',
        'data/risk_tracking_cron.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
from odoo import models, fields, api

class StockInventoryReport(models.TransientModel):
    _name = 'stock.inventory.report'
    _description = 'Stock Inventory Report'

    product_id = fields.Many2one('product.product', string='Product')
    product_code = fields.Char(related='product_id.default_code', string='Product Code', readonly=True)
    product_name = fields.Char(related='product_id.name', string='Product Name', readonly=True)
    saldo_awal = fields.Float(string='Saldo Awal', readonly=True)
    total_masuk = fields.Float(string='Total Masuk', readonly=True)
    total_keluar = fields.Float(string='Total Keluar', readonly=True)
    saldo_akhir = fields.Float(string='Saldo Akhir', readonly=True)

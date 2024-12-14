from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    division_id = fields.Many2one(
        'sanqua.division', 
        string='Divisi Produk',
        required=True
    )
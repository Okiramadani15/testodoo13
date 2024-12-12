from odoo import models, fields, api

class SanquaDivision(models.Model):
    _name = 'sanqua.division'
    _description = 'Divisi Produk SanQua'
    
    name = fields.Selection([
        ('SQA', 'SanQua'),
        ('GLN', 'Galon'),
        ('BTV', 'Batavia'),
        ('BVG', 'Minuman')
    ], string='Nama Divisi', required=True)
    
    code = fields.Char('Kode Divisi', required=True)
    description = fields.Text('Deskripsi')
    
    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Kode divisi harus unik!')
    ]
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    division_ids = fields.Many2many(
        'sanqua.division', 
        string='Divisi',
        help='Divisi yang dimiliki pelanggan'
    )
    credit_limits = fields.One2many(
        'sanqua.credit.limit', 
        'partner_id', 
        string='Batas Kredit'
    )

class SanquaCreditLimit(models.Model):
    _name = 'sanqua.credit.limit'
    _description = 'Batas Kredit Pelanggan'
    
    partner_id = fields.Many2one('res.partner', string='Pelanggan', required=True)
    division_id = fields.Many2one('sanqua.division', string='Divisi', required=True)
    credit_limit = fields.Monetary(string='Batas Kredit', required=True)
    currency_id = fields.Many2one('res.currency', string='Mata Uang', 
        default=lambda self: self.env.company.currency_id)
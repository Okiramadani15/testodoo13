from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    division_id = fields.Many2one(
        'sanqua.division', 
        string='Divisi',
        required=True
    )

    # pickup_method = fields.Char(string="Pickup Method")
    pickup_method = fields.Selection([
        ('delivery', 'Delivery'),
        ('take_in_plant', 'Take in Plant')
    ], default='delivery', string='Pickup Method')
    
    # expiration_date = fields.Date('Tanggal Kadaluarsa')
    @api.onchange('division_id')
    def _filter_products_by_division(self):
        # Filter produk berdasarkan divisi yang dipilih
        if self.division_id:
            return {
                'domain': {
                    'order_line.product_id': [
                        ('division_id', '=', self.division_id.id)
                    ]
                }
            }
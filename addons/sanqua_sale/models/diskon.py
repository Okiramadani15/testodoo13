# from odoo.exceptions import ValidationError

# class ProductDiscount(models.Model):
#     _name = 'product.discount'
#     _description = 'Diskon Produk'

#     product_id = fields.Many2one('product.product', string='Produk', required=True)
#     discount_amount = fields.Float(string='Jumlah Diskon', required=True)

#     @api.constrains('discount_amount')
#     def _check_discount_amount(self):
#         if self.discount_amount < 0:
#             raise ValidationError("Jumlah Diskon tidak boleh negatif.")

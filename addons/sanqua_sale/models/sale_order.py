from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type')
    is_overlimit = fields.Boolean(
        string='Over Credit Limit', 
        compute='_compute_customer_status', 
        store=True
    )
    is_overdue = fields.Boolean(
        string='Has Overdue Invoices', 
        compute='_compute_customer_status', 
        store=True
    )
    risk_status = fields.Selection([
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('block', 'Block')
    ], string='Risk Status', 
        compute='_compute_customer_status', 
        store=True
    )
    division_id = fields.Many2one(
        'sanqua.division',
        string='Divisi',
        required=True
    )
    pickup_method = fields.Selection([
        ('delivery', 'Delivery'),
        ('take_in_plant', 'Take in Plant')
    ], default='delivery', string='Pickup Method')

    @api.depends('partner_id', 'amount_total', 'division_id')
    def _compute_customer_status(self):
        for order in self:
            if not order.partner_id or not order.division_id:
                order.update({
                    'is_overlimit': False,
                    'is_overdue': False,
                    'risk_status': 'normal'
                })
                continue

            credit_limit = self._check_credit_limit(order)
            overdue_status = self._check_overdue_invoices(order)

            order.update({
                'is_overlimit': credit_limit['is_overlimit'],
                'is_overdue': overdue_status['is_overdue'],
                'risk_status': self._determine_risk_status(
                    credit_limit['is_overlimit'], 
                    overdue_status['is_overdue']
                )
            })

    def _check_credit_limit(self, order):
        credit_limit_rec = self.env['sanqua.credit.limit'].search([
            ('partner_id', '=', order.partner_id.id),
            ('division_id', '=', order.division_id.id)
        ], limit=1)

        if not credit_limit_rec:
            return {'is_overlimit': False, 'current_balance': 0, 'credit_limit': 0}

        days_to_check = 30
        date_threshold = fields.Date.today() - timedelta(days=days_to_check)

        domain = [
            ('partner_id', '=', order.partner_id.id),
            ('division_id', '=', order.division_id.id),
            ('state', 'not in', ['draft', 'cancel']),
            ('date_order', '>=', date_threshold)
        ]
        orders = self.env['sale.order'].search(domain)
        total_used = sum(orders.mapped('amount_total'))

        is_overlimit = (total_used + order.amount_total) > credit_limit_rec.credit_limit

        return {
            'is_overlimit': is_overlimit, 
            'current_balance': total_used,
            'credit_limit': credit_limit_rec.credit_limit
        }

    def _check_overdue_invoices(self, order):
        overdue_invoices = self.env['account.move'].search([
            ('partner_id', '=', order.partner_id.id),
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_payment_state', '=', 'not_paid'),
            ('invoice_date_due', '<', date.today())
        ])

        return {
            'is_overdue': bool(overdue_invoices),
            'overdue_count': len(overdue_invoices)
        }

    def _determine_risk_status(self, is_overlimit, is_overdue):
        if is_overlimit and is_overdue:
            return 'block'
        elif is_overlimit or is_overdue:
            return 'warning'
        return 'normal'

    def action_confirm(self):
        for order in self:
            if order.risk_status == 'warning':
                warnings = []
                if order.is_overlimit:
                    warnings.append("Perhatian: Order melebihi batas kredit!")
                if order.is_overdue:
                    warnings.append("Perhatian: Terdapat invoice yang belum dibayar!")

                if warnings:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': "\n".join(warnings),
                            'type': 'warning',
                            'sticky': True,
                        }
                    }
            elif order.risk_status == 'block':
                raise ValidationError(
                    "Sales Order tidak dapat dikonfirmasi. "
                    "Customer memiliki status risiko tinggi (Overlimit dan Overdue)."
                )

        return super(SaleOrder, self).action_confirm()

    @api.onchange('division_id')
    def _onchange_division_id(self):
        if self.division_id:
            return {
                'domain': {
                    'partner_id': [('division_ids', 'in', [self.division_id.id])],
                    'order_line.product_id': [('division_id', '=', self.division_id.id)]
                }
            }
        return {
            'domain': {
                'partner_id': [],
                'order_line.product_id': []
            }
        }

    @api.onchange('pickup_method')
    def _update_order_line_discounts(self):
        for line in self.order_line:
            line._apply_take_in_plant_discount()

    def _get_take_in_plant_discount(self, product):
        """Menghitung diskon untuk metode 'take in plant'."""
        if product and self.pickup_method == 'take_in_plant':
            # Contoh logika pemberian diskon berdasarkan kategori produk
            if product.categ_id.name == 'Special':
                return 10  # Diskon tetap 10%
            return 5  # Diskon default 5%
        return 0

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.order_id.division_id and self.product_id:
            if self.product_id.division_id != self.order_id.division_id:
                raise ValidationError(
                    f"Produk {self.product_id.name} tidak sesuai dengan divisi {self.order_id.division_id.name}."
                )

    @api.model
    def _apply_take_in_plant_discount(self):
        if self.order_id.pickup_method == 'take_in_plant':
            discount = self.order_id._get_take_in_plant_discount(self.product_id)
            self.update({
                'discount': discount, 
                'price_unit': self.price_unit - discount
            })
            self.price_subtotal = self.product_uom_qty * self.price_unit















# from odoo import models, fields, api
# from odoo.exceptions import ValidationError, UserError
# from datetime import date, timedelta
# import logging

# _logger = logging.getLogger(__name__)

# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
    
#     picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type')

#     @api.model
#     def _get_take_in_plant_discount(self, product):
#         """
#         Hitung diskon 10% untuk metode Take in Plant berdasarkan produk
#         """
#         if self.pickup_method != 'take_in_plant':
#             return 0

#         return product.lst_price * 0.1

#     def _is_take_in_plant(self):
#         """
#         Validasi apakah metode pengambilan adalah "take in plant"
#         """
#         return self.pickup_method == 'take_in_plant'

#     def apply_discounts_to_order(self):
#         """
#         Terapkan diskon 10% ke semua baris pesanan untuk Take in Plant
#         """
#         if self._is_take_in_plant():
#             for line in self.order_line:
#                 discount = self._get_take_in_plant_discount(line.product_id)
                
#                 # Terapkan diskon langsung ke harga unit
#                 line.price_unit = line.price_unit * 0.9  # Potong 10%
#                 line.discount = 10  # Set diskon 10%
                
#                 # Perbarui subtotal
#                 line.price_subtotal = line.product_uom_qty * line.price_unit

#     # Tambahkan field baru untuk manajemen risiko
#     is_overlimit = fields.Boolean(
#         string='Over Credit Limit', 
#         compute='_compute_customer_status', 
#         store=True
#     )
#     is_overdue = fields.Boolean(
#         string='Has Overdue Invoices', 
#         compute='_compute_customer_status', 
#         store=True
#     )
#     risk_status = fields.Selection([
#         ('normal', 'Normal'),
#         ('warning', 'Warning'),
#         ('block', 'Block')
#     ], string='Risk Status', 
#         compute='_compute_customer_status', 
#         store=True
#     )

#     division_id = fields.Many2one(
#         'sanqua.division',
#         string='Divisi',
#         required=True
#     )

#     pickup_method = fields.Selection([
#         ('delivery', 'Delivery'),
#         ('take_in_plant', 'Take in Plant')
#     ], default='delivery', string='Pickup Method')

#     @api.depends('partner_id', 'amount_total', 'division_id')
#     def _compute_customer_status(self):
#         for order in self:
#             if not order.partner_id or not order.division_id:
#                 order.is_overlimit = False
#                 order.is_overdue = False
#                 order.risk_status = 'normal'
#                 continue

#             # Cek Credit Limit
#             credit_limit = self._check_credit_limit(order)
            
#             # Cek Invoice Overdue
#             overdue_status = self._check_overdue_invoices(order)

#             # Tentukan status risiko
#             order.is_overlimit = credit_limit['is_overlimit']
#             order.is_overdue = overdue_status['is_overdue']
#             order.risk_status = self._determine_risk_status(
#                 credit_limit['is_overlimit'], 
#                 overdue_status['is_overdue']
#             )

#     def _check_credit_limit(self, order):
#         """
#         Periksa apakah pesanan melebihi batas kredit yang ditentukan
#         """
#         credit_limit_rec = self.env['sanqua.credit.limit'].search([
#             ('partner_id', '=', order.partner_id.id),
#             ('division_id', '=', order.division_id.id)
#         ], limit=1)

#         # Jika tidak ada record batas kredit, anggap normal
#         if not credit_limit_rec:
#             return {'is_overlimit': False, 
#                     'current_balance': 0,
#                     'default_limit': 0
#                     }

#         # Hitung total saldo yang sudah digunakan
#         days_to_check = 30  # Misalnya, cek 30 hari terakhir
#         date_threshold = fields.Date.today() - timedelta(days=days_to_check)

#         domain = [
#             ('partner_id', '=', order.partner_id.id),
#             ('division_id', '=', order.division_id.id),
#             ('state', 'not in', ['draft', 'cancel']),
#             ('date_order', '>=', date_threshold)
#         ]
#         orders = self.env['sale.order'].search(domain)
#         total_used = sum(orders.mapped('amount_total'))

#         is_overlimit = (total_used + order.amount_total) > credit_limit_rec.credit_limit

#         return {
#             'is_overlimit': is_overlimit, 
#             'current_balance': total_used,
#             'credit_limit': credit_limit_rec.credit_limit,
#             'orders_count': len(orders)
#         }

#     def _check_overdue_invoices(self, order):
#         """
#         Periksa apakah ada invoice yang sudah jatuh tempo
#         """
#         overdue_invoices = self.env['account.move'].search([
#             ('partner_id', '=', order.partner_id.id),
#             ('type', 'in', ['out_invoice', 'out_refund']),
#             ('state', '=', 'posted'),
#             ('invoice_payment_state', '=', 'not_paid'),
#             ('invoice_date_due', '<', date.today())
#         ])

#         return {
#             'is_overdue': len(overdue_invoices) > 0,
#             'overdue_count': len(overdue_invoices)
#         }

#     def _determine_risk_status(self, is_overlimit, is_overdue):
#         """
#         Tentukan status risiko berdasarkan kondisi kredit dan invoice
#         """
#         if is_overlimit and is_overdue:
#             return 'block'
#         elif is_overlimit or is_overdue:
#             return 'warning'
#         return 'normal'

#     def action_confirm(self):
#         """
#         Override method konfirmasi SO untuk menambahkan warning
#         """
#         for order in self:
#             if order.risk_status == 'warning':
#                 warning_msg = []
#                 if order.is_overlimit:
#                     warning_msg.append("Perhatian: Order melebihi batas kredit!")
#                 if order.is_overdue:
#                     warning_msg.append("Perhatian: Terdapat invoice yang belum dibayar!")
                
#                 # Tampilkan warning menggunakan UserError
#                 if warning_msg:
#                     return {
#                         'type': 'ir.actions.client',
#                         'tag': 'display_notification',
#                         'params': {
#                             'message': "\n".join(warning_msg),
#                             'type': 'warning',
#                             'sticky': True,
#                         }
#                     }
#             elif order.risk_status == 'block':
#                 raise ValidationError(
#                     "Sales Order tidak dapat dikonfirmasi. "
#                     "Customer memiliki status risiko tinggi (Overlimit dan Overdue)."
#                 )
        
#         return super(SaleOrder, self).action_confirm()

#     @api.onchange('division_id')
#     def _onchange_division_id(self):
#         """
#         Filter produk dan pelanggan berdasarkan divisi yang dipilih.
#         """
#         if self.division_id:
#             return {
#                 'domain': {
#                     'partner_id': [('division_ids', 'in', [self.division_id.id])],
#                     'order_line.product_id': [('division_id', '=', self.division_id.id)]
#                 }
#             }
#         else:
#             return {
#                 'domain': {
#                     'partner_id': [],
#                     'order_line.product_id': []
#                 }
#             }

#     @api.onchange('pickup_method')
#     def _update_order_line_discounts(self):
#         """
#         Perbarui diskon untuk semua baris pesanan jika metode pengambilan berubah.
#         """
#         for line in self.order_line:
#             line._apply_take_in_plant_discount()


# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'

#     @api.onchange('product_id')
#     def _onchange_product_id(self):
#         """ Validasi bahwa produk sesuai dengan divisi yang dipilih pada SO. """
#         if self.order_id.division_id and self.product_id:
#             if self.product_id.division_id != self.order_id.division_id:
#                 raise ValidationError(
#                     f"Produk {self.product_id.name} tidak sesuai dengan divisi {self.order_id.division_id.name}."
#                 )

#     @api.onchange('product_id')
#     def _set_unit_price_from_pricelist(self):
#         """ Set harga produk berdasarkan pricelist divisi pelanggan. """
#         if self.order_id.partner_id and self.order_id.division_id and self.product_id:
#             # Ambil pricelist yang terkait dengan divisi
#             pricelist = self.order_id.division_id.pricelist_id

#             # Jika pricelist divisi tidak ada, gunakan pricelist partner
#             if not pricelist:
#                 pricelist = (
#                     self.order_id.pricelist_id or 
#                     self.order_id.partner_id.property_product_pricelist
#                 )

#             if pricelist:
#                 # Dapatkan harga produk dari pricelist
#                 price = pricelist.get_product_price(
#                     self.product_id,
#                     self.product_uom_qty or 1.0,
#                     self.order_id.partner_id
#                 )
#                 self.price_unit = price


#     @api.model
#     def _apply_take_in_plant_discount(self):
#         """
#         Terapkan diskon jika metode pengambilan adalah "take in plant".
#         """
#         if self.order_id._is_take_in_plant():
#             discount = self.order_id._get_take_in_plant_discount(self.product_id)
#             self.update({'discount': discount, 'price_unit': self.price_unit - discount})
#             self.price_subtotal = self.product_uom_qty * self.price_unit

#     @api.onchange('pickup_method')
#     def _update_line_for_take_in_plant(self):
#         """
#         Perbarui harga baris pesanan saat metode pengambilan berubah
#         """
#         for line in self:
#             if line.order_id._is_take_in_plant():
#                 # Hitung diskon 10%
#                 line.price_unit = line.price_unit * 0.9
#                 line.discount = 10
                
# class PickupDiscount(models.Model):
#     _name = 'sanqua.pickup.discount'
#     _description = 'Pickup Discount'

#     product_id = fields.Many2one('product.product', string='Product', required=True)
#     discount_amount = fields.Float(string='Discount Amount', required=True)
#     active = fields.Boolean(default=True)
#     company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)




from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Tambahkan field baru untuk manajemen risiko
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
                order.is_overlimit = False
                order.is_overdue = False
                order.risk_status = 'normal'
                continue

            # Cek Credit Limit
            credit_limit = self._check_credit_limit(order)
            
            # Cek Invoice Overdue
            overdue_status = self._check_overdue_invoices(order)

            # Tentukan status risiko
            order.is_overlimit = credit_limit['is_overlimit']
            order.is_overdue = overdue_status['is_overdue']
            order.risk_status = self._determine_risk_status(
                credit_limit['is_overlimit'], 
                overdue_status['is_overdue']
            )

    def _check_credit_limit(self, order):
        """
        Periksa apakah pesanan melebihi batas kredit yang ditentukan
        """
        credit_limit_rec = self.env['sanqua.credit.limit'].search([
            ('partner_id', '=', order.partner_id.id),
            ('division_id', '=', order.division_id.id)
        ], limit=1)

        # Jika tidak ada record batas kredit, anggap normal
        if not credit_limit_rec:
            return {'is_overlimit': False, 'current_balance': 0}

        # Hitung total saldo yang sudah digunakan
        domain = [
            ('partner_id', '=', order.partner_id.id),
            ('division_id', '=', order.division_id.id),
            ('state', 'not in', ['draft', 'cancel'])
        ]
        total_used = sum(self.env['sale.order'].search(domain).mapped('amount_total'))

        is_overlimit = (total_used + order.amount_total) > credit_limit_rec.credit_limit

        return {
            'is_overlimit': is_overlimit, 
            'current_balance': total_used
        }

    def _check_overdue_invoices(self, order):
        """
        Periksa apakah ada invoice yang sudah jatuh tempo
        """
        overdue_invoices = self.env['account.move'].search([
            ('partner_id', '=', order.partner_id.id),
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_payment_state', '=', 'not_paid'),
            ('invoice_date_due', '<', date.today())
        ])

        return {
            'is_overdue': len(overdue_invoices) > 0,
            'overdue_count': len(overdue_invoices)
        }

    def _determine_risk_status(self, is_overlimit, is_overdue):
        """
        Tentukan status risiko berdasarkan kondisi kredit dan invoice
        """
        if is_overlimit and is_overdue:
            return 'block'
        elif is_overlimit or is_overdue:
            return 'warning'
        return 'normal'

    def action_confirm(self):
        """
        Override method konfirmasi SO untuk menambahkan warning
        """
        for order in self:
            if order.risk_status == 'warning':
                warning_msg = []
                if order.is_overlimit:
                    warning_msg.append("Perhatian: Order melebihi batas kredit!")
                if order.is_overdue:
                    warning_msg.append("Perhatian: Terdapat invoice yang belum dibayar!")
                
                # Tampilkan warning menggunakan UserError
                if warning_msg:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': "\n".join(warning_msg),
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
        """
        Filter produk dan pelanggan berdasarkan divisi yang dipilih.
        """
        if self.division_id:
            return {
                'domain': {
                    'partner_id': [('division_ids', 'in', [self.division_id.id])],
                    'order_line.product_id': [('division_id', '=', self.division_id.id)]
                }
            }
        else:
            return {
                'domain': {
                    'partner_id': [],
                    'order_line.product_id': []
                }
            }

    @api.onchange('pickup_method')
    def _update_order_line_discounts(self):
        """
        Perbarui diskon untuk semua baris pesanan jika metode pengambilan berubah.
        """
        for line in self.order_line:
            line._apply_take_in_plant_discount()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """ Validasi bahwa produk sesuai dengan divisi yang dipilih pada SO. """
        if self.order_id.division_id and self.product_id:
            if self.product_id.division_id != self.order_id.division_id:
                raise ValidationError(
                    f"Produk {self.product_id.name} tidak sesuai dengan divisi {self.order_id.division_id.name}."
                )

    @api.onchange('product_id')
    def _set_unit_price_from_pricelist(self):
        """ Set harga produk berdasarkan pricelist divisi pelanggan. """
        if self.order_id.partner_id and self.order_id.division_id and self.product_id:
            # Ambil pricelist yang terkait dengan divisi
            pricelist = self.order_id.division_id.pricelist_id

            # Jika pricelist divisi tidak ada, gunakan pricelist partner
            if not pricelist:
                pricelist = (
                    self.order_id.pricelist_id or 
                    self.order_id.partner_id.property_product_pricelist
                )

            if pricelist:
                # Dapatkan harga produk dari pricelist
                price = pricelist.get_product_price(
                    self.product_id,
                    self.product_uom_qty or 1.0,
                    self.order_id.partner_id
                )
                self.price_unit = price

    @api.onchange('order_id.pickup_method', 'product_id')
    def _apply_take_in_plant_discount(self):
        """
        Terapkan diskon khusus untuk metode 'Take in Plant'.
        """
        if self.order_id.pickup_method == 'take_in_plant' and self.product_id:
            sku_discount_map = {
                'PROD001': 10000,  # Contoh diskon spesifik per SKU
                'PROD002': 5000,
            }

            discount_amount = sku_discount_map.get(self.product_id.default_code, 0)
            if discount_amount > 0:
                new_price = self.price_unit - discount_amount
                self.price_unit = max(new_price, 0) 

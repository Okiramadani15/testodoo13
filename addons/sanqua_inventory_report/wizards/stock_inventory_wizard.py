from odoo import models, fields, api

class StockInventoryWizard(models.TransientModel):
    _name = 'stock.inventory.wizard'
    _description = 'Stock Inventory Wizard'

    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    location_id = fields.Many2one('stock.location', string='Plant', required=True)

    def generate_report(self):
        self.ensure_one()
        # Logika pengambilan data
        products = self.env['product.product'].search([])
        report_data = []

        for product in products:
            saldo_awal = self._compute_saldo_awal(product.id)
            total_masuk = self._compute_total_masuk(product.id)
            total_keluar = self._compute_total_keluar(product.id)
            saldo_akhir = saldo_awal + total_masuk - total_keluar

            report_data.append((0, 0, {
                'product_id': product.id,
                'saldo_awal': saldo_awal,
                'total_masuk': total_masuk,
                'total_keluar': total_keluar,
                'saldo_akhir': saldo_akhir,
            }))

        self.env['stock.inventory.report'].create(report_data)

    def _compute_saldo_awal(self, product_id):
        moves = self.env['stock.move'].search([
            ('product_id', '=', product_id),
            ('state', '=', 'done'),
            ('date', '<', self.date_start)
        ])
        return sum(moves.mapped('quantity_done'))

    def _compute_total_masuk(self, product_id):
        moves = self.env['stock.move'].search([
            ('product_id', '=', product_id),
            ('state', '=', 'done'),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('location_dest_id', '=', self.location_id.id)
        ])
        return sum(moves.mapped('quantity_done'))

    def _compute_total_keluar(self, product_id):
        moves = self.env['stock.move'].search([
            ('product_id', '=', product_id),
            ('state', '=', 'done'),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('location_id', '=', self.location_id.id)
        ])
        return sum(moves.mapped('quantity_done'))

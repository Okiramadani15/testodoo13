from odoo import models, fields, api

class StockInventoryWizard(models.TransientModel):
    _name = 'stock.inventory.wizard'
    _description = 'Stock Inventory Wizard'

    product_id = fields.Many2one('product.product', string="Product")
    start_date = fields.Datetime(string='Start Date', required=True)
    end_date = fields.Datetime(string='End Date', required=True)
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

            report_data.append({
                'product_id': product.id,
                'saldo_awal': saldo_awal,
                'total_masuk': total_masuk,
                'total_keluar': total_keluar,
                'saldo_akhir': saldo_akhir,
            })

        # Membuat laporan di model 'stock.inventory.report'
        report = self.env['stock.inventory.report'].create(report_data)

        # Menggunakan action window untuk menampilkan hasil laporan
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Inventory Report',
            'res_model': 'stock.inventory.report',
            'view_mode': 'tree,form',  # Menampilkan laporan dalam tampilan tree dan form
            'target': 'current',  # Menampilkan di jendela yang sama
            'context': {
                'default_product_id': report_data[0]['product_id'],
            },
        }


    def _compute_saldo_awal(self, product_id):
        moves = self.env['stock.move'].search([
            ('product_id', '=', product_id),
            ('state', '=', 'done'),
            ('date', '<', self.start_date)
        ])
        return sum(moves.mapped('quantity_done'))

    def _compute_total_masuk(self, product_id):
        moves = self.env['stock.move'].search([
            ('product_id', '=', product_id),
            ('state', '=', 'done'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('location_dest_id', '=', self.location_id.id)
        ])
        return sum(moves.mapped('quantity_done'))

    def _compute_total_keluar(self, product_id):
        moves = self.env['stock.move'].search([
            ('product_id', '=', product_id),
            ('state', '=', 'done'),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('location_id', '=', self.location_id.id)
        ])
        return sum(moves.mapped('quantity_done'))



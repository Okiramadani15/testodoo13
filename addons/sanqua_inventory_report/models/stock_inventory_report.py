from odoo import models, fields, api
from odoo.exceptions import UserError

class StockInventoryReport(models.TransientModel):
    _name = 'sanqua.stock.inventory.report'
    _description = 'Laporan Persediaan Stok'

    date_from = fields.Date('Dari Tanggal', required=True)
    date_to = fields.Date('Sampai Tanggal', required=True)
    division_id = fields.Many2one('sanqua.division', string='Divisi')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to and record.date_from > record.date_to:
                raise UserError('Tanggal awal tidak boleh lebih besar dari tanggal akhir!')

    def generate_report(self):
        # Persiapkan domain untuk pencarian
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ]

        # Tambahkan filter divisi jika dipilih
        if self.division_id:
            domain.append(('product_id.division_id', '=', self.division_id.id))

        # Ambil data pergerakan stok
        stock_moves = self.env['stock.move'].search(domain)

        # Proses data untuk laporan
        report_data = []
        for move in stock_moves:
            report_data.append({
                'product': move.product_id.name,
                'quantity': move.product_qty,
                'location_from': move.location_id.name,
                'location_to': move.location_dest_id.name,
                'date': move.date
            })

        return report_data
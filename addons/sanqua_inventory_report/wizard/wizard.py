from odoo import models, fields, api
from odoo.exceptions import UserError

class StockInventoryReportWizard(models.TransientModel):
    _name = 'sanqua.stock.inventory.report'
    _description = 'Wizard Laporan Persediaan Stok'

    date_from = fields.Date(string='Dari Tanggal', required=True)
    date_to = fields.Date(string='Sampai Tanggal', required=True)
    division_id = fields.Many2one('sanqua.division', string='Divisi')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """Memastikan Tanggal From tidak lebih besar dari Tanggal To."""
        for record in self:
            if record.date_from and record.date_to and record.date_from > record.date_to:
                raise UserError('Tanggal awal tidak boleh lebih besar dari tanggal akhir!')

    def generate_report(self):
        """Fungsi untuk mengambil data laporan berdasarkan filter."""
        # Filter domain berdasarkan input
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ]

        if self.division_id:
            domain.append(('product_id.division_id', '=', self.division_id.id))

        # Ambil data dari model `stock.move`
        stock_moves = self.env['stock.move'].search(domain)

        if not stock_moves:
            raise UserError('Tidak ada data yang ditemukan untuk kriteria yang dipilih.')

        # Data untuk laporan
        report_data = []
        for move in stock_moves:
            report_data.append({
                'product': move.product_id.name,
                'quantity': move.product_qty,
                'location_from': move.location_id.name,
                'location_to': move.location_dest_id.name,
                'date': move.date
            })

        # Logika untuk menampilkan atau memproses laporan lebih lanjut
        # Misalnya, Anda bisa membuka laporan PDF atau menyimpan file CSV
        return {
            'type': 'ir.actions.report',
            'report_name': 'sanqua_stock_inventory_report_template',
            'report_type': 'qweb-pdf',
            'data': {'report_data': report_data},
        }

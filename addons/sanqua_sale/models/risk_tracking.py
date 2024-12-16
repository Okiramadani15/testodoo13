from odoo import models, fields, api
from datetime import timedelta

class CustomerRiskTracking(models.Model):
    _name = 'sanqua.customer.risk.tracking'
    _description = 'Pelacakan Risiko Pelanggan'

    partner_id = fields.Many2one('res.partner', string='Pelanggan', required=True)
    division_id = fields.Many2one('sanqua.division', string='Divisi')
    
    # Statistik Risiko
    total_overlimit_orders = fields.Integer(string='Total Order Melebihi Limit')
    total_overdue_invoices = fields.Integer(string='Total Invoice Tertunggak')
    
    # Periode Risiko
    risk_start_date = fields.Date(string='Tanggal Mulai Risiko')
    last_risk_assessment = fields.Date(string='Terakhir Dinilai')
    
    # Status Risiko
    risk_level = fields.Selection([
        ('low', 'Rendah'),
        ('medium', 'Sedang'),
        ('high', 'Tinggi')
    ], string='Tingkat Risiko', compute='_compute_risk_level', store=True)

    @api.depends('total_overlimit_orders', 'total_overdue_invoices')
    def _compute_risk_level(self):
        for record in self:
            total_risk_points = record.total_overlimit_orders + record.total_overdue_invoices
            
            if total_risk_points <= 2:
                record.risk_level = 'low'
            elif total_risk_points <= 5:
                record.risk_level = 'medium'
            else:
                record.risk_level = 'high'

    @api.model
    def update_customer_risk(self):
        """
        Metode untuk memperbarui risiko pelanggan secara berkala
        """
        # Ambil semua pelanggan
        partners = self.env['res.partner'].search([])
        
        for partner in partners:
            # Hitung order melebihi limit dalam 90 hari terakhir
            overlimit_orders = self.env['sale.order'].search([
                ('partner_id', '=', partner.id),
                ('is_overlimit', '=', True),
                ('date_order', '>=', fields.Date.today() - timedelta(days=90))
            ])
            
            # Hitung invoice tertunggak
            overdue_invoices = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'posted'),
                ('invoice_payment_state', '=', 'not_paid'),
                ('invoice_date_due', '<', fields.Date.today())
            ])
            
            # Update atau buat record risiko
            risk_tracking = self.search([
                ('partner_id', '=', partner.id)
            ], limit=1)
            
            if not risk_tracking:
                risk_tracking = self.create({
                    'partner_id': partner.id,
                })
            
            risk_tracking.write({
                'total_overlimit_orders': len(overlimit_orders),
                'total_overdue_invoices': len(overdue_invoices),
                'last_risk_assessment': fields.Date.today()
            })
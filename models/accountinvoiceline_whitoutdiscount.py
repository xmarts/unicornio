
from odoo import api, fields, models
from odoo.tools.sql import drop_view_if_exists


class AccountInvoiceLineWhithoutDiscout(models.Model):
    _name = "account.invoice.line.sindescuento"
    _description = "Reporte de lineas sin descuento"
    _auto = False

    id = fields.Integer('id', readonly=True)
    origin = fields.Char('Origen', readonly=True)
    create_date = fields.Datetime('Fecha creacion', readonly=True)
    price_unit = fields.Float('Precio Unitario', readonly=True)
    price_subtotal = fields.Float('Precio total', readonly=True)
    write_uid = fields.Many2one('res.groups', 'Write UID', readonly=True, index=True)
    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True, index=True)
    uom_id = fields.Many2one('product.uom', 'Unidad de Medida', readonly=True, index=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', readonly=True, index=True)
    create_uid =fields.Many2one('res.groups', 'Write UID', readonly=True, index=True)
    sequence =fields.Integer('Secuencia',  readonly=True, index=True)
    company_id = fields.Many2one('res.company', string='Company',  readonly=True, index=True)
    account_analytic_id= fields.Many2one('account.analytic.account', string='Analytic account', readonly=True, index=True)
    account_id = fields.Many2one('account.account', string='Tax Account', readonly=True, index=True)
    discount = fields.Float(string='Discount (%)', readonly=True, index=True)
    write_date = fields.Datetime('Fecha creacion', readonly=True)
    price_subtotal_signed =fields.Monetary(string='Amount Signed', readonly=True, index=True)
    name = fields.Char('Nombre' ,readonly=True, index=True)
    product_id = fields.Many2one('product.product', string='Product',readonly=True, index=True)
    invoice_id=fields.Many2one('account.invoice', string='Invoice',readonly=True, index=True)
    quantity = fields.Float(string='Quantity',readonly=True, index=True)
    layout_category_sequence =fields.Integer('layout category sequence' , readonly=True, index=True)
    layout_category_id = fields.Many2one('sale.layout.category', string='layout category',readonly=True, index=True)
    purchase_line_id =fields.Many2one('purchase.order', string='layout category',readonly=True, index=True)
    asset_category_id =fields.Many2one('account.asset.category', string='asset category',readonly=True, index=True)
    asset_end_date = fields.Date('asset end date', readonly=True, index=True)
    asset_start_date =fields.Date('asset end date', readonly=True, index=True)
    asset_mrr =fields.Float(string='asset', readonly=True, index=True)
    serie = fields.Char('serie',  readonly=True, index=True)

    @api.model_cr
    def init(self):
        drop_view_if_exists(self._cr, 'account_invoice_line_sindescuento')
        self._cr.execute("""
            create or replace view account_invoice_line_sindescuento as (
             SELECT account_invoice_line.id, account_invoice_line.origin, 
                account_invoice_line.create_date, account_invoice_line.price_unit, 
                account_invoice_line.price_subtotal, account_invoice_line.write_uid, 
                account_invoice_line.currency_id, account_invoice_line.uom_id, 
                account_invoice_line.partner_id, account_invoice_line.create_uid, 
                
                account_invoice_line.sequence, account_invoice_line.company_id, 
                account_invoice_line.account_analytic_id, account_invoice_line.account_id, 
                account_invoice_line.discount, account_invoice_line.write_date, 
                account_invoice_line.price_subtotal_signed, account_invoice_line.name, 
                account_invoice_line.product_id, account_invoice_line.invoice_id, 
                account_invoice_line.quantity, 
                account_invoice_line.layout_category_sequence, 
                account_invoice_line.layout_category_id, 
                account_invoice_line.purchase_line_id, 
                account_invoice_line.asset_category_id, account_invoice_line.asset_end_date, 
                account_invoice_line.asset_start_date, account_invoice_line.asset_mrr, 
                account_invoice_line.serie
               FROM account_invoice_line
              WHERE account_invoice_line.product_id <> 19880
            )""")

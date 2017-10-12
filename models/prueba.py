from odoo.addons.report_xls.report.report_xls import ReportXls

class PartnerXls(ReportXls):

    def generate_xlsx_report(self, workbook, data, partners):
        for obj in partners:
            report_name = obj.name
            # One sheet by partner
            sheet = workbook.add_worksheet(report_name[:31])
            bold = workbook.add_format({'bold': True})
            sheet.write(0, 0, obj.name, bold)


PartnerXls('report.res.partner.xls',
            'res.partner')

for line in self:
    if line.state not in ('sale', 'done'):
        line.invoice_status = 'no'
    elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
        if line.name.find('Descuento') <> -1 and line.qty_invoiced > line.product_uom_qty:
            line.invoice_status = 'invoiced'
        else:
            line.invoice_status = 'to invoice'
    elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and \
                    float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
        line.invoice_status = 'upselling'
    elif float_compare(line.qty_invoiced, line.product_uom_qty,
                       precision_digits=precision) >= 0 or line.qty_invoiced > line.product_uom_qty:
        line.invoice_status = 'invoiced'
    elif line.name.find('Descuento') <> -1 and line.qty_invoiced > line.product_uom_qty:
        line.invoice_status = 'invoiced'
    else:
        line.invoice_status = 'no'

## -*- coding: utf-8 -*-

from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import shutil
import logging
import time
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        is_desc =False
        desc_tipo=""
        porcentaje=0.00
        monto=0.00
        fijo=0.00
        amount=0.00
        valor=len(self)
        apa=False
        apa2 = False
        count=0
        if valor ==1:
            for order in self:
                group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
                if order.partner_id.global_discount is True:
                    desc_tipo=order.partner_id.discount_type
                    porcentaje =order.partner_id.discount_percentage
                    fijo= order.partner_id.discount_amount
                    is_desc=True
                naye=order.order_line.sorted(key=lambda l: l.qty_delivered, reverse=True)
                for line in order.order_line.sorted(key=lambda l: l.qty_delivered, reverse=True):
                    valorif=float_is_zero(line.qty_to_invoice, precision_digits=precision)
                    if line.name.find('Descuento')<>-1 and monto <>0.00:
                        isdescuento=True
                    elif float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        continue
                    elif line.name.find('Descuento')<>-1 and monto == 0.00:
                        continue
                    if group_key not in invoices:
                        inv_data = order._prepare_invoice()
                        invoice = inv_obj.create(inv_data)
                        references[invoice] = order
                        invoices[group_key] = invoice
                    elif group_key in invoices:
                        vals = {}
                        if order.name not in invoices[group_key].origin.split(', '):
                            vals['origin'] = invoices[group_key].origin + ', ' + order.name
                        if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(
                                ', ') and order.client_order_ref != invoices[group_key].name:
                            vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                        invoices[group_key].write(vals)
                    if line.name.find('Descuento')==-1:
                        subtotal=0.0
                        line_discount = line.discount
                        if line.discount == 0.00 or False:
                            subtotal = (line.qty_to_invoice * line.price_unit)
                        else:
                            discount = line.discount/100
                            total = (line.qty_to_invoice * line.price_unit)
                            precio = total * discount
                            subtotal =  total- precio
                        monto = monto+ subtotal
                        if line.qty_to_invoice > 0:
                            line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                        elif line.qty_to_invoice < 0 and final:
                            line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                    elif is_desc==True:
                        if desc_tipo == 'fixed':
                            amount = fijo
                        elif desc_tipo == 'percentage':
                            amount = (monto * porcentaje)/100
                        line.invoice_line_create2(invoices[group_key].id, 1,amount)


                if references.get(invoices.get(group_key)):
                    if order not in references[invoices[group_key]]:
                        references[invoice] = references[invoice] | order
        elif valor >1:
            for order in self:
                count+=1
                group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
                v= group_key[1]
                if order.partner_id.global_discount is True:
                    desc_tipo = order.partner_id.discount_type
                    porcentaje = order.partner_id.discount_percentage
                    fijo = order.partner_id.discount_amount
                    is_desc = True
                for line in order.order_line.sorted(key=lambda l: l.qty_delivered, reverse=True):
                    if line.name.find('Descuento')<>-1 and monto <>0.00:
                        isdescuento=True
                    elif float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        continue
                    elif line.name.find('Descuento')<>-1 and monto == 0.00:
                        continue
                    if group_key not in invoices:
                        inv_data = order._prepare_invoice()
                        invoice = inv_obj.create(inv_data)
                        references[invoice] = order
                        invoices[group_key] = invoice
                        monto=0.00
                    elif group_key in invoices:
                        vals = {}
                        if order.name not in invoices[group_key].origin.split(', '):
                            vals['origin'] = invoices[group_key].origin + ', ' + order.name
                        if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(
                                ', ') and order.client_order_ref != invoices[group_key].name:
                            vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                        invoices[group_key].write(vals)
                    if line.name.find('Descuento') == -1:
                        subtotal = 0.0
                        line_discount = line.discount
                        if line.discount == 0.00 or False:
                            subtotal = (line.qty_to_invoice * line.price_unit)
                        else:
                            discount = line.discount / 100
                            total = (line.qty_to_invoice * line.price_unit)
                            precio = total * discount
                            subtotal = total - precio
                        monto = monto + subtotal
                        if line.qty_to_invoice > 0:
                            line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                        elif line.qty_to_invoice < 0 and final:
                            line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                    elif is_desc == True and valor==count:
                        if references.get(invoices.get(group_key)):
                            if order not in references[invoices[group_key]]:
                                if desc_tipo == 'fixed':
                                    amount = fijo
                                elif desc_tipo == 'percentage':
                                    amount = (monto * porcentaje) / 100
                                line.invoice_line_create2(invoices[group_key].id, 1, amount)

                if references.get(invoices.get(group_key)):
                    if order not in references[invoices[group_key]]:
                        references[invoice] = references[invoice] | order
                        group_key=None

        if not invoices:
            raise UserError(_('There is no invoicable line.'))

        for invoice in invoices.values():
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_untaxed < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            invoice.message_post_with_view('mail.message_origin_link',
                                           values={'self': invoice, 'origin': references[invoice]},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    @api.multi
    def _prepare_invoice_line2(self, qty,amount):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {}
        account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(
                _('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': -amount,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.project_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res

    @api.multi
    def invoice_line_create2(self, invoice_id, qty, amount):
        """
        Create an invoice line. The quantity to invoice can be positive (invoice) or negative
        (refund).

        :param invoice_id: integer
        :param qty: float quantity to invoice
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line2(qty=qty,amount=amount)
                vals.update({'invoice_id': invoice_id, 'sale_line_ids': [(6, 0, [line.id])]})
                self.env['account.invoice.line'].create(vals)

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_get_to_invoice_qty()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            order = line.order_id
            cont = 0
            _logger.info(_("hola entre a compute estutus"))
            product_id = self.env.user.company_id.sale_discount_product_id
            if line.qty_delivered > 0:
                _logger.info(_("entro al if compute estutus"))
                discount_line = self.env['sale.order.line'].search(
                    [('order_id', '=', order.id), ('product_id', '=', product_id.id)])
                _logger.info(_("estutus %s")%(discount_line))
                vals = {
                    'invoice_status':'invoiced',
                    'qty_delivered': 1,
                    'qty_invoiced': 1,
                    'qty_to_invoice': 0
                }
                discount_line.write({'qty_delivered': 1})
                discount_line.write({'qty_invoiced': 1})
                discount_line.write({'qty_to_invoice': 0})
                discount_line.write({'invoice_status': 'invoiced'})
            orderlines = self.env['sale.order.line'].search(
                [('order_id', '=', order.id), ('product_id', '!=', product_id.id)])
            for l in orderlines:
                if l.product_uom_qty == l.qty_delivered and l.product_uom_qty == l.qty_invoiced:
                    cont += 1
            if len(orderlines) == cont:
                linediscount = self.env['sale.order.line'].search(
                    [('order_id', '=', order.id), ('product_id', '=', product_id.id)])
                if len(linediscount) == 1:
                    linediscount.write({'qty_delivered': 1})
                    linediscount.write({'qty_invoiced': 1})
                    linediscount.write({'qty_to_invoice': 0})
            if line.state not in ('sale', 'done'):
                line.invoice_status = 'no'
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and\
                    float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

## -*- coding: utf-8 -*-

from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import shutil
import logging
import time
import amount_to_text_es_MX
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    #@api.depends('order_line.price_total')
    #def _amount_all(self):

        #for order in self:
        #   amount_untaxed = amount_tax = 0.0
        #    for line in order.order_line:
        #        amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
        #        if order.company_id.tax_calculation_rounding_method == 'round_globally':
        #            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        #            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
        #                                            product=line.product_id, partner=order.partner_shipping_id)
        #            amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
        #        else:
        #            amount_tax += line.price_tax

        #    amount= suma= descuento = total= 0.0
        #    if order.discount_type == 'fixed':
        #        descuento = order.discount_amount
        #    if order.discount_type == 'percentage':
        #        suma = amount_untaxed
        #        descuento = (suma * order.discount_percentage) / 100
        #        total = suma - descuento
        #        amount = total+amount_tax
        #    order.update({
        #        'suma': suma,
        #        'discount_rate':descuento,
        #        'amount_untaxed': order.pricelist_id.currency_id.round(total),
        #        'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
        #        'amount_total': amount,
        #    })

    @api.multi
    def create_discount(self):
        Line = self.env['sale.order.line']
        product_id = self.env.user.company_id.sale_discount_product_id
        if not product_id:
            raise UserError(_('Please set Sale Discount product in General Settings first.'))

        # Remove Discount line first
        self._discount_unset()
        #raise UserError(_("valor de self \n\n \n%s") % (self))
        for order in self:
            amount = 0
            if order.discount_type == 'fixed':
                amount = order.discount_amount
            if order.discount_type == 'percentage':
                amount = (order.suma * order.discount_percentage)/100
            order.write ({ 'discount_rate': -amount})
            self.discount_rate = -amount
            #Create the Sale line
            #Line.create({
            #    'name': product_id.name,
            #    'price_unit': -amount,
            #    'quantity': 1.0,
            #    'discount': 0.0,
            #    'product_uom': product_id.uom_id.id,
            #    'product_id': product_id.id,
            #    'order_id': order.id,
            #    'sequence': 100,
            #})
        return True


    
    #@api.model
    #def create(self,vals):
        #partner = vals['partner_id']
        #if partner <> 1:
            #isdiscount =False or vals['global_discount']
            #order_line = vals['order_line']
            #pay = vals['payment_term_id']
            #total = 0
            #new_id = super(SaleOrder,self).create(vals)
            #if isdiscount == True:
                #Line = self.env['sale.order.line']
                #product_id = self.env.user.company_id.sale_discount_product_id
                #_logger.info(_("valor del producto:  \n\n \n%s") % (product_id))
                #if not product_id:
                #    raise UserError(_('Please set Sale Discount product in General Settings first.'))
                #self._discount_unset()
                #orderid =self.browse( new_id)
                #order =int(str(orderid.id.id))

                #if discount_type == 'fixed':
                #    amount = discount_amount
                #if discount_type == 'percentage':
                #    amount = (suma * discount_percentage)/100
                #vals['discount_rate']=-amount
                #Line.create({
                #    'name': product_id.name,
                #    'price_unit': 0,
                #    'quantity': 1.0,
                #    'discount': 0.0,
                #    'product_uom': product_id.uom_id.id,
                #    'product_id': product_id.id,
                #    'order_id': order,
                #    'qty_delivered': 0,
                #    'sequence': 100,
                #})
            #raise UserError(_('HOLLA ENTRO 333S.'))
        #else:
            #new_id = super(SaleOrder, self).create(vals)
        #return new_id

    #@api.onchange('order_line')
    #def _onchange_orderline(self):
    #    if self.order_line:
    #        x = 0
    #        cont = len(self.order_line.filtered(lambda r: r.is_discount == True))
    #        vl = cont == 0 and abs(self.discount_rate) > 0
    #        if cont == 0 and abs(self.discount_rate) > 0:
    #            self.write({'discount_rate': 0})
class SaleOrderLines(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def _onchange_orderline(self):
        if self.order_id.discount_type == 'fixed':
            self.discount = self.order_id.discount_amount
        if self.order_id.discount_type == 'percentage':
            self.discount= self.order_id.discount_percentage
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
        
            #Create the Sale line
            Line.create({
                'name': product_id.name,
                'price_unit': -amount,
                'quantity': 1.0,
                'discount': 0.0,
                'product_uom': product_id.uom_id.id,
                'product_id': product_id.id,
                'order_id': order.id,
                'sequence': 100,
            })
        return True
    
    @api.model
    def create(self,vals):
        partner = vals['partner_id']
        if partner <> 1:
            isdiscount =False or vals['global_discount']
            order_line = vals['order_line']
            pay = vals['payment_term_id']
            total = 0
            new_id = super(SaleOrder,self).create(vals)
            if isdiscount == True:
                _logger.info(_('HOLLA ENTRO.'))
                Line = self.env['sale.order.line']
                product_id = self.env.user.company_id.sale_discount_product_id
                _logger.info(_("valor del producto:  \n\n \n%s") % (product_id))
                if not product_id:
                    raise UserError(_('Please set Sale Discount product in General Settings first.'))
                self._discount_unset()
                orderid =self.browse( new_id)
                order =int(str(orderid.id.id))

                #if discount_type == 'fixed':
                #    amount = discount_amount
                #if discount_type == 'percentage':
                #    amount = (suma * discount_percentage)/100
                #vals['discount_rate']=-amount
                Line.create({
                    'name': product_id.name,
                    'price_unit': 0,
                    'quantity': 1.0,
                    'discount': 0.0,
                    'product_uom': product_id.uom_id.id,
                    'product_id': product_id.id,
                    'order_id': order,
                    'sequence': 100,
                })
            #raise UserError(_('HOLLA ENTRO 333S.'))
        else:
            new_id = super(SaleOrder, self).create(vals)
        return new_id

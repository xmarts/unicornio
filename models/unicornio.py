## -*- coding: utf-8 -*-

from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, date, time,timedelta
from odoo.tools import float_is_zero, float_compare
from dateutil.relativedelta import relativedelta
import shutil
import logging
import time
import amount_to_text_es_MX
import threading
_logger = logging.getLogger(__name__)
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale',
    'in_refund': 'purchase',
}

class Unicornio_categorylistprice(models.Model):
    _name = 'res.partnerprice.lines'
    reslines_id = fields.Many2one('res.partner.lines')
    pricelist_id= fields.Many2one('product.pricelist', string="Lista de Precio",  required=True)
    utility= fields.Float(string="Porcentaje de Utilidad", required=True )

class Unicornioproduct_fields(models.Model):

    _inherit = 'product.template'
    ubication_id= fields.Many2one('stock.location', string="Ubicación")
    ubicationinfo_id= fields.Many2one('stock.location.informative', string="Ubicación")
    pediment = fields.Boolean(string='Controla no. pedimento', default=False)
    clasification = fields.Selection(selection=[('product_linea', 'Producto en línea'),('pedido', 'Sobre pedido'),('descontinuado','Descontinuado o linea baja de rotación')], string="Clasificación")
    @api.model
    def create(self,vals):
        new_id =super(Unicornioproduct_fields,self).create(vals)
        if 'default_code' in vals:
            name = vals['default_code']
            product =self.browse( new_id)
            po =int(str(product.id.id))
            #_logger.info(_("entrooooooooooo  \n\n \n%s") % (po))
            line_obj = self.env['quotation.price.line']
            lines = line_obj.search([('linea', '=',name)])
            if len(lines)==1:
                #_logger.info(_("entrooooooooooo  al ifff \n\n \n%s") % (lines))
                list_obj = self.env['quotation.pricelist.line']
                lista = list_obj.search([('quotationprice_id', '=',lines.id)])
                pricelist_obj = self.env['product.pricelist.item']
                for l in lista:
                    #_logger.info(_("entrooooooooooo a for a crear \n\n %s\n") % (l.pricelist_id.id))
                    pricelist_obj.create({
                        'pricelist_id':l.pricelist_id.id,
                        'applied_on': '1_product',
                        'compute_price': 'fixed',
                        'fixed_price': l.totals,
                        'product_tmpl_id':po ,
                    })
            if len(lines)> 1:
                raise UserError(_('Este producto  esta cotizando en más de un registro, especifique el adecuado.'))
        return new_id
    @api.one
    @api.constrains('default_code')
    def condiciones(self):
        product_obj = self.env['product.template']
        if self.default_code is not False:
            product = product_obj.search([('default_code', '=',self.default_code),('id', '!=',self.id)])
            #_logger.info(_("entrooooooooooo id \n\n p%sp  \n") %  (self.id))
            #_logger.info(_("entrooooooooooo code \n\n p%sp  \n") %  (self.default_code))
            if self.default_code is not u'':
                if len(product) <> 0:
                    raise UserError(_('El Campo Referencia Interna Existe en otro producto'))

class Unicorniosales_fields(models.Model):

    _inherit = 'sale.order'
    delivery= fields.Selection([('foraneo', 'Foraneo'), ('mostrador', 'Mostrador'),('local', 'Local'),('cliente', 'Cliente pasa')], string='Tipo Entrega')
    delivered = fields.Boolean(string='Entregado', default=False)
    sequence=fields.Char('sufijo', compute="_compute_sequence")
    nopurchase= fields.Char('No. Orden Compra')
    days =fields.Char('dias',compute="_compute_days")
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    
    @api.one
    def _compute_sequence(self):
        self.sequence=self.name[2:]
    @api.one
    def _compute_days(self):
        #_logger.info(_("RESTAAAA DE FECHAS: \n\n \n%s") % (str(self.validity_date)))
        if str(self.validity_date)<> 'False':
            #_logger.info(_("entrooooooooooo  \n\n \n%s") % (str(self.validity_date)))
            fecha= str(self.validity_date) + ' 00:00:00'
            fecha_caducidad=datetime.strptime(fecha,'%Y-%m-%d %H:%M:%S' ).date()
            fecha_orden = datetime.strptime(str(self.date_order),'%Y-%m-%d %H:%M:%S' ).date()
            total= fecha_caducidad-fecha_orden
            #_logger.info(_("RESTAAAA DE FECHAS: \n\n \n%s") % (total.days))
            self.days=total.days

    # @api.onchange('partner_id')
    # def deliveredpartner_onchange(self):
    #     self.delivery=self.partner_id.delivery

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            #'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'sale_order_ids':self.id,
            'delivery_id':self.delivery,
            'pay_method_ids': [(6, 0, [int(x) for x in self.pay_method_id])],
            'name': self.nopurchase,
            'acc_payment' :self.acc_payment.id,
            'delivered':self.delivered


        }
        return invoice_vals

class Unicornioaccount_fields(models.Model):

    _inherit = 'account.invoice'
   ## @api.one
    #def _compute_delivery(self):
     #   sale_obj = self.env['sale.order']
      #  idsale = sale_obj.search([('name', '=', self.origin)])
       # _logger.info(_("ID de venta: \n%d") % (idsale))
        #self.delivery_id=idsale.delivery
    #delivery_id= fields.Selection([('foraneo', 'Foraneo'), ('mostrador', 'Mostrador'),('local', 'Local'),('cliente', 'Cliente pasa')], string='Tipo Entrega',compute='_compute_delivery')
    #@api.one
    #def _compute_deliveryed(self):
    #    sale_obj = self.env['sale.order']
    #    idsale = sale_obj.search([('name', '=', self.origin)])
    #    _logger.info(_("ID de venta: \n%d") % (idsale))
    #    self.delivered=idsale.delivered
    #delivered = fields.Boolean(string='Entregado' ,compute='_compute_deliveryed')"""
    delivery_id= fields.Selection([('foraneo', 'Foraneo'), ('mostrador', 'Mostrador'),('local', 'Local'),('cliente', 'Cliente pasa')], string='Tipo Entrega')
    delivered = fields.Boolean(string='Entregado', default=False)
    sale_order_ids=fields.Many2one('sale.order',  'Sale Orders')

    @api.model
    def create(self, vals):
        origin = vals['origin']
        if origin is not False:
            if origin.find('SO') <> -1:
                order=self.env['sale.order'].search([('name','=',origin)])
                #raise UserError(_("ENTROOOO %s") % (order.company_id.id))
                company = order.company_id
                currency = order.currency_id
                journal_obj = self.env['account.journal']
                journal_id = journal_obj.search([('company_id', '=', company.id), ('currency_id', '=', currency.id)])
                for journal in journal_id:
                    #_logger.info(_("ID  de journal \n%s\n\n\n") % (journal.type))
                    if journal.name.find('Factura') <> -1 and journal.type == 'sale':
                        vals['journal_id'] = journal.id
                        #_logger.info(_("journal entro al if \n\n%s\n\n\n") % (journal.name))
                        # raise UserError(_("ENTROOOO")%(journal.name))
        return super(Unicornioaccount_fields, self).create(vals)


class Unicornio_Route(models.Model):
	_name = 'route' 
	name=fields.Char('Nombre', required=True) 
	notes=fields.Text('Notas')  

class Unicornio_Saleroute(models.Model):
    _name = 'sale.route'
    date_order = fields.Datetime('fecha', index=True, copy=False, default=fields.Datetime.now,\
        help="fecha de creación de Cotización de Precio")
    name=fields.Char('Entrega', required=True,index=True, copy=False, default='New',readonly=True)
    notes = fields.Text('Observaciones')
    employee_id = fields.Many2one('hr.employee', string="Reṕartidor", required=True)
    route_id=fields.Many2one('route',string="Ruta", required=True)
    delivery= fields.Selection([('foraneo', 'Foraneo'), ('mostrador', 'Mostrador'),('local', 'Local'),('cliente', 'Cliente pasa')], string='Tipo Entrega', required=True)
    line_ids = fields.One2many('sale.route.line','routeline_id')
    generate=fields.Boolean(string='Generado', readonly=True, default=False)

    @api.model
    def create(self,vals):
    	if vals.get('name','New')=='New':
    		_logger.info('ERntroooooo ')
    		vals['name']=self.env['ir.sequence'].next_by_code('sale.route') or 'New'
    	return super(Unicornio_Saleroute,self).create(vals)
    @api.one
    def generate_route(self):
    	_logger.info("entro al boton")
    	invoice_obj = self.env['account.invoice']
        invoices = []
        ruta = self
        routes =invoice_obj.search([('delivery_id', '=', ruta.delivery), 
                                              ('delivered', '=', False)])
        #raise UserError(_("Error:Hay:  \n%s!") % (routes))
        count = 0
        for route in routes:
            if route.currency_id.name == 'MXN' and  route.amount_total > 1000 or route.currency_id.name =='USD' and route.amount_total > 100:
            	if count==0:
            		count=1
            	else:
            		count=count+1

            	lines_obj = self.env['sale.route.line']
            	#raise UserError(_("Error:Hay \n%s!") % (time.strftime("%xd/%m/%Y")))
            	#self.write({'xls_file_signed_index' : adjuntos.store_fname})
            	lines_vals ={
            		'priority': count,
            		'invoice_id': route.id,
                    'partner_id': route.partner_id.id,
            		#'date_delivery': str(time.strftime("%d/%m/%Y")),
            		'delivered': route.delivered,
            		'routeline_id': ruta.id,
            	}
            	lines_create_id = lines_obj.create(lines_vals)
            	self.write({'generate' : True})
            

class Unicornio_Salerouteline(models.Model):
    _name = 'sale.route.line'
    priority = fields.Integer(string="Prioridad", required=True)
    invoice_id =fields.Many2one('account.invoice',string='No. Factura', required=True)
    partner_id  =fields.Many2one('res.partner',string='Cliente', required=True)
    date_delivery=fields.Date(string='Fecha Entrega', default=fields.Date.today())
    delivered = fields.Boolean(string='Entregado')
    notes =fields.Text('Observación')
    routeline_id = fields.Many2one('sale.route')


    @api.onchange('delivered')
    def delivered_onchange(self):
  		if self.delivered == True:
  			invoice_obj = self.env['account.invoice']
  			invoiceid = invoice_obj.search([('id', '=', self.invoice_id.id)])
			#_logger.info(_("ID de venta: \n%d") % (invoiceid))
			#partner_obj = self.pool.get ( 'res.partner') 
			invoiceid.write ({ 'delivered': True})
			sale_obj = self.env['sale.order']
			idsale = sale_obj.search([('name', '=', invoiceid.origin)])
			#_logger.info(_("ID de venta: \n%d") % (idsale))
			idsale.write ({ 'delivered': True})

class Unicornio_SaleOrder(models.Model):
    _inherit = 'sale.order'
    discount_rate= fields.Float('Descuento')
    suma = fields.Float('Suma', compute='_compute_suma')
    date_delivery = fields.Datetime('Fecha de Entrega', index=True, copy=False, default=fields.Datetime.now,\
        help="Tiempo de Entrega Asignada por Partida")
    @api.multi
    def _default_date(self):
        dias = timedelta(days=3)
        #_logger.info(_(" ENTRO AL IF UBICACIOOOON : %s") % (self.date_order))
        #fecha_orden = datetime.strptime(str(self.date_order),'%m/%d/%Y %H:%M:%S.%f' )
        fecha_orden = datetime.now()
        fecha_fin = fecha_orden +  dias
        #_logger.info(_(" ENTRO AL IF UBICACIOOOON : %s") % (fecha_fin.date))
        validity_date = fecha_fin.date()
        return validity_date

    validity_date = fields.Date(string='Expiration Date', readonly=True, default=_default_date, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Manually set the expiration date of your quotation (offer), or it will set the date automatically based on the template if online quotation is installed.")
    description = fields.Text('Descripción')

    @api.one
    def _compute_suma(self):
        sale_obj = self.env['sale.order.line']
        sale = sale_obj.search([('order_id', '=', self.id)])
        total = 0
        apa = False
        for sales in sale:
            #_logger.info(_(" ENTRO AL mi funcion suma : %s") % (sales.name.find('Descuento')))
            if sales.name.find('Descuento')==  -1:
                #total = sales.price_unit * sales.product_qty
                total=total+ sales.price_subtotal
        #_logger.info(_(" ENTRO AL mi funcion suma : %s") % (total))
        self.suma = total
        for order in self:
            amount = 0
            if order.discount_type == 'fixed':
                amount = order.discount_amount
            if order.discount_type == 'percentage':
                amount = (order.suma * order.discount_percentage)/100
            order.write ({ 'discount_rate': -amount})
            product_id = self.env.user.company_id.sale_discount_product_id
            line = sale_obj.search([('order_id', '=', self.id),('product_id','=',product_id.id)])
            line.write ({'price_unit': -amount})
        


    amount_to_text  = fields.Char(compute='_get_amount_to_text', string='Monto en Texto', readonly=True,
                                help='Amount of the invoice in letter')

    @api.one
    @api.depends('amount_total','pricelist_id')
    def _get_amount_to_text(self):
        #_logger.info(_("ENNTRO a monto texto "))
        self.amount_to_text = amount_to_text_es_MX.get_amount_to_text(self, self.amount_total, self.pricelist_id.currency_id.name)

class StockPackOperation(models.Model):
    _inherit='stock.pack.operation'
    @api.one
    def _compute_qtystock(self):
        self.qty_stock= self.product_id.qty_available
    qty_stock  = fields.Integer('Cantidad Almacenada', compute="_compute_qtystock")
    #@api.one
    #def _compute_location_description(self):
     #   self.from_loc = '%s%s' % (self.location_id.name, self.product_id and self.package_id.name or '')
      #  picking_obj = self.env['stock.picking']
      #  picking = picking_obj.search([('id', '=', self.picking_id.id)])
      #  if picking.origin[0:2].upper() <> 'SO':
      #      self.to_loc =  '%s%s' % (self.product_id.ubication_id.name,self.result_package_id.name or '')
      #      _logger.info(_(" ENTRO AL IF UBICACIOOOON : %s") % (self.product_id.ubication_id.name))
      #  else:
      #      self.to_loc = '%s%s' % (self.location_dest_id.name, self.result_package_id.name or '')
      #      _logger.info(_("ENTRO A ELSE UBICACIOOOON "))
        #self.to_loc = '%s%s' % (self.location_dest_id.name, self.result_package_id.name or '')
    #@api.model
    #def create(self,vals):
    #    picking_id=vals['picking_id']
    #    product_id=vals['product_id']
    #    _logger.info(_(" PICKING ID: %s") % (picking_id))
    #    picking_obj = self.env['stock.picking']
    #    picking = picking_obj.search([('id', '=',picking_id)])
    #    if picking.origin[0:2].upper() <> 'SO':
    #        _logger.info('ERntro a COMPRA')
    #        product_obj = self.env['product.template']
    #        product = product_obj.search([('id', '=',product_id)])
    #        vals['location_dest_id']=product.ubication_id.id
    #    return super(StockPackOperation,self).create(vals)
class Unicornio_Salerouteline(models.Model):
    _name = 'stock.location.informative'
    name=fields.Char('Nombre', required=True)
    posx=fields.Integer('Pasillo (X)')
    posy=fields.Integer('Estantería (Y)')
    posz=fields.Integer('Altura (Z)')


class Unicornio_Salerouteline(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def do_new_transfer(self):
        for pick in self:
            #raise UserError(_('entro'))
            pack_operations_delete = self.env['stock.pack.operation']
            if not pick.move_lines and not pick.pack_operation_ids:
                raise UserError(_('Please create some Initial Demand or Mark as Todo and create some Operations. '))
            for pack in pick.pack_operation_ids:
                #_logger.info(_("ENTOOOOOOOOOO al foor  y valor de packaged_id es: %s \n\n") % ( self.name.find('IN')))
                #raise UserError(_("Error:\n valor de name %s ") % (self.name[0:5]))self.name[0:5]=='WH/IN':
                if pack.product_id.pediment == True and pack.qty_done >0  and pack.result_package_id.id is False and  self.name.find('IN') is not -1:
                    raise UserError(_("Error:\n El producto %s controla pedimentos, pero aun no se ha asociado uno.") % (pack.product_id.name))
            # In draft or with no pack operations edited yet, ask if we can just do everything
            if pick.state == 'draft' or all([x.qty_done == 0.0 for x in pick.pack_operation_ids]):
                # If no lots when needed, raise error
                picking_type = pick.picking_type_id
                if (picking_type.use_create_lots or picking_type.use_existing_lots):
                    for pack in pick.pack_operation_ids:
                        if pack.product_id and pack.product_id.tracking != 'none':
                            raise UserError(_('Some products require lots/serial numbers, so you need to specify those first!'))
                view = self.env.ref('stock.view_immediate_transfer')
                wiz = self.env['stock.immediate.transfer'].create({'pick_id': pick.id})
                # TDE FIXME: a return in a loop, what a good idea. Really.
                return {
                    'name': _('Immediate Transfer?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.immediate.transfer',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }

            # Check backorder should check for other barcodes
            if pick.check_backorder():
                view = self.env.ref('stock.view_backorder_confirmation')
                wiz = self.env['stock.backorder.confirmation'].create({'pick_id': pick.id})
                # TDE FIXME: same reamrk as above actually
                return {
                    'name': _('Create Backorder?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.backorder.confirmation',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }
            for operation in pick.pack_operation_ids:
                if operation.qty_done < 0:
                    raise UserError(_('No negative quantities allowed'))
                if operation.qty_done > 0:
                    operation.write({'product_qty': operation.qty_done})
                else:
                    pack_operations_delete |= operation
            if pack_operations_delete:
                pack_operations_delete.unlink()
        self.do_transfer()
        return

class AccountInvoice_fields(models.Model):

    _inherit = 'account.invoice'
    cambio = fields.Float(string='Tipo de Cambio', required=False,  help='Tipo de cambio especifico para los pagos', digits=(12, 4))
    discount_rate= fields.Float(string='Descuento', compute="_compute_discount")
    suma = fields.Float(string='Suma', compute="_compute_suma")
    is_credit = fields.Boolean(string='Es nota de crédito', default=False)

    #@api.model
    #def create(self, vals):
    #    partner = vals['partner_id']
    #    partner_id = self.env['res.partner'].search([('id', '=', partner)])
    #    if partner_id.global_discount==True:
    #        new_id = super(AccountInvoice_fields, self).create(vals)
    #        Line = self.env['account.invoice.line']
    #        product_id = self.env.user.company_id.sale_discount_product_id
    #        _logger.info(_("valor del producto:  \n\n \n%s") % (vals['invoice_lines_ids']))
    #        invoiceid = self.browse(new_id)
    #        invoice = int(str(invoiceid.id.id))
    #        if partner_id.discount_type == 'fixed':
    #            amount = partner_id.discount_amount
    #        if partner_id.discount_type == 'percentage':
    #            amount = (vals['suma'] * partner_id.discount_percentage)/100
    #            Line.create({
    #                'name': product_id.name,
    #                'origin': vals['origin'],
    #                'currency_id': vals['currency_id'],
    #                'price_unit':-amount,
    #                'quantity': 1.0,
    #                'discount': 0.0,
    #                'uom_id': product_id.uom_id.id,
    #                'partner_id': partner_id.id,
    #                'product_id': product_id.id,
    #                'invoice_id': invoice,
    #                'sequence': 100,
    #            })
                # raise UserError(_('HOLLA ENTRO 333S.'))
    #    else:
    #        new_id = super(AccountInvoice_fields, self).create(vals)
    #    return new_id

    @api.onchange('is_credit')
    def _onchange_is_credit(self):
        if self.is_credit== True:
            self.type='out_refund'
    @api.depends('invoice_line_ids')
    @api.one
    def _compute_suma(self):
        total=0
        amount = 0
        is_discount=self.partner_id.global_discount
        discount_type=self.partner_id.discount_type
        discount_amount=self.partner_id.discount_amount
        discount_percentage=self.partner_id.discount_percentage
        for line in self.invoice_line_ids:
            #_logger.info(_(" ENTRO AL mi funcion suma : %s") % (line.name.find('Descuento')))
            if line.name.find('Descuento')==  -1:
                total=total+ line.price_subtotal
        #_logger.info(_(" ENTRO AL mi funcion suma : %s") % (total))
        self.suma = total
        if discount_type == 'fixed' and is_discount==True:
            amount = discount_amount
        if discount_type == 'percentage' and is_discount==True:
            amount = (total * discount_percentage)/100
        #self.write ({ 'discount_rate': -amount})
        product_id = self.env.user.company_id.sale_discount_product_id
        lines = self.invoice_line_ids.search([('invoice_id', '=', self.id),('product_id','=',product_id.id)])
        #lines.write ({'price_unit': -amount})
        #self.button_dummy()

    @api.depends('invoice_line_ids')
    @api.one
    def _compute_discount(self):
        total = 0
        for line in self.invoice_line_ids:
            #_logger.info(_(" ENTRO AL mi funcion descuento : %s") % (line.name.find('Descuento')))
            if line.name.find('Descuento') <> -1:
                total = total + line.price_subtotal
        #_logger.info(_(" ENTRO AL mi funcion descuento : %s") % (total))
        self.discount_rate = total

    @api.one
    @api.depends('invoice_line_ids', 'tax_line_ids.amount','suma','amount_untaxed')
    def _compute_amount(self):
        _logger.info("")
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    @api.multi
    def button_dummy(self):
        self._onchange_invoice_line_ids()
        self._compute_amount()
        self._compute_discount()
        return self

    @api.one
    @api.depends('pay_method_ids')
    def _compute_pay(self):
        #self.pay_method=(x for x in self.pay_method_ids.name.split(','))
        self.pay_method = self.pay_method_ids.name

    pay_method = fields.Char(string="Método de Pago", compute="_compute_pay",store=True,help="Campo para agrupacion de metodo de pago")
    pay = fields.Char(string="Método de Pago", store=True)

    @api.model
    def _default_journal(self):
        #_logger.info(_('entro DEFAULT JOURNALLLLLLLLLLL\n\n\n'))
        if self._context.get('default_journal_id', False):
            #_logger.info(_('entro aqui \n\n\n%s')%(self._context.get('default_journal_id')))
            return self.env['account.journal'].browse(self._context.get('default_journal_id'))
        inv_type = self._context.get('type', 'out_invoice')
        #_logger.info(_('entro DEFAULT JOURNALLLLLLLLLLL\n\n\n'))
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', filter(None, map(TYPE2JOURNAL.get, inv_types))),
            ('company_id', '=', company_id),
        ]
        #_logger.info(_('todo bien :)\n\n\n'))
        if self.is_credit == True:
            domain = []
            domain = [
                ('is_credit', 'in', True),
                ('company_id', '=', company_id)
            ]
        return self.env['account.journal'].search(domain, limit=1)
    journal_id = fields.Many2one('account.journal', string='Journal',default=_default_journal,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 domain="[('type', 'in', {'out_invoice': ['sale'], 'out_refund': ['sale'], 'in_refund': ['purchase'], 'in_invoice': ['purchase']}.get(type, [])), ('company_id', '=', company_id),('currency_id', '=', currency_id)]")

    @api.onchange('currency_id')
    def _onchange_currency_id(self):
        #_logger.info(_('funcion onchange entroooooooooooooooooo\n\n\n'))
        #_logger.info(_('valor de journal\n\n\n%s') % (self._context.get('default_journal_id')))
        #if self._context.get('default_journal_id', False):
        #_logger.info(_('funcion onchange if\n\n\n'))
        inv_type = self._context.get('type', 'out_invoice')
        inv_type2 = self._context.get('type', 'in_refund')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        currency = self.currency_id
        domain = [
            ('type', 'in', filter(None, map(TYPE2JOURNAL.get, inv_types))),
            ('company_id', '=', company_id),
            ('currency_id', '=', currency.id)
        ]
        #_logger.info(_('salio\n\n\n'))
        if self.is_credit == True:
            domain= []
            domain = [
                ('is_credit', 'in', True),
                ('company_id', '=', company_id),
                ('currency_id', '=', currency.id)
            ]
        journal = self.env['account.journal'].search(domain, limit=1)
        self.journal_id=journal.id

    @api.onchange('is_credit')
    def _onchange_iscredit(self):
        if self.is_credit==True:
            #_logger.info(_('funcion onchange entroooooooooooooooooo\n\n\n'))
            #_logger.info(_('valor de journal\n\n\n%s') % (self._context.get('default_journal_id')))
            # if self._context.get('default_journal_id', False):
            # _logger.info(_('funcion onchange if\n\n\n'))
            inv_type = self._context.get('type', 'out_invoice')
            inv_type2 = self._context.get('type', 'in_refund')
            inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
            company_id = self._context.get('company_id', self.env.user.company_id.id)
            currency = self.currency_id
            #_logger.info(_('salio\n\n\n'))
            #if self.type == 'out_refund':
            domain = [
                ('is_credit', '=', True),
                ('company_id', '=', company_id)
            ]
            journal = self.env['account.journal'].search(domain, limit=1)
            #raise UserError(_("entro %s")%(journal))
            self.journal_id = journal.id

class resCurrency(models.Model):
    _inherit = 'res.currency'

    @api.multi
    @api.depends('name')
    def _get_current_rate(self):
        date = self._context.get('date') or fields.Datetime.now()
        company_id = self._context.get('company_id') or self.env.user.company_id.id
        for currency in self:
            self._cr.execute("""SELECT rate, rate2 FROM res_currency_rate 
                                   WHERE currency_id = %s
                                     AND left(name::text, 10) <= %s
                                     AND (company_id is null
                                         OR company_id = %s)
                                ORDER BY name desc, company_id desc LIMIT 1""",
                             (currency.id or 0, date, company_id))
            rec = self._cr.fetchone()
            currency.rate = self._cr.rowcount and rec[0] or 1.0
            currency.rate2 = self._cr.rowcount and rec[1] or 1.0
    rate2   = fields.Float(compute="_get_current_rate", string='Current 1/Rate', digits=(20,4),help='The rate of the currency as 1/rate.')
    rate    = fields.Float(compute="_get_current_rate", string='Current Rate', digits=(22,4),help='The rate of the currency to the currency of rate 1.')
class AccountJournal(models.Model):
    _inherit = 'account.journal'
    name_report = fields.Char('Nombre para el reporte')
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    description = fields.Text('Descripción')

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'    
    is_discount = fields.Boolean(string="Es Descuento", defalut=False, compute="_compute_isdiscount")
    @api.one
    def _compute_isdiscount(self):
        if self.name.find('Descuento') is not -1:
            self.is_discount = True
class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'    
    is_discount = fields.Boolean(string="Es Descuento", defalut=False, compute="_compute_isdiscountin")
    serie = fields.Text(string="No. Serie")
    @api.one
    def _compute_isdiscountin(self):
        if self.name.find('Descuento') is not -1:
            self.is_discount = True

    #@api.model
    #def create(self, vals):
    #    _logger.info(_("entro a crear") )
    #    name = vals['name']
    #    invoice = vals['invoice_id']
    #    _logger.info(_("invoice_id %s") % (invoice))
    #    invoice_id= self.env['account.invoice'].search([('id', '=',invoice)])
    #    partner= invoice_id.partner_id
    #    partner_id= self.env['res.partner'].search([('id','=',partner.id)])
    #    _logger.info(_("npartner_id %s") % (partner_id))
    #    _logger.info(_("name.find('Descuento')t %s") % (name.find('Descuento')))
    #    _logger.info(_("partner_id.isdiscount %s") % (partner_id.global_discount))
    #    if name.find('Descuento') <> -1 and partner_id.global_discount == True:
    #        amount = 0
    #        if partner_id.discount_type == 'fixed':
    #            vals['price_subtotal'] = partner_id.discount_amount
    #        if partner_id.discount_type == 'percentage':
    #            _logger.info(_("(invoice_id.amount_total * partner_id.discount_percentage) / 100 %s") % ((invoice_id.amount_total * partner_id.discount_percentage) / 100))
    #            amount=(invoice_id.amount_total * partner_id.discount_percentage) / 100
    #            vals['price_subtotal'] = -amount
    #        _logger.info(_("valor de amount %s")%(vals['price_subtotal']))
    #    return super(AccountInvoiceLine, self).create(vals)
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    description = fields.Text('Descripción')

class stockMove(models.Model):
    _inherit= 'stock.move'
    @api.one
    def _compute_qtystock(self):
        sSelf = self.sudo()
        self.qty_stock= sSelf.product_id.qty_available
    qty_stock  = fields.Integer('Cantidad Almacenada', compute="_compute_qtystock")
class AccountJournal(models.Model):
    _inherit= 'account.journal'
    is_credit = fields.Boolean(string="Es Nota de Credito", defalut=False)
    type_account = fields.Selection(selection=[('ingreso','Ingreso'), ('egreso','Egreso')], string="Tipo de Diario")











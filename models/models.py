## -*- coding: utf-8 -*-

from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import shutil
import logging
_logger = logging.getLogger(__name__)

class quotationsprice(models.Model):
	_name = "quotation.price"
	name=fields.Char('Cotización', required=True,index=True, copy=False, default='New',readonly=True)
	provider_id=fields.Many2one('res.partner', string="Proveedor",  domain="[('supplier','=',True)]", required=True)
	date_order = fields.Datetime('Fecha', required=True, index=True, copy=False, default=fields.Datetime.now,\
        help="fecha de creación de Cotización de Precio")
	observation=fields.Text('Observación')
	pricelist_id= fields.Many2one('product.pricelist', string="Lista de Precio",  required=True)
	partner_id=fields.Many2one('res.partner', string="Cliente",  domain="[('customer','=',True)]")
	active = fields.Boolean(string='Activo', default=True)
	line_ids = fields.One2many('quotation.price.line','quotation_id')

	@api.model
	def create(self,vals):
		if vals.get('name','New')=='New':
			_logger.info('ERntroooooo ')
			vals['name']=self.env['ir.sequence'].next_by_code('quotation.price') or 'New'
		return super(quotationsprice,self).create(vals)

class quotationspriceline(models.Model):
	_name = "quotation.price.line"
	quotation_id = fields.Many2one('quotation.price')
	linea= fields.Char('Código de Producto')
	categ_id = fields.Many2one('product.category', string="Linea", required=True )
	costo= fields.Float(string="Costo", required=True)
	qty= fields.Integer(string="Cantidad", required=True)
	total= fields.Float(string="Costo Total Vendedor")
	costo_logistic= fields.Float(string="Costo Logistica")
	lineprice_ids = fields.One2many('quotation.pricelist.line','quotationprice_id')
	qty_list= fields.Integer(string="Cantidad" )

	@api.multi
	def action_split_quote(self):
		action_ctx= dict(self.env.context)
		view_id=self.env.ref('unicornio.view_price_quote_form').id
		return {
            'name': _('Lista de Precios'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'quotation.price.line',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': action_ctx
        }
   	split_quote=action_split_quote
   	@api.multi
   	def save(self):
   		#for pack in self:
   		#	pack.write({'qty_list':sum(pack.lineprice_ids.mapped)})
   		return{'type':'ir.action.act_window_close'}

   	@api.onchange('costo','qty')
  	def price_logistic(self):
  		totales= (self.qty * self.costo)
  		self.total = float(totales)
  		#_logger.info(_("Costo total del vendedor : \n%d") % (totales))
  		provider=self.quotation_id.provider_id.id
  		partner_obj=self.env['res.partner']
  		partner = partner_obj.search([('id', '=',provider)])
  		total2=(partner.logistic/100)*totales
  		self.costo_logistic =float(total2)
  			
class quotationspricelistline(models.Model):
	_name = "quotation.pricelist.line"
	quotationprice_id = fields.Many2one('quotation.price.line')
	pricelist_id= fields.Many2one('product.pricelist', string="Lista de Precio",  required=True)
	totals= fields.Float(string="Total", readonly=True )


class Unicornio_categorylines(models.Model):
    _name = 'res.partner.lines'
    categ_id = fields.Many2one('product.category', string="Categoria", required=True )
    partner_id = fields.Many2one('res.partner')
    linepartner_ids = fields.One2many('res.partnerprice.lines','reslines_id')
    
    @api.multi
    def action_split_price(self):
    	action_ctx=dict(self.env.context)
    	view_id=self.env.ref('unicornio.view_price_utility_form').id
    	return{
            'name': _('Lista de Precios'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.partner.lines',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': action_ctx
    	}
    split_price=action_split_price

    @api.multi
    def save(self):
    	return{'type':'ir.action.act_window_close'}

class parterUnicornio_fields(models.Model):

	_inherit = 'res.partner'
    	lines_ids = fields.One2many('res.partner.lines','partner_id','Lines')
    	logistic= fields.Float(string="Costo Logística")
      


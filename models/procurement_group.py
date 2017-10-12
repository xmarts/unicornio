from openerp import fields,models

class pantillas_wni_ro_procurement_group(models.Model):

    _name = 'procurement.group'
    _inherit ='procurement.group'

    sale_order_id = fields.One2many('sale.order','procurement_group_id')

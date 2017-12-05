## -*- coding: utf-8 -*-

from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import shutil
import logging
import time
import amount_to_text_es_MX
_logger = logging.getLogger(__name__)

class AccountINvoice(models.Model):
    _inherit = 'account.invoice'
    invoice_line_withoutdiscount_ids = fields.One2many('account.invoice.line.sindescuento', 'invoice_id', string='Invoice Lines',
                                       readonly=True, states={'draft': [('readonly', False)]}, copy=True)
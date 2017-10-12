## -*- coding: utf-8 -*-

from openerp import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import shutil
import logging
_logger = logging.getLogger(__name__)
class Accountpaymentun(models.Model):
    _inherit ='account.payment'
    def _create_payment_entry(self, amount):
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        invoice_currency = False
        if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
            # if all the invoices selected share the same currency, record the paiement in that currency too
            invoice_currency = self.invoice_ids[0].currency_id
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(
            amount, self.currency_id, self.company_id.currency_id, invoice_currency)
        move = self.env['account.move'].create(self._get_move_vals())
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        _logger.info(_("ENTROO debit: \n%s ") % (debit))
        _logger.info(_("ENTROO credit: \n%s  ") % (credit))
        _logger.info(_("ENTROO  amount_currency: \n%s  ") % (amount_currency))
        _logger.info(_("ENTROO  amount_currency: \n%s  ") % (currency_id))
        _logger.info(_("ENTROO  currency: \n%s  ") % (currency_id))
        _logger.info(_("ENTROO: metodo get_move_vals() \n%s  ") % (self._get_move_vals()))
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
        _logger.info(_("ENTROO: self.invoice_ids\n%s  ") % (self.invoice_ids))
        _logger.info(_("self._get_counterpart_move_line_vals(self.invoice_ids) \n%s  ") % (
        self._get_counterpart_move_line_vals(self.invoice_ids)))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)
        _logger.info(_("counterpart_aml_dict: \n%s  ") % (counterpart_aml_dict))
        if self.payment_difference_handling == 'reconcile' and self.payment_difference:
            _logger.info(_("entro al if \n "))
            writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
            _logger.info(_("self._get_shared_move_line_vals(0, 0, 0, move.id, False): \n%s  ") % (
                self._get_shared_move_line_vals(0, 0, 0, move.id, False)))
            amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(
                self.payment_difference, self.currency_id, self.company_id.currency_id, invoice_currency)[2:]
            _logger.info(_("ENTROO  amount_currency: \n%s  ") % (amount_currency_wo))
            _logger.info(_("ENTROO  currency_id: \n%s  ") % (currency_id))
            total_residual_company_signed = sum(invoice.residual_company_signed for invoice in self.invoice_ids)
            total_payment_company_signed = self.currency_id.with_context(date=self.payment_date).compute(self.amount,
                                                                                                         self.company_id.currency_id)
            _logger.info(_("total_residual_company_signed\n%s  ") % (total_residual_company_signed))
            _logger.info(_("total_payment_company_signed  \n%s  ") % (total_payment_company_signed))
            if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
                amount_wo = total_payment_company_signed - total_residual_company_signed
            else:
                amount_wo = total_residual_company_signed - total_payment_company_signed
            if amount_wo > 0:
                debit_wo = amount_wo
                credit_wo = 0.0
                amount_currency_wo = abs(amount_currency_wo)
            else:
                debit_wo = 0.0
                credit_wo = -amount_wo
                amount_currency_wo = -abs(amount_currency_wo)
            _logger.info(_("debit_wo\n%s  ") % (debit_wo))
            _logger.info(_("credit_wo  \n%s  ") % (credit_wo))
            _logger.info(_("amount_currency_wo \n%s  ") % (amount_currency_wo))
            writeoff_line['name'] = _('Counterpart')
            writeoff_line['account_id'] = self.writeoff_account_id.id
            writeoff_line['debit'] = debit_wo
            writeoff_line['credit'] = credit_wo
            writeoff_line['amount_currency'] = amount_currency_wo
            writeoff_line['currency_id'] = currency_id
            _logger.info(_("writeoff_line\n%s  ") % (writeoff_line))
            writeoff_line = aml_obj.create(writeoff_line)
            if counterpart_aml['debit']:
                counterpart_aml['debit'] += credit_wo - debit_wo
                _logger.info(_("counterpart_aml['debit']\n%s  ") % (counterpart_aml['debit']))
            if counterpart_aml['credit']:
                counterpart_aml['credit'] += debit_wo - credit_wo
                _logger.info(_("counterpart_aml['credit'] \n%s  ") % (counterpart_aml['credit']))
            counterpart_aml['amount_currency'] -= amount_currency_wo

        self.invoice_ids.register_payment(counterpart_aml)
        _logger.info(_("counterpart_aml \n%s  ") % (counterpart_aml))
        if not self.currency_id != self.company_id.currency_id:
            amount_currency = 0
        liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
        liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
        aml_obj.create(liquidity_aml_dict)
        _logger.info(_("liquidity_aml_dict \n%s  ") % (liquidity_aml_dict))
        move.post()
        return move
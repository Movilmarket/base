# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    bolson_id = fields.Many2one("bolson.bolson", string="Liquidacion", readonly=False, states={'paid': [('readonly', True)]}, ondelete='restrict')

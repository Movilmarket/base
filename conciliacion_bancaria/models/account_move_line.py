# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    conciliado_banco = fields.One2many("conciliacion_bancaria.fecha", "move_id", string="Conciliacion Linea")

# Esto tiene que ser un registro aparte y no otra colummna de account.move.line
# para que se pueda conciliar y desconciliar aunque el movimiento ya este validado.
class ConciliacionBancariaLinea(models.Model):
    _name = "conciliacion_bancaria.fecha"
    _description = "Relaciona un apunte contable con la fecha que fue conciliado"

    move_id = fields.Many2one("account.move.line", string="Apunte", required=True)
    fecha = fields.Date(string="Fecha", required=True)

    _sql_constraints = [
        ('move_uniq', 'unique (move_id)', 'Ese apunte ya fue conciliado.')
    ]

# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _

class ConciliacionAutomatica_PendientesExcel(models.Model):
    _name = "conciliacion_bancaria.pendientes_excel"

    fecha = fields.Date(string="Fecha", required=True)
    account_id = fields.Many2one('account.account', string='Cuenta')
    tipo_documento = fields.Char(string="Tipo doc.", required=True)
    numero_documento = fields.Char(string="No. doc.", required=True)
    monto = fields.Float(string='Monto', required=True)

    def _existe_registro(self, numero_documento, account_id):
        registro = self.search([('numero_documento', '=', numero_documento), ('account_id', '=', account_id)])
        if registro:
            return registro[0].id
        return False


    
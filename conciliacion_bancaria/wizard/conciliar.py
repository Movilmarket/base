# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import UserError, ValidationError

class Conciliar(models.TransientModel):
    _name = "conciliacion_bancaria.conciliar"
    _description = "Conciliar con banco"

    fecha = fields.Date(string="Fecha")

    @api.multi
    def conciliar(self):
        for rec in self:
            for line in self.env['account.move.line'].browse(self.env.context.get('active_ids', [])):
                if rec.fecha:
                    self.env['conciliacion_bancaria.fecha'].create({
                        'move_id': line.id,
                        'fecha': rec.fecha
                    })
        return {'type': 'ir.actions.act_window_close'}

    def desconciliar(self):
        for rec in self:
            for line in self.env['account.move.line'].browse(self.env.context.get('active_ids', [])):
                conciliados = self.env['conciliacion_bancaria.fecha'].search([('move_id','=',line.id)])
                conciliados.unlink()
        return {'type': 'ir.actions.act_window_close'}

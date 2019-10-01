# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class DisponibilidadResumenReporte(models.Model):
    _name = "conciliacion_bancaria.disponibilidad_resumen.report"
    _description = "Reporte Disponibilidad Resumen"
    _auto = False

    cuenta_id = fields.Many2one('account.account', string='Cuenta', readonly=True)
    debe_sin_conciliar = fields.Float(string='Créditos en circulación', readonly=True)
    haber_sin_conciliar = fields.Float(string='Débitos en circulación', readonly=True)
    saldo_conciliado = fields.Float(string='Saldo conciliado', readonly=True)
    creditos_no_encontrados = fields.Float(string='Creditos no encontrados', readonly=True)
    debitos_no_encontrados = fields.Float(string='Debitos no encontrados', readonly=True)
    saldo = fields.Float(string='Saldo', readonly=True)
    saldo_banco = fields.Float(string='Saldo banco', readonly=True)
    saldo_disponible = fields.Float(string='Saldo disponible', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'conciliacion_bancaria_disponibilidad_resumen_report')
        self._cr.execute("""
            CREATE OR REPLACE VIEW conciliacion_bancaria_disponibilidad_resumen_report AS (
                select cuenta_id as id,
                    cuenta_id,
                    sum(debe_sin_conciliar) as debe_sin_conciliar,
                    sum(haber_sin_conciliar) as haber_sin_conciliar,
                    sum(saldo_conciliado) as saldo_conciliado,
                    sum(creditos_no_encontrados) as creditos_no_encontrados,
                    sum(abs(debitos_no_encontrados)) as debitos_no_encontrados,
                    sum(saldo_conciliado + debe_sin_conciliar - haber_sin_conciliar) as saldo,
                    sum(saldo_conciliado + creditos_no_encontrados + debitos_no_encontrados) as saldo_banco,
                    sum(saldo_conciliado + debe_sin_conciliar - haber_sin_conciliar + creditos_no_encontrados + debitos_no_encontrados) as saldo_disponible
                from (
                    select l.id as id,
                        l.account_id as cuenta_id,
                        case when f.fecha is null and l.debit > 0 then l.debit else 0 end as debe_sin_conciliar,
                        case when f.fecha is null and l.credit > 0 then l.credit else 0 end as haber_sin_conciliar,
                        case when f.fecha is not null then l.debit - l.credit else 0 end as saldo_conciliado,
                        0 as creditos_no_encontrados,
                        0 as debitos_no_encontrados
                    from account_move_line l left join conciliacion_bancaria_fecha f on (l.id = f.move_id)
                    where account_id in (
                        select id from account_account where internal_type = 'liquidity'
                    )
                    union all
                    select l.id as id,
                        l.account_id as cuenta_id,
                        0 as debe_sin_conciliar,
                        0 as haber_sin_conciliar,
                        0 as saldo_conciliado,
                        case when monto > 0 then monto else 0 end as creditos_no_encontrados,
                        case when monto < 0 then monto else 0 end as debitos_no_encontrados
                        from conciliacion_bancaria_pendientes_excel l
                ) as detalles
                group by cuenta_id
            )
        """)

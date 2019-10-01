# -*- encoding: utf-8 -*-

{
    'name' : 'Conciliación Bancaria',
    'version' : '1.0',
    'category': 'Custom',
    'description': """Manejo de conciliación bancaria""",
    'author': 'Rodrigo Fernandez',
    'website': 'http://solucionesprisma.com/',
    'depends' : [ 'account' ],
    'data' : [
        'views/account_move_line.xml',
        'views/report.xml',
        'views/reporte_banco.xml',
        'views/reporte_disponibilidad_resumen.xml',
        'views/conciliacion_automatica.xml',
        'wizard/conciliar.xml',
        'wizard/conciliacion_automatica.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

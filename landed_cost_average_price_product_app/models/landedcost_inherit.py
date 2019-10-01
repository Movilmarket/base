# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.addons.stock_landed_costs.models import product
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

class Landed_cost_inherit(models.Model):
    
    _inherit = 'stock.landed.cost'

    def get_valuation_lines(self):
        lines = []
        for move in self.mapped('picking_ids').mapped('move_lines'):
            # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
            if move.product_id.valuation != 'real_time' or move.product_id.cost_method not in  ['fifo','average']:
                continue
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': move.product_qty,
                'former_cost': move.value,
                'weight': move.product_id.weight * move.product_qty,
                'volume': move.product_id.volume * move.product_qty
            }
            lines.append(vals)

        if not lines and self.mapped('picking_ids'):
            raise UserError(_("You cannot apply landed costs on the chosen transfer(s). Landed costs can only be applied for products with automated inventory valuation and FIFO costing method."))
        return lines

    @api.multi
    def button_validate(self):
        res = super(Landed_cost_inherit, self).button_validate()
        for cost in self :
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                if line.move_id.picking_id.picking_type_id.code == 'incoming' :
                    cost_to_add = 0
                    code = line.move_id.picking_id.picking_type_id.code
                    stock_move = self.env['stock.move'].search([('product_id','=',line.move_id.product_id.id)])
                    quantity_to_add = 0
                    for stock in stock_move :
                        if stock.picking_id.picking_type_id.code == 'incoming' :
                            quantity_to_add = quantity_to_add + stock.quantity_done
                    if line.quantity > 0 :
                        cost_to_add = cost_to_add + line.additional_landed_cost 
                    if line.product_id.cost_method == 'average'  and not float_is_zero(quantity_to_add, precision_rounding=line.product_id.uom_id.rounding):
                                line.product_id.with_context(force_company=self.company_id.id).sudo().standard_price += cost_to_add/quantity_to_add

        return res
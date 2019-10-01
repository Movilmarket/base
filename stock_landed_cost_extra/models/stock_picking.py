# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class StockPicking(models.Model):
    _inherit = 'stock.picking'
  
    landed_costs_id = fields.Many2one('stock.landed.cost', string='Landed Costs', ondelete='restrict', domain="[('state', '=', 'draft')]")
    landed_costs_ok = fields.Boolean(compute='_get_landed_costs_status')
    
    def _get_landed_costs_status(self):
        self.landed_costs_ok = self.landed_costs_id and self.landed_costs_id.state!='draft'    

    @api.multi
    def write(self, vals):
        process_ok = self.env.context.get('is_origen_lc',True)
        if process_ok:       
            for picking in self:
                if picking.landed_costs_id:            
                    new_landed_costs = []                        
                    if picking.state == 'done' and picking.landed_costs_id:                                                
                        for landed_cost in picking.landed_costs_id.picking_ids:
                            if not (picking.id==landed_cost.id):
                                new_landed_costs.append(landed_cost.id)                    
                        picking.landed_costs_id.picking_ids = [(6, 0, new_landed_costs)]
                        picking.landed_costs_id.compute_landed_cost()
                    message = _("Unlinked the picking order: <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> to this doc") % (picking.id, picking.name)
                    picking.landed_costs_id.message_post(
                        body=message,
                        subject=_("Picking order unlinked"),
                        message_type='comment', 
                    )
        res = super(StockPicking, self).write(vals)
        if process_ok:                
            for picking in self:
                if picking.landed_costs_id:            
                    new_landed_costs = []                        
                    if picking.state == 'done' and picking.landed_costs_id:                                
                        new_landed_costs.append(picking.id)
                        for landed_cost in picking.landed_costs_id.picking_ids:
                            new_landed_costs.append(landed_cost.id)                    
                        picking.landed_costs_id.picking_ids = [(6, 0, new_landed_costs)]
                        picking.landed_costs_id.compute_landed_cost()
                    message = _("Linked the picking order: <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> to this doc") % (picking.id, picking.name)
                    picking.landed_costs_id.message_post(
                        body=message,
                        subject=_("Picking order linked"),
                        message_type='comment', 
                    )                
        return res
  
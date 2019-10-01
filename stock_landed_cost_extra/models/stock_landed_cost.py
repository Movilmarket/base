# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'
        
    @api.multi
    def button_reopen(self):
        if self.state=='cancel':
            return self.write({'state': 'draft'})
            
    @api.multi
    def write(self, values):
        for rec in self:
            old_picking_ids = [x.id for x in rec.picking_ids]
            old_invoice_ids = [x.invoice_id.id for x in rec.cost_lines if x.invoice_id]
            res = super(LandedCost, self).write(values)
               
            new_picking_ids = [x.id for x in rec.picking_ids] 
            del_picking_ids = [x for x in old_picking_ids if x not in new_picking_ids]
            new_picking_ids += old_picking_ids
            for stock_id in new_picking_ids:
                if rec.state=='cancel'  or (stock_id in del_picking_ids):
                    res = False
                else:
                    res = rec.id
                self.env['stock.picking'].with_context(is_origen_lc=False).browse(stock_id).write({'landed_costs_id':res})
            new_invoice_ids = [x.invoice_id.id for x in rec.cost_lines if x.invoice_id]
            del_invoice_ids = [x for x in old_invoice_ids if x not in new_invoice_ids] 
            new_invoice_ids += old_invoice_ids    
            for invoice_id in new_invoice_ids:
                if rec.state=='cancel'  or (invoice_id in del_invoice_ids):
                    res = False
                else:
                    res = rec.id
                self.env['account.invoice'].with_context(is_origen_lc=False).browse(invoice_id).write({'landed_costs_id':res})
            if rec.state=='calcel':
                message = _("Linked documents were released to this doc")
                picking.landed_costs_id.message_post(
                    body=message,
                    subject=_("Landed Cost unlinked"),
                    message_type='comment', 
                )
        return res

class LandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'

    invoice_id = fields.Many2one('account.invoice', 'Invoice')
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
                
    landed_costs_id = fields.Many2one('stock.landed.cost', string='Landed Costs', ondelete='restrict', domain="[('state', '=', 'draft')]")
    landed_costs_ok = fields.Boolean(compute='_get_landed_costs_status')
    
    def _get_landed_costs_status(self):
        self.landed_costs_ok = self.landed_costs_id and self.landed_costs_id.state!='draft'  
        
    @api.multi
    def write(self, values):
        for rec in self:
            if 'landed_costs_id' in values and rec.landed_costs_id:
                if rec.picking_ids:
                    for picking in rec.picking_ids:
                        picking.landed_costs_id = False
                if rec.invoice_ids:
                    for invoice in rec.invoice_ids:
                        invoice.landed_costs_id = False
                message = _("Unlinked the purchase order: <a href=# data-oe-model=purchase.order data-oe-id=%d>%s</a> to this doc") % (rec.id, rec.name)
                rec.landed_costs_id.message_post(
                    body=message,
                    subject="Purchase order unlinked",
                    message_type='comment', 
                )                        
        res = super(PurchaseOrder, self).write(values)
        for rec in self:
            if 'landed_costs_id' in values and rec.landed_costs_id:
                if rec.picking_ids:
                    for picking in rec.picking_ids:
                        picking.landed_costs_id = rec.landed_costs_id.id
                if rec.invoice_ids:
                    for invoice in rec.invoice_ids:
                        if any(ptype == True for ptype in rec.order_line.mapped('product_id.landed_cost_ok')):
                            invoice.landed_costs_id = rec.landed_costs_id.id
                message = _("Linked the purchase order: <a href=# data-oe-model=purchase.order data-oe-id=%d>%s</a> to this doc") % (rec.id, rec.name)
                rec.landed_costs_id.message_post(
                    body=message,
                    subject=_("Purchase order Linked"),
                    message_type='comment', 
                )       
        return res

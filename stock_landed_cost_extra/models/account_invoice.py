# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
                      
    landed_costs_id = fields.Many2one('stock.landed.cost', string='Landed Costs', ondelete='restrict', domain="[('state', '=', 'draft')]")
    landed_costs_ok = fields.Boolean(compute='_get_landed_costs_status')
    
    def _get_landed_costs_status(self):
        self.landed_costs_ok = self.landed_costs_id and self.landed_costs_id.state!='draft'    
    
    @api.multi
    def write(self, vals):
        process_ok = self.env.context.get('is_origen_lc',True)
        if process_ok:
            landed_cost_lines = self.env['stock.landed.cost.lines'] 
            for invoice in self:
                if invoice.landed_costs_id and not (invoice.state in ['draft','cancel']):
                    for landed_line in invoice.landed_costs_id.cost_lines:                                
                        if landed_line.invoice_id.id==invoice.id:
                            landed_line.unlink()
                    invoice.landed_costs_id.compute_landed_cost()
                    message = _("Unlinked the invoice: <a href=# data-oe-model=account.invoice data-oe-id=%d>%s</a> to this doc") % (invoice.id, invoice.number)
                    invoice.landed_costs_id.message_post(
                        body=message,
                        subject=_("Invoice unlinked"),
                        message_type='comment', 
                    )                        
        res = super(AccountInvoice, self).write(vals)
        if process_ok:        
            for invoice in self:
                if invoice.landed_costs_id and not (invoice.state in ['draft','cancel']):
                    for landed_cost in invoice.invoice_line_ids:
                        if landed_cost.product_id.landed_cost_ok:
                            landed_vals = {'product_id':landed_cost.product_id.id,
                                           'name':landed_cost.name,
                                           'account_id':landed_cost.account_id.id,
                                           'price_unit':landed_cost.price_subtotal,
                                           'split_method':landed_cost.product_id.split_method,
                                           'invoice_id':invoice.id,
                                           'cost_id':invoice.landed_costs_id.id}
                            res_id = landed_cost_lines.create(landed_vals)
                    invoice.landed_costs_id.compute_landed_cost()
                    message = _("Linked the invoice: <a href=# data-oe-model=account.invoice data-oe-id=%d>%s</a> to this doc") % (invoice.id, invoice.number)
                    invoice.landed_costs_id.message_post(
                        body=message,
                        subject=_("Invoice linked"),
                        message_type='comment', 
                    )                  
        return res                                             
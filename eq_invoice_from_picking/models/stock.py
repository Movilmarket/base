# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

journal_type_dict = {
            ('outgoing', 'customer'): ['out_invoice'],
            ('incoming', 'supplier'): ['in_invoice'],
            }


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    @api.depends('invoice_ids')
    def _get_len_invoice_ids(self):
        for picking in self:
            picking.invoice_ids_count = len(picking.invoice_ids)

    invoice_ids = fields.Many2many('account.invoice', 'table_account_invoice_stock_picking_relation', 'picking_id', 'invoice_id',
                                    string="Invoice", copy=False)
    invoice_ids_count = fields.Integer(string="Invoices", compute="_get_len_invoice_ids", store=True)

    @api.multi
    def view_account_invoices(self):
        if self.invoice_ids:
            invoice_type = self.invoice_ids[0].type
            if invoice_type == 'in_invoice':
                action = self.env.ref('account.action_vendor_bill_template').read()[0]
            else:  # invoice_type == 'out_invoice':
                action = self.env.ref('account.action_invoice_tree1').read()[0]
            action['domain'] = [('id', 'in', self.invoice_ids.ids)]
            return action

    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        context = self.env.context
        invoice_vals = {
            'name': self.name,
            'type': context.get('invoice_type'),
            'partner_id': self.partner_id.id,
            'journal_id': context.get('journal_id'),
            'company_id': self.company_id.id,
            'date_invoice': context.get('invoice_date'),
            'stock_picking_ids': [(4, self.id)],
            'origin': self.origin,
            'user_id': context.get('user_id')
        }
        return invoice_vals


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    def _prepare_invoice_line_from_po_line(self, line):
        data = super(account_invoice, self)._prepare_invoice_line_from_po_line(line)
        if self.env.context.get('from_picking_done_qty'):
            data['quantity'] = self.env.context.get('from_picking_done_qty')
        return data


    stock_picking_ids = fields.Many2many('stock.picking', 'table_account_invoice_stock_picking_relation', 'invoice_id', 'picking_id',
                                        string="Picking Ref.")


class wizard_stock_picking_invoice(models.TransientModel):
    _name = 'wizard.stock.picking.invoice'
    _description = "Wizard Stock Picking Description"

    journal_id = fields.Many2one('account.journal', string="Journal", required=True)
    invoice_type = fields.Selection([('out_invoice', 'Create Customer Invoice'),
                                     ('out_refund', 'Create Customer Credit Note'),
                                     ('in_invoice', 'Create Vendor Bill'),
                                     ('in_refund', 'Create Vendor Refund')], 'Invoice Type', readonly=True)
    invoice_date = fields.Date(string="Invoice Date")
    group_by_partner = fields.Boolean(string="Group By Partner")

    @api.model
    def default_get(self, fieldslist):
        res = super(wizard_stock_picking_invoice, self).default_get(fieldslist)
        context = self.env.context
        picking_ids = context and context.get('active_ids', [])
        pickings = self.env['stock.picking'].browse(picking_ids)
        pick = pickings and pickings[0]
        if not pick or not pick.move_lines:
            return {}
        type = pick.picking_type_code
        usage = pick.move_lines[0].location_id.usage if type == 'incoming' else pick.move_lines[0].location_dest_id.usage
        res.update({'invoice_type': journal_type_dict.get((type, usage), [''])[0]})
        return res

    @api.onchange('invoice_type')
    def _onchange_invoice_type(self):
        domain = [('type', 'in', {'out_invoice': ['sale'],
                                  'out_refund': ['sale'],
                                  'in_refund': ['purchase'],
                                  'in_invoice': ['purchase']}.get(self.invoice_type, [])),
                  ('company_id', '=', self.env.user.company_id.id)]
        return {'domain': {'journal_id': domain}}

    @api.multi
    def create_invoice(self):
        picking_ids = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        invoice_date = self.invoice_date or datetime.now().today().date()
        if any([not picking.partner_id for picking in picking_ids]):
            raise ValidationError(_("Partner not found. For create invoice, into picking must have the partner."))
        picking_code_lst = picking_ids.mapped('picking_type_code')
        if 'internal' in picking_code_lst:
            raise ValidationError(_("Select only Delivery Orders / Receipts for create Invoice."))
        if len(set(picking_code_lst)) > 1:
            raise ValidationError(_("Selected picking must have same Operation Type."))
        if not self.journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))

        if any([ picking.state not in ['done'] for picking in picking_ids]):
            raise ValidationError(_("Selected picking must have in Done State."))

        groupby_lst = {}
        for picking_id in picking_ids.filtered(lambda l:l.state == 'done'):
            if picking_id.invoice_ids or not picking_id.move_lines:
                continue
            if self.group_by_partner:
                key = picking_id.partner_id.id
            else:
                key = picking_id.id
            groupby_lst.setdefault(key, [])
            groupby_lst[key].append(picking_id)

        for lst_items in groupby_lst.values():
            invoice_lst = {}
            for picking in lst_items:
                user_id = False
                if picking.sale_id:
                    user_id = picking.sale_id.user_id.id or False
                if picking.purchase_id:
                    user_id = picking.purchase_id.user_id.id or False
                key = (picking.partner_id.id, picking.company_id.id, user_id)
                invoice_vals = picking.with_context(journal_id=self.journal_id.id, invoice_date=self.invoice_date, invoice_type=self.invoice_type, user_id=user_id)._prepare_invoice()
                if key not in invoice_lst:
                    invoice_id = self.env['account.invoice'].create(invoice_vals)
                    invoice_lst[key] = invoice_id
                else:
                    invoice_id = invoice_lst[key]
                    update_inv_data = {'stock_picking_ids': [(4, picking.id)]}
                    if not invoice_id.origin or invoice_vals['origin'] not in invoice_id.origin.split(', '):
                        invoice_origin = filter(None, [invoice_id.origin, invoice_vals['origin']])
                        update_inv_data['origin'] = ', '.join(invoice_origin)
                    if invoice_vals.get('name', False) and (not invoice_id.name or invoice_vals['name'] not in invoice_id.name.split(', ')):
                        invoice_name = filter(None, [invoice_id.name, invoice_vals['name']])
                        update_inv_data['name'] = ', '.join(invoice_name)
                    if update_inv_data:
                        invoice_id.write(update_inv_data)
                if invoice_id:
                    for each in picking.move_lines:
                        if each.sale_line_id:
                            qty = each.sale_line_id.qty_to_invoice
                            if qty > each.quantity_done:
                                qty = each.quantity_done
                            each.sale_line_id.invoice_line_create(invoice_id=invoice_id.id, qty=qty)
                        if each.purchase_line_id:
                            invoice_id.write({'purchase_id': each.purchase_line_id.order_id.id})
                            invoice_id.with_context({'from_picking_done_qty': each.quantity_done})._prepare_invoice_line_from_po_line(each.purchase_line_id)
                            invoice_id.purchase_order_change()
                    picking.write({'invoice_ids': [(4, invoice_id.id)],
                    })
                    invoice_id.compute_taxes()
                    if not invoice_id.invoice_line_ids:
                        invoice_id.sudo().unlink()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- coding: utf-8 -*-
import json
import logging
from lxml import etree
from lxml.builder import E
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class BundleProduct(models.Model):
    _name = 'bundle.product'

    @api.onchange('product_id')
    def _product_onchange(self):
        for rec in self:
            rec.uom_id = rec.product_id.uom_id.id
            rec.unit_price = rec.product_id.lst_price

    @api.depends('unit_price','qty')
    def _compute_sale_price(self):
        for rec in self:
            rec.sale_price = rec.qty * rec.unit_price

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
    qty = fields.Float(
        string='Quantity',
        default=1.0,
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Uom',
    )
    product_template_id = fields.Many2one(
        'product.template',
        string='Product Bundle',
    )
    unit_price = fields.Float(
        string='Unit Price',
    )
    sale_price = fields.Float(
        string='Sub Total',
        compute='_compute_sale_price'
    )
    pricelist_id = fields.Many2one(
        'product.pricelist', 
        string='Pricelist', 
        help="Pricelist for current bundle.")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends('bundle_product_ids','pricelist_bundle_id')
    def _compute_total(self):
        for rec in self:
            rec.list_price = 0
            for product in rec.bundle_product_ids:                
                if rec.pricelist_bundle_id.id==product.pricelist_id.id:
                    rec.total2 += product.sale_price
                if not product.pricelist_id:
                    rec.total += product.sale_price
                    rec.list_price += product.sale_price
                            
    @api.depends('pricelist_bundle_id','bundle_product_ids')
    def _check_pricelist_bundle(self):
        is_updated = 0
        if self.pricelist_bundle_id:            
            if self.item_ids:
                is_updated = 1                
                for x in self.item_ids:
                    if x.pricelist_id.id==self.pricelist_bundle_id.id:
                        price_fixed = x.fixed_price
                        is_updated = 2                    
            else:
                is_updated = 1
        self.pricelist_bundle_update = is_updated                            

    bundle_product = fields.Boolean(
        'Is Bundled',
    )
    bundle_product_ids = fields.One2many(
        'bundle.product',
        'product_template_id',
        domain=[('pricelist_id','=',False)]
    )    
    total = fields.Float(
        string="Total",
        compute="_compute_total",
    )
    total2 = fields.Float(
        string="Total",
        compute="_compute_total",
    )    
    pricelist_bundle_id = fields.Many2one(
        'product.pricelist', 
        string='Pricelist', 
        help="Pricelist for current bundle.")
    pricelist_bundle_update = fields.Integer(
        compute="_check_pricelist_bundle",
    )
    pricelist_bundle_domain = fields.Char(
        compute="_compute_pricelist_bundle_domain",
        readonly=True,
        store=False,
    )    
    
    @api.multi
    @api.depends('pricelist_bundle_id')
    def _compute_pricelist_bundle_domain(self):
        for rec in self:
            if self.pricelist_bundle_id and self.pricelist_bundle_update==1:
                rec.pricelist_bundle_domain = json.dumps([('pricelist_id','=',False)])
            else:  
                rec.pricelist_bundle_domain = json.dumps([('pricelist_id','=',self.pricelist_bundle_id.id if self.pricelist_bundle_id else False)])        

    """
    @api.onchange('pricelist_bundle_id','bundle_product_ids')
    @api.model
    def onchange_pricelist_bundle_id(self):
        return {'domain':{'bundle_product_ids':self.pricelist_bundle_domain}}
        """    

    @api.model
    def create(self, vals):
        bundle_product = vals.get('bundle_product', False)
        attribute_line_ids = vals.get('attribute_line_ids', False)
        if bundle_product and attribute_line_ids:
            raise ValidationError(_('You can not set variant for bundled product.'))
        return super(ProductTemplate, self).create(vals)

    @api.multi
    def write(self, vals):
        for rec in self:
            bundle_product = vals.get('bundle_product', False) or rec.bundle_product
            attribute_line_ids = vals.get('attribute_line_ids', False) or rec.attribute_line_ids            
            if bundle_product and attribute_line_ids:
                raise ValidationError(_('You can not set variant for bundled product.'))                    
        res = super(ProductTemplate, self).write(vals)
        return res
    
    def action_create_pricelist_bundle(self):
        # Duplicar los productos del combo original y asignarle la tarica indicada
        vals = {}

        new_bundle = []
        for rec in self.bundle_product_ids:
            if not rec.pricelist_id:
                vals2 = {
                    'product_id':rec.product_id.id,
                    'qty':rec.qty,
                    'uom_id':rec.uom_id.id,
                    #'product_template_id':rec.product_template_id,
                    'unit_price':rec.unit_price,
                    'sale_price':rec.sale_price,
                    'pricelist_id':self.pricelist_bundle_id.id,
                }
                new_bundle.append((0,0,vals2))

        item_ids = []
        item_ids.append((0, 0, {'pricelist_id':self.pricelist_bundle_id.id,'fixed_price':self.total}))  
        vals['bundle_product_ids'] = new_bundle
        vals['item_ids'] = item_ids
        self.update(vals)  
                
        # Actualizar la lista de Precios con el Precio del combo para la tarifa        

    
    def action_update_pricelist_bundle(self):
                
        return True        

class StockMove(models.Model):
    _inherit = "stock.move"
    
    @api.model_create_multi
    def create(self, vals_list):
        new_list = []
        for vals in vals_list:    
            bundle = vals['product_id']        
            bundle_id = self.env['product.product'].browse(bundle)
            if bundle_id.product_tmpl_id.bundle_product:
                qty = vals['product_uom_qty']
                nvals = vals.copy()
                for product in bundle_id.product_tmpl_id.bundle_product_ids:
                    product_id = product.product_id.id
                    product_name = product.product_id.product_tmpl_id.name
                    product_uom_id = product.uom_id.id
                    new_qty = qty*product.qty     
                    if 'sale_line_id' in vals:               
                        nvals = {'warehouse_id':vals['warehouse_id'],
                                 'date_expected': vals['date_expected'], 
                                 'product_id': product_id, 
                                 'product_uom_qty': new_qty, 
                                 'location_dest_id': vals['location_dest_id'], 
                                 'rule_id': vals['rule_id'], 
                                 'priority': vals['priority'], 
                                 'product_uom': product_uom_id, 
                                 'partner_id': vals['partner_id'], 
                                 'origin': vals['origin'], 
                                 'route_ids': vals['route_ids'], 
                                 'location_id': vals['location_id'], 
                                 'move_dest_ids': vals['move_dest_ids'], 
                                 'name': product_name, 
                                 'sale_line_id': vals['sale_line_id'], 
                                 'propagate': vals['propagate'], 
                                 'group_id': vals['group_id'], 
                                 'company_id': vals['company_id'], 
                                 'picking_type_id': vals['picking_type_id'], 
                                 'date': vals['date'], 
                                 'procure_method': vals['procure_method']}
                    else:
                        nvals = {'product_uom': product_uom_id, 
                                 'product_uom_qty': new_qty, 
                                 'picking_type_id': vals['picking_type_id'], 
                                 'picking_id': vals['picking_id'], 
                                 'location_dest_id': vals['location_dest_id'], 
                                 'location_id': vals['location_id'], 
                                 'state': vals['state'], 
                                 'product_id': product_id, 
                                 'additional': vals['additional'], 
                                 'name': product_name, 
                                 'date_expected': vals['date_expected']}
                    _logger.info('Product new vals %s' % (nvals))                     
                    new_list.append(nvals)
            else:
                new_list.append(vals)                            
        res = super(StockMove, self).create(new_list)
        return res
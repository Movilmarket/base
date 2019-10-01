# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BundleProductPriceRate(models.TransientModel):
    _name = "bundle.product.pricerate"
    
    @api.model
    def default_get(self, fields):
        rec = super(BundleProductPriceRate, self).default_get(fields)
        active_id = self.env[self._context.get('active_model') ].browse(self._context.get('active_id'))
        bundle_product_obj = self.env['bundle.product']
        new_bundle = []
        if active_id.pricelist_bundle_update==1:
            for product in active_id.bundle_product_ids:
                vals2 = {
                    'product_id':product.product_id.id,
                    'qty':product.qty,
                    'uom_id':product.uom_id.id,
                    'unit_price':product.unit_price,
                    'sale_price':product.sale_price,
                    'pricelist_id':active_id.pricelist_bundle_id.id,
                }                
                new_bundle.append((0,0,vals2))
        else:
            for product in bundle_product_obj.search([('pricelist_id','=',active_id.pricelist_bundle_id.id),('product_template_id','=',active_id.id)]):
                vals2 = {
                    'product_id':product.product_id.id,
                    'qty':product.qty,
                    'uom_id':product.uom_id.id,
                    'unit_price':product.unit_price,
                    'sale_price':product.sale_price,
                    'pricelist_id':active_id.pricelist_bundle_id.id,
                }                 
                new_bundle.append((0,0,vals2))                            
        rec.update({
                'pricelist_id':active_id.pricelist_bundle_id.id,
                'bundle_product_ids':new_bundle,
        })
        return rec    
    
    @api.depends('bundle_product_ids')
    def _compute_total(self):
        for rec in self:
            for product in rec.bundle_product_ids:                
                rec.sale_price += product.sale_price

    
    qty = fields.Float(
        'Quantity',
        default=0.0,
    )
    pricelist_id = fields.Many2one(
        'product.pricelist',
        'Pricelist',
    )
    product_template_id = fields.Many2one(
        'product.template',
        string='Product Bundle',
    )    
    bundle_product_ids = fields.One2many(
        'bundle.product.tmp',
        'tmp_template_id',        
        string='Bundle Products',    
    )
    sale_price = fields.Float(
        string='Pack / Bundle Price',
        compute='_compute_total'
    )    
        
    @api.multi
    def update_pricelist_bundle_product(self):
        vals = {}
        active_id = self.env[self._context.get('active_model') ].browse(self._context.get('active_id'))
        active_obj = self.env['product.template'].browse(self._context.get('active_id'))
        bundle_product_obj = self.env['bundle.product']
        product_pricelist_item_obj = self.env['product.pricelist.item']
        new_bundle = []
        for product in self.bundle_product_ids:
            vals2 = {
                'product_id':product.product_id.id,
                'qty':product.qty,
                'uom_id':product.uom_id.id,
                'unit_price':product.unit_price,
                'sale_price':product.sale_price,
                'pricelist_id':active_id.pricelist_bundle_id.id,
            }
            new_bundle.append((0,0,vals2))
        bundle_ids_old = bundle_product_obj.search([('pricelist_id','=',active_id.pricelist_bundle_id.id),('product_template_id','=',active_id.id)])
        xids = [x.id for x in bundle_ids_old]
        bundle_product_obj.browse(xids).unlink()
        item_ids_old = product_pricelist_item_obj.search([('pricelist_id','=',active_id.pricelist_bundle_id.id),('product_tmpl_id','=',active_id.id)])
        xids = [x.id for x in item_ids_old]
        product_pricelist_item_obj.browse(xids).unlink()        
        item_ids = []
        item_ids.append((0, 0, {'pricelist_id':self.pricelist_id.id,'fixed_price':self.sale_price,'min_quantity':self.qty}))
        vals['bundle_product_ids'] = new_bundle
        vals['item_ids'] = item_ids        
        active_id.update(vals)

class BundleProduct(models.TransientModel):
    _name = 'bundle.product.tmp'

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
    tmp_template_id = fields.Many2one(
        'bundle.product.pricerate',
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
                                 
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
from datetime import date, datetime, time, timedelta

_logger = logging.getLogger(__name__)

class inventory_transfer_request(models.Model):
    _name = 'inventory_transfer_request.inventory_transfer_request'
    _description = 'Stock Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(default='New', readonly=True, required=True)
    description = fields.Text()
    requested_by = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user, readonly=1)
    approved_by = fields.Many2one('res.users', string='Approved By')
    validated_by = fields.Many2one('res.users', string='Validated By', required=True)
    recived_by = fields.Many2one('res.users', string='Recived By', required=True)
    request_date = fields.Date(required=True)
    product_lines_ids = fields.One2many('inventory.transfer.line', 'transfer_request_id', string='Products')
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent'), ('validated', 'Validated'),('approved', 'Approved'),('confirmed', 'Confirmed')], string='Status', readonly=True, default='draft')
    total = fields.Float('Total', readonly=1)

    
    @api.onchange('product_lines_ids')
    def onchange_product_line_ids(self):
        sum = 0
        if self.product_lines_ids:
            for line in self.product_lines_ids:
                sum = sum + line.total_price
            self.total = sum

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('inventory_transfer_request.inventory_transfer_request.sequence') or 'New'

        return super(inventory_transfer_request, self).create(vals)
           
    def button_send_request(self):
        self.state = 'sent'
        users = self.env.ref('inventory_transfer_request.group_inventory_validator').users
        if self.product_lines_ids:        
            for user in users:
                activity_type = self.env.ref('inventory_transfer_request.mail_activity_inv_approval')
                self.activity_schedule('inventory_transfer_request.mail_activity_inv_approval', user_id=user.id, note=f'Please Validate This Request')
        else:
            raise UserError(_(str("Please Select Products")))

    def button_validate(self):
        context = self._context
        current_uid = context.get('uid')
        user = self.env['res.users'].browse(current_uid)

        if user.id != self.validated_by.id:
            raise UserError(_(str("Sory The Request Was Sent For Other User")))
        else:
            self.state = 'validated'
       
        activity_id = self.env['mail.activity'].search([('res_id', '=',  self.id), ('user_id', '=', self.env.user.id),
                                                         ('activity_type_id', '=', self.env.ref('inventory_transfer_request.mail_activity_inv_approval').id)])
        activity_id.action_feedback(feedback='Approved')

        other_activity_id = self.env['mail.activity'].search([('res_id', '=',  self.id), ('activity_type_id', '=', self.env.ref('inventory_transfer_request.mail_activity_inv_approval').id)])
        other_activity_id.unlink()

    def button_approve(self):
        self.state = 'approved'
        context = self._context
        current_uid = context.get('uid')
        user = self.env['res.users'].browse(current_uid)
        self.approved_by = user
    
    def button_confirm(self):
        self.state = 'confirmed'

    def button_reset_to_draft(self):
        self.state = 'draft'
    
    def button_refuse(self):
        self.state = 'refused'

    def button_make_transfer(self):

        view_id = self.env.ref('stock.view_picking_form')

        order_line = []
        for line in self.product_lines_ids:
            product = line.product_id

            product_line = (0, 0, {
                'product_id': line.product_id,
                'product_uom': line.product_id.uom_id.id,
            })
            order_line.append(product_line)
        _logger.info("------------order Line-----------sub=s%s",order_line)

        if order_line:
            return {
                'name': _('New Quotation'),
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'target': 'current',
                'request_id': self.id,
                'view_id': view_id.id,
                'views': [(view_id.id, 'form')],
                'context': {
                # 'default_move_ids_without_package': order_line,
                'default_transfer_request_id': self.id,
                }
            }


class StockPicking(models.Model):
    _inherit = "stock.picking"


    transfer_request_id = fields.Many2one('inventory_transfer_request.inventory_transfer_request', string='Transfer Request')

    @api.onchange('transfer_request_id')
    def _onchange_transfer_request_id(self):
        products=[(5,0,0)]
        for line in self.transfer_request_id.product_lines_ids:
            _logger.info("------------line-----------sub=s%s",line)
            # self.product_catalogue_ids.product_id = line
            val={}
            val['product_id']=line.product_id
            val['product_uom']=line.product_id.uom_id
            val['product_uom_qty']=line.requested_qty
            val['name']=self.transfer_request_id.name
            products.append((0,0, val))
        _logger.info("------------products-----------sub=s%s",products)
        
        self.move_ids_without_package = products

class inventory_transfer_line(models.Model):
    _name = "inventory.transfer.line"
    # _description = 'Inventory Transfer Line'
    

    transfer_request_id = fields.Many2one('inventory_transfer_request.inventory_transfer_request', string='Transfer Request')
    requested_qty = fields.Integer(required=True, string='Requested Quantity', default=1)
    unit_price = fields.Float(required=True, string='Unit Price')
    total_price = fields.Float(required=True, string='Total Price')
    product_id = fields.Many2one('product.product', required=True, string='Product')
    part_number = fields.Char()
    request_date = fields.Date(tring='Date', default=datetime.today())




    @api.onchange('product_id', 'requested_qty', 'unit_price')
    def onchange_product_id(self):
        if self.product_id.list_price > 1:
                self.unit_price =self.product_id.standard_price

        if self.product_id:
                # self.unit_price =self.product_id.list_price
                self.total_price =self.unit_price * self.requested_qty
                self.part_number =self.product_id.default_code
          

    # @api.onchange('product_id', 'requested_qty')
    # def onchange_product_id(self):
    #     if self.product_id:
    #         self.unit_price =self.product_id.list_price
            # new = []
            # for vals in vals_list:
            #     new.append(vals)
            # print(new)

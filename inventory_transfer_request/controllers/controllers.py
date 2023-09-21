# -*- coding: utf-8 -*-
# from odoo import http


# class InventoryTransferRequest(http.Controller):
#     @http.route('/inventory_transfer_request/inventory_transfer_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/inventory_transfer_request/inventory_transfer_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('inventory_transfer_request.listing', {
#             'root': '/inventory_transfer_request/inventory_transfer_request',
#             'objects': http.request.env['inventory_transfer_request.inventory_transfer_request'].search([]),
#         })

#     @http.route('/inventory_transfer_request/inventory_transfer_request/objects/<model("inventory_transfer_request.inventory_transfer_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('inventory_transfer_request.object', {
#             'object': obj
#         })

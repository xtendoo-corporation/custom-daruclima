# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Integración con FSM
    fsm_order_id = fields.Many2one(
        'daruclima.fsm.order',
        string='Orden de Servicio FSM',
        help="Orden de servicio de campo relacionada"
    )
    is_fsm_order = fields.Boolean(
        string='Es Orden FSM',
        compute='_compute_is_fsm_order',
        store=True
    )

    @api.depends('fsm_order_id')
    def _compute_is_fsm_order(self):
        for order in self:
            order.is_fsm_order = bool(order.fsm_order_id)

    def action_view_fsm_order(self):
        """Ver la orden FSM relacionada"""
        if self.fsm_order_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'daruclima.fsm.order',
                'res_id': self.fsm_order_id.id,
                'view_mode': 'form',
            }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    # Integración con FSM
    fsm_order_id = fields.Many2one(
        'daruclima.fsm.order',
        string='Orden de Servicio FSM',
        help="Orden de servicio de campo relacionada"
    )
    is_fsm_service = fields.Boolean(
        string='Es Servicio FSM',
        related='product_id.is_fsm_service',
        store=True
    )

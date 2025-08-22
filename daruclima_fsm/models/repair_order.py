# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models, _


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    # Integración con FSM
    fsm_order_id = fields.Many2one(
        'daruclima.fsm.order',
        string='Orden de Servicio FSM',
        help="Orden de servicio de campo relacionada"
    )
    fsm_equipment_id = fields.Many2one(
        'daruclima.fsm.equipment',
        string='Equipo FSM',
        help="Equipo de cliente relacionado"
    )

    def action_view_fsm_order(self):
        """Ver la orden FSM relacionada"""
        if self.fsm_order_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'daruclima.fsm.order',
                'res_id': self.fsm_order_id.id,
                'view_mode': 'form',
            }

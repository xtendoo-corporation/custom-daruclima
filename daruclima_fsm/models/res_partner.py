# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Campos FSM
    is_fsm_location = fields.Boolean(
        string='Es Ubicación FSM',
        help="Este contacto es una ubicación de servicio"
    )

    # Relaciones FSM
    fsm_location_ids = fields.One2many(
        'daruclima.fsm.location',
        'partner_id',
        string='Ubicaciones de Servicio'
    )
    fsm_order_ids = fields.One2many(
        'daruclima.fsm.order',
        'partner_id',
        string='Órdenes de Servicio'
    )
    fsm_equipment_ids = fields.One2many(
        'daruclima.fsm.equipment',
        'partner_id',
        string='Equipos'
    )

    # Estadísticas FSM
    fsm_order_count = fields.Integer(
        string='Total Órdenes FSM',
        compute='_compute_fsm_statistics'
    )
    fsm_location_count = fields.Integer(
        string='Total Ubicaciones',
        compute='_compute_fsm_statistics'
    )
    fsm_equipment_count = fields.Integer(
        string='Total Equipos',
        compute='_compute_fsm_statistics'
    )

    @api.depends('fsm_order_ids', 'fsm_location_ids', 'fsm_equipment_ids')
    def _compute_fsm_statistics(self):
        for partner in self:
            partner.fsm_order_count = len(partner.fsm_order_ids)
            partner.fsm_location_count = len(partner.fsm_location_ids)
            partner.fsm_equipment_count = len(partner.fsm_equipment_ids)

    def action_view_fsm_orders(self):
        """Ver órdenes FSM del cliente"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Órdenes FSM - {self.name}',
            'res_model': 'daruclima.fsm.order',
            'view_mode': 'tree,form,kanban',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def action_view_fsm_locations(self):
        """Ver ubicaciones FSM del cliente"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ubicaciones - {self.name}',
            'res_model': 'daruclima.fsm.location',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def action_view_fsm_equipment(self):
        """Ver equipos FSM del cliente"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Equipos - {self.name}',
            'res_model': 'daruclima.fsm.equipment',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

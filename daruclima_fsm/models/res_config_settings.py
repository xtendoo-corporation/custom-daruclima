# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Configuración FSM
    fsm_default_team_id = fields.Many2one(
        'daruclima.fsm.team',
        string='Equipo FSM por Defecto',
        config_parameter='daruclima_fsm.default_team_id'
    )
    fsm_auto_create_project = fields.Boolean(
        string='Crear Proyecto Automáticamente',
        config_parameter='daruclima_fsm.auto_create_project',
        help="Crear automáticamente un proyecto para cada orden FSM"
    )
    fsm_enable_geolocation = fields.Boolean(
        string='Habilitar Geolocalización',
        config_parameter='daruclima_fsm.enable_geolocation',
        help="Habilitar funciones de geolocalización para órdenes FSM"
    )
    fsm_invoice_policy = fields.Selection([
        ('manual', 'Manual'),
        ('timesheet', 'Basado en Hojas de Tiempo'),
        ('delivery', 'Al Completar Orden')
    ], string='Política de Facturación FSM',
        config_parameter='daruclima_fsm.invoice_policy',
        default='manual'
    )

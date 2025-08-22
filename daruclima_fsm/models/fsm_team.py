# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models, _


class DaruclimeFSMTeam(models.Model):
    _name = 'daruclima.fsm.team'
    _description = 'Equipo de Servicio de Campo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(
        string='Nombre del Equipo',
        required=True,
        tracking=True
    )
    code = fields.Char(
        string='Código',
        required=True,
        help="Código único del equipo"
    )
    description = fields.Text(
        string='Descripción'
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )
    active = fields.Boolean(
        string='Activo',
        default=True
    )

    # Responsable del equipo
    leader_id = fields.Many2one(
        'daruclima.fsm.person',
        string='Líder del Equipo',
        tracking=True
    )

    # Miembros del equipo
    person_ids = fields.One2many(
        'daruclima.fsm.person',
        'team_id',
        string='Miembros del Equipo'
    )

    # Territorios asignados
    territory_ids = fields.Many2many(
        'res.country.state',
        string='Territorios Asignados',
        help="Territorios donde opera este equipo"
    )

    # Estadísticas
    order_count = fields.Integer(
        string='Órdenes Totales',
        compute='_compute_statistics'
    )
    order_active_count = fields.Integer(
        string='Órdenes Activas',
        compute='_compute_statistics'
    )
    order_completed_count = fields.Integer(
        string='Órdenes Completadas',
        compute='_compute_statistics'
    )

    # Configuración
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )
    color = fields.Integer(
        string='Color',
        default=0
    )

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for team in self:
            if team.code:
                team.display_name = f"[{team.code}] {team.name}"
            else:
                team.display_name = team.name

    def _compute_statistics(self):
        """Calcula estadísticas del equipo"""
        for team in self:
            orders = self.env['daruclima.fsm.order'].search([
                ('team_id', '=', team.id)
            ])
            team.order_count = len(orders)
            team.order_active_count = len(orders.filtered(lambda o: not o.is_closed))
            team.order_completed_count = len(orders.filtered(lambda o: o.is_closed))

    def action_view_orders(self):
        """Acción para ver las órdenes del equipo"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Órdenes del Equipo {self.name}',
            'res_model': 'daruclima.fsm.order',
            'view_mode': 'tree,form,kanban',
            'domain': [('team_id', '=', self.id)],
            'context': {'default_team_id': self.id}
        }


class DaruclimeFSMPerson(models.Model):
    _name = 'daruclima.fsm.person'
    _description = 'Técnico de Servicio de Campo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        tracking=True
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        required=True,
        tracking=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Usuario',
        related='employee_id.user_id',
        store=True
    )

    # Información del técnico
    phone = fields.Char(
        string='Teléfono',
        related='employee_id.work_phone'
    )
    mobile = fields.Char(
        string='Móvil',
        related='employee_id.mobile_phone'
    )
    email = fields.Char(
        string='Email',
        related='employee_id.work_email'
    )

    # Equipo al que pertenece
    team_id = fields.Many2one(
        'daruclima.fsm.team',
        string='Equipo',
        tracking=True
    )

    # Especialidades
    skill_ids = fields.Many2many(
        'hr.skill',
        string='Habilidades',
        help="Habilidades y especialidades del técnico"
    )
    category_ids = fields.Many2many(
        'daruclima.fsm.tag',
        string='Especialidades',
        help="Categorías de servicios en las que se especializa"
    )

    # Configuración
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    is_available = fields.Boolean(
        string='Disponible',
        default=True,
        help="Indica si el técnico está disponible para nuevas asignaciones"
    )

    # Estadísticas
    order_count = fields.Integer(
        string='Órdenes Asignadas',
        compute='_compute_statistics'
    )
    order_active_count = fields.Integer(
        string='Órdenes Activas',
        compute='_compute_statistics'
    )
    order_completed_count = fields.Integer(
        string='Órdenes Completadas',
        compute='_compute_statistics'
    )
    hours_total = fields.Float(
        string='Horas Totales',
        compute='_compute_statistics'
    )

    # Ubicación actual
    partner_latitude = fields.Float(
        string='Latitud',
        digits=(10, 7)
    )
    partner_longitude = fields.Float(
        string='Longitud',
        digits=(10, 7)
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )

    def _compute_statistics(self):
        """Calcula estadísticas del técnico"""
        for person in self:
            orders = self.env['daruclima.fsm.order'].search([
                ('person_ids', 'in', [person.id])
            ])
            person.order_count = len(orders)
            person.order_active_count = len(orders.filtered(lambda o: not o.is_closed))
            person.order_completed_count = len(orders.filtered(lambda o: o.is_closed))

            # Calcular horas totales de timesheet
            timesheets = self.env['account.analytic.line'].search([
                ('employee_id', '=', person.employee_id.id),
                ('fsm_order_id', '!=', False)
            ])
            person.hours_total = sum(timesheets.mapped('unit_amount'))

    def action_view_orders(self):
        """Acción para ver las órdenes del técnico"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Órdenes de {self.name}',
            'res_model': 'daruclima.fsm.order',
            'view_mode': 'tree,form,kanban',
            'domain': [('person_ids', 'in', [self.id])],
            'context': {'default_person_ids': [(6, 0, [self.id])]}
        }

    def action_view_schedule(self):
        """Acción para ver la agenda del técnico"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Agenda de {self.name}',
            'res_model': 'daruclima.fsm.order',
            'view_mode': 'calendar,tree,form',
            'domain': [('person_ids', 'in', [self.id])],
            'context': {
                'default_person_ids': [(6, 0, [self.id])],
                'calendar_default_start': 'date_scheduled',
            }
        }

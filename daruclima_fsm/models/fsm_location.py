# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models, _


class DaruclimeFSMLocation(models.Model):
    _name = 'daruclima.fsm.location'
    _description = 'Ubicación de Servicio'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Nombre de la Ubicación',
        required=True,
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True
    )

    # Dirección completa
    street = fields.Char(string='Calle')
    street2 = fields.Char(string='Calle 2')
    city = fields.Char(string='Ciudad')
    state_id = fields.Many2one('res.country.state', string='Provincia')
    zip = fields.Char(string='Código Postal')
    country_id = fields.Many2one('res.country', string='País')

    # Geolocalización
    partner_latitude = fields.Float(
        string='Latitud',
        digits=(10, 7)
    )
    partner_longitude = fields.Float(
        string='Longitud',
        digits=(10, 7)
    )

    # Información de contacto
    contact_id = fields.Many2one(
        'res.partner',
        string='Contacto Principal',
        domain="[('parent_id', '=', partner_id), ('is_company', '=', False)]"
    )
    phone = fields.Char(string='Teléfono')
    email = fields.Char(string='Email')

    # Equipos en esta ubicación
    equipment_ids = fields.One2many(
        'daruclima.fsm.equipment',
        'location_id',
        string='Equipos'
    )

    # Órdenes de servicio
    order_ids = fields.One2many(
        'daruclima.fsm.order',
        'location_id',
        string='Órdenes de Servicio'
    )

    # Información adicional
    description = fields.Text(string='Descripción')
    access_info = fields.Text(
        string='Información de Acceso',
        help="Instrucciones especiales para acceder a la ubicación"
    )

    # Configuración
    active = fields.Boolean(string='Activo', default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )

    # Estadísticas
    order_count = fields.Integer(
        string='Total Órdenes',
        compute='_compute_statistics'
    )
    equipment_count = fields.Integer(
        string='Total Equipos',
        compute='_compute_statistics'
    )

    @api.depends('order_ids', 'equipment_ids')
    def _compute_statistics(self):
        for location in self:
            location.order_count = len(location.order_ids)
            location.equipment_count = len(location.equipment_ids)

    def action_view_orders(self):
        """Ver órdenes de esta ubicación"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Órdenes - {self.name}',
            'res_model': 'daruclima.fsm.order',
            'view_mode': 'tree,form,kanban',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id}
        }

    def action_view_equipment(self):
        """Ver equipos de esta ubicación"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Equipos - {self.name}',
            'res_model': 'daruclima.fsm.equipment',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id}
        }


class DaruclimeFSMEquipment(models.Model):
    _name = 'daruclima.fsm.equipment'
    _description = 'Equipo de Cliente'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Nombre del Equipo',
        required=True,
        tracking=True
    )
    code = fields.Char(
        string='Código/Serie',
        tracking=True
    )

    # Relaciones
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True
    )
    location_id = fields.Many2one(
        'daruclima.fsm.location',
        string='Ubicación',
        tracking=True
    )

    # Información del equipo
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        help="Producto relacionado con este equipo"
    )
    brand = fields.Char(string='Marca')
    model = fields.Char(string='Modelo')
    serial_number = fields.Char(string='Número de Serie')

    # Fechas importantes
    purchase_date = fields.Date(string='Fecha de Compra')
    installation_date = fields.Date(string='Fecha de Instalación')
    warranty_expiry = fields.Date(string='Vencimiento Garantía')

    # Estado y mantenimiento
    status = fields.Selection([
        ('active', 'Activo'),
        ('maintenance', 'En Mantenimiento'),
        ('inactive', 'Inactivo'),
        ('retired', 'Retirado')
    ], string='Estado', default='active', tracking=True)

    maintenance_frequency = fields.Integer(
        string='Frecuencia Mantenimiento (días)',
        default=365,
        help="Días entre mantenimientos preventivos"
    )
    last_maintenance_date = fields.Date(string='Último Mantenimiento')
    next_maintenance_date = fields.Date(
        string='Próximo Mantenimiento',
        compute='_compute_next_maintenance'
    )

    # Órdenes de servicio relacionadas
    order_ids = fields.Many2many(
        'daruclima.fsm.order',
        string='Órdenes de Servicio'
    )

    # Información técnica
    specifications = fields.Text(string='Especificaciones Técnicas')
    manual_url = fields.Char(string='URL del Manual')
    notes = fields.Text(string='Notas')

    # Configuración
    active = fields.Boolean(string='Activo', default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )

    # Estadísticas
    order_count = fields.Integer(
        string='Total Órdenes',
        compute='_compute_statistics'
    )
    maintenance_count = fields.Integer(
        string='Mantenimientos',
        compute='_compute_statistics'
    )

    @api.depends('last_maintenance_date', 'maintenance_frequency')
    def _compute_next_maintenance(self):
        for equipment in self:
            if equipment.last_maintenance_date and equipment.maintenance_frequency:
                equipment.next_maintenance_date = equipment.last_maintenance_date + timedelta(
                    days=equipment.maintenance_frequency
                )
            else:
                equipment.next_maintenance_date = False

    @api.depends('order_ids')
    def _compute_statistics(self):
        for equipment in self:
            equipment.order_count = len(equipment.order_ids)
            equipment.maintenance_count = len(equipment.order_ids.filtered(
                lambda o: 'mantenimiento' in o.description.lower()
            ))

    def action_view_orders(self):
        """Ver órdenes de este equipo"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Órdenes - {self.name}',
            'res_model': 'daruclima.fsm.order',
            'view_mode': 'tree,form',
            'domain': [('equipment_ids', 'in', [self.id])],
            'context': {'default_equipment_ids': [(6, 0, [self.id])]}
        }

    def action_schedule_maintenance(self):
        """Programar mantenimiento"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Programar Mantenimiento - {self.name}',
            'res_model': 'daruclima.fsm.order',
            'view_mode': 'form',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_location_id': self.location_id.id,
                'default_equipment_ids': [(6, 0, [self.id])],
                'default_description': f'Mantenimiento preventivo de {self.name}',
            }
        }

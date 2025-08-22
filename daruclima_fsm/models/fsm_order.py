# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class DaruclimeFSMOrder(models.Model):
    _name = 'daruclima.fsm.order'
    _description = 'Orden de Trabajo'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'priority desc, date_scheduled asc, id desc'
    _rec_name = 'name'

    # Campos básicos
    name = fields.Char(
        string='Número',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nuevo'),
        tracking=True
    )

    # Información del cliente y ubicación
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True,
        help="Cliente para quien se realiza el servicio"
    )
    location_id = fields.Many2one(
        'daruclima.fsm.location',
        string='Ubicación del Servicio',
        tracking=True,
        help="Ubicación donde se realizará el servicio"
    )
    contact_id = fields.Many2one(
        'res.partner',
        string='Persona de Contacto',
        domain="[('parent_id', '=', partner_id), ('is_company', '=', False)]",
        help="Persona de contacto en la ubicación del servicio"
    )

    # Información del servicio
    description = fields.Text(
        string='Descripción del Trabajo',
        required=True,
        tracking=True
    )
    internal_note = fields.Text(
        string='Notas Internas',
        help="Notas internas no visibles para el cliente"
    )
    customer_note = fields.Text(
        string='Notas del Cliente',
        help="Notas visibles para el cliente"
    )

    # Gestión de estados y prioridades
    stage_id = fields.Many2one(
        'daruclima.fsm.stage',
        string='Etapa',
        required=True,
        tracking=True,
        group_expand='_read_group_stage_ids',
        default=lambda self: self._get_default_stage()
    )
    priority = fields.Selection([
        ('0', 'Muy Baja'),
        ('1', 'Baja'),
        ('2', 'Normal'),
        ('3', 'Alta'),
        ('4', 'Muy Alta'),
        ('5', 'Urgente')
    ], string='Prioridad', default='2', tracking=True)

    color = fields.Char(string='Color', related='stage_id.color', store=True)
    is_closed = fields.Boolean(string='Cerrado', related='stage_id.is_closed', store=True)

    # Fechas y tiempo
    date_created = fields.Datetime(
        string='Fecha de Creación',
        default=fields.Datetime.now,
        readonly=True
    )
    date_scheduled = fields.Datetime(
        string='Fecha Programada',
        tracking=True,
        help="Fecha y hora programada para el servicio"
    )
    date_start = fields.Datetime(
        string='Fecha de Inicio',
        tracking=True
    )
    date_end = fields.Datetime(
        string='Fecha de Finalización',
        tracking=True
    )
    duration = fields.Float(
        string='Duración (Horas)',
        compute='_compute_duration',
        store=True,
        help="Duración del trabajo en horas"
    )

    # Equipo y técnicos
    team_id = fields.Many2one(
        'daruclima.fsm.team',
        string='Equipo',
        required=True,
        default=lambda self: self._get_default_team(),
        tracking=True
    )
    person_ids = fields.Many2many(
        'daruclima.fsm.person',
        string='Técnicos Asignados',
        tracking=True
    )
    responsible_id = fields.Many2one(
        'daruclima.fsm.person',
        string='Técnico Responsable',
        tracking=True
    )

    # Equipos y servicios
    equipment_ids = fields.Many2many(
        'daruclima.fsm.equipment',
        string='Equipos a Revisar/Reparar',
        help="Equipos que serán revisados o reparados"
    )
    tag_ids = fields.Many2many(
        'daruclima.fsm.tag',
        string='Etiquetas',
        help="Etiquetas para clasificar y analizar órdenes"
    )

    # Integración con ventas
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        help="Orden de venta relacionada"
    )
    sale_line_ids = fields.One2many(
        'sale.order.line',
        'fsm_order_id',
        string='Líneas de Venta'
    )

    # Materiales y stock
    material_ids = fields.One2many(
        'daruclima.fsm.material',
        'order_id',
        string='Materiales Utilizados'
    )
    stock_picking_ids = fields.One2many(
        'stock.picking',
        'fsm_order_id',
        string='Movimientos de Stock'
    )

    # Hojas de tiempo
    timesheet_ids = fields.One2many(
        'account.analytic.line',
        'fsm_order_id',
        string='Hojas de Tiempo'
    )

    # Reparaciones
    repair_ids = fields.One2many(
        'repair.order',
        'fsm_order_id',
        string='Órdenes de Reparación'
    )

    # Campos de conteo para botones estadísticos
    repair_count = fields.Integer(
        string='Número de Reparaciones',
        compute='_compute_repair_count'
    )
    quotation_count = fields.Integer(
        string='Número de Presupuestos',
        compute='_compute_quotation_count'
    )

    # Facturación
    invoice_status = fields.Selection([
        ('no', 'Sin Facturar'),
        ('partial', 'Parcialmente Facturado'),
        ('invoiced', 'Facturado')
    ], string='Estado de Facturación', compute='_compute_invoice_status', store=True)

    invoice_ids = fields.Many2many(
        'account.move',
        string='Facturas',
        copy=False
    )

    # Totales
    total_cost = fields.Monetary(
        string='Costo Total',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    total_sale = fields.Monetary(
        string='Total de Venta',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    margin = fields.Monetary(
        string='Margen',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    margin_percent = fields.Float(
        string='% Margen',
        compute='_compute_totals',
        store=True
    )

    # Campos de empresa y moneda
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True
    )

    # Portal
    access_url = fields.Char(
        string='URL de Acceso',
        compute='_compute_access_url'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code('daruclima.fsm.order') or _('Nuevo')
            # Garantizar etapa por defecto si no viene informada
            if not vals.get('stage_id'):
                vals['stage_id'] = self._get_default_stage()
        return super().create(vals_list)

    def _get_default_stage(self):
        """Obtiene la etapa por defecto de forma robusta y devuelve su id"""
        Stage = self.env['daruclima.fsm.stage'].sudo()
        # Primero intentar buscar una etapa marcada como por defecto
        stage = Stage.search([
            ('is_default', '=', True),
            ('company_id', 'in', [self.env.company.id, False])
        ], limit=1)

        # Si no hay etapa por defecto, buscar por código 'new'
        if not stage:
            stage = Stage.search([
                ('code', '=', 'new'),
                ('company_id', 'in', [self.env.company.id, False])
            ], limit=1)

        # Si tampoco existe, tomar la primera etapa disponible
        if not stage:
            stage = Stage.search([
                ('company_id', 'in', [self.env.company.id, False])
            ], limit=1)

        # Si no hay ninguna etapa, crear una básica
        if not stage:
            stage = Stage.create({
                'name': 'Nuevo',
                'code': 'new',
                'sequence': 1,
                'is_default': True,
                'is_closed': False,
                'color': '#E6E6FA',
                'company_id': self.env.company.id
            })

        # Devolver id para compatibilidad con default de Many2one
        return stage.id

    def _get_default_team(self):
        """Obtiene el equipo por defecto - Método mejorado"""
        # Buscar el primer equipo disponible para la empresa
        team = self.env['daruclima.fsm.team'].search([
            ('company_id', 'in', [self.env.company.id, False])
        ], limit=1)

        # Si no hay ningún equipo, crear uno básico
        if not team:
            team = self.env['daruclima.fsm.team'].create({
                'name': 'Equipo Principal',
                'code': 'MAIN',
                'sequence': 1,
                'description': 'Equipo principal de órdenes de trabajo',
                'company_id': self.env.company.id
            })

        return team

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        """Calcula la duración del trabajo"""
        for record in self:
            if record.date_start and record.date_end:
                delta = record.date_end - record.date_start
                record.duration = delta.total_seconds() / 3600
            else:
                record.duration = 0.0

    @api.depends('sale_line_ids', 'material_ids', 'timesheet_ids')
    def _compute_totals(self):
        """Calcula los totales de costo, venta y margen"""
        for record in self:
            total_cost = sum(record.material_ids.mapped('cost_total'))
            total_cost += sum(record.timesheet_ids.mapped('amount'))

            total_sale = sum(record.sale_line_ids.mapped('price_subtotal'))

            record.total_cost = total_cost
            record.total_sale = total_sale
            record.margin = total_sale - total_cost
            record.margin_percent = (record.margin / total_sale * 100) if total_sale else 0.0

    @api.depends('invoice_ids', 'sale_line_ids')
    def _compute_invoice_status(self):
        """Calcula el estado de facturación"""
        for record in self:
            if not record.sale_line_ids:
                record.invoice_status = 'no'
            elif all(line.invoice_status == 'invoiced' for line in record.sale_line_ids):
                record.invoice_status = 'invoiced'
            elif any(line.invoice_status == 'invoiced' for line in record.sale_line_ids):
                record.invoice_status = 'partial'
            else:
                record.invoice_status = 'no'

    def _compute_access_url(self):
        """Calcula la URL de acceso al portal"""
        for record in self:
            record.access_url = f'/my/fsm/{record.id}'

    @api.model
    def _read_group_stage_ids(self, stages, domain, order=None):
        """Expande las etapas en vista kanban - Método corregido para Odoo 18"""
        # Obtener todas las etapas disponibles para la empresa actual
        search_domain = [('company_id', 'in', [self.env.company.id, False])]
        stage_ids = self.env['daruclima.fsm.stage'].search(search_domain, order=order or 'sequence, id')
        return stage_ids

    def action_start_work(self):
        """Inicia el trabajo"""
        self.ensure_one()
        if not self.date_start:
            self.write({
                'date_start': fields.Datetime.now(),
                'stage_id': self.env['daruclima.fsm.stage'].search([
                    ('code', '=', 'in_progress'),
                    ('company_id', 'in', [self.env.company.id, False])
                ], limit=1).id
            })

    def action_end_work(self):
        """Finaliza el trabajo"""
        self.ensure_one()
        if not self.date_end:
            self.write({
                'date_end': fields.Datetime.now(),
                'stage_id': self.env['daruclima.fsm.stage'].search([
                    ('code', '=', 'done'),
                    ('company_id', 'in', [self.env.company.id, False])
                ], limit=1).id
            })

    def action_create_invoice(self):
        """Abre el wizard para crear factura"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crear Factura',
            'res_model': 'daruclima.fsm.create.invoice',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_fsm_order_id': self.id}
        }

    def action_request_materials(self):
        """Abre el wizard para solicitar materiales"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Solicitar Materiales',
            'res_model': 'daruclima.fsm.material.request',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_fsm_order_id': self.id}
        }

    def action_view_attachments(self):
        """Abrir vista de adjuntos para esta orden FSM"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Adjuntos',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('res_model', '=', 'daruclima.fsm.order'), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': 'daruclima.fsm.order',
                'default_res_id': self.id,
            }
        }

    def action_view_fsm_order(self):
        """Abrir la Orden de Venta relacionada desde la orden FSM."""
        self.ensure_one()
        if not self.sale_order_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
        }

    @api.depends('repair_ids')
    def _compute_repair_count(self):
        """Calcula el número de órdenes de reparación"""
        for record in self:
            record.repair_count = len(record.repair_ids)

    @api.depends('sale_order_id')
    def _compute_quotation_count(self):
        """Calcula el número de presupuestos/órdenes de venta"""
        for record in self:
            # Contar órdenes de venta en estado de presupuesto
            quotations = self.env['sale.order'].search([
                ('partner_id', '=', record.partner_id.id),
                ('state', 'in', ['draft', 'sent']),
                ('fsm_order_id', '=', record.id)
            ])
            record.quotation_count = len(quotations)

    def action_create_repair_order(self):
        """Crea una orden de reparación a partir de la orden de servicio"""
        self.ensure_one()

        # Verificar si ya existe una orden de reparación
        existing_repair = self.env['repair.order'].search([
            ('fsm_order_id', '=', self.id)
        ], limit=1)

        if existing_repair:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Orden de Reparación',
                'res_model': 'repair.order',
                'res_id': existing_repair.id,
                'view_mode': 'form',
                'target': 'current',
            }

        # Preparar valores para la orden de reparación (solo campos que existen)
        repair_vals = {
            'partner_id': self.partner_id.id,
            'fsm_order_id': self.id,
            'internal_notes': f"<p><strong>Orden FSM:</strong> {self.name}</p>" +
                            f"<p><strong>Descripción:</strong> {self.description or ''}</p>" +
                            (f"<p><strong>Notas internas:</strong> {self.internal_note}</p>" if self.internal_note else "") +
                            (f"<p><strong>Notas del cliente:</strong> {self.customer_note}</p>" if self.customer_note else ""),
            'company_id': self.company_id.id,
        }

        # Si hay equipos definidos, tomar el primero como producto a reparar
        if self.equipment_ids:
            equipment = self.equipment_ids[0]
            if hasattr(equipment, 'product_id') and equipment.product_id:
                repair_vals['product_id'] = equipment.product_id.id
                repair_vals['product_qty'] = 1.0
                repair_vals['product_uom'] = equipment.product_id.uom_id.id

        # Crear la orden de reparación
        repair_order = self.env['repair.order'].create(repair_vals)

        # Añadir materiales como operaciones de reparación
        for material in self.material_ids:
            self.env['repair.line'].create({
                'repair_id': repair_order.id,
                'type': 'add',
                'product_id': material.product_id.id,
                'product_uom_qty': material.quantity,
                'product_uom': material.product_id.uom_id.id,
                'price_unit': material.cost_unit,
                'name': material.product_id.name,
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Orden de Reparación',
            'res_model': 'repair.order',
            'res_id': repair_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_quotation(self):
        """Crea un presupuesto a partir de la orden de servicio"""
        self.ensure_one()

        # Si ya existe una orden de venta/presupuesto, abrirla
        if self.sale_order_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Presupuesto',
                'res_model': 'sale.order',
                'res_id': self.sale_order_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

        # Preparar valores para el presupuesto (siempre en estado borrador)
        quotation_vals = {
            'partner_id': self.partner_id.id,
            'fsm_order_id': self.id,
            'origin': self.name,
            'note': self.customer_note or '',
            'company_id': self.company_id.id,
            'date_order': fields.Datetime.now(),
            'state': 'draft',  # Asegurar que se crea como presupuesto
        }

        # Crear el presupuesto
        quotation = self.env['sale.order'].create(quotation_vals)

        # Añadir líneas basadas en los materiales utilizados
        for material in self.material_ids:
            self.env['sale.order.line'].create({
                'order_id': quotation.id,
                'product_id': material.product_id.id,
                'product_uom_qty': material.quantity,
                'product_uom': material.product_id.uom_id.id,
                'price_unit': material.product_id.list_price,
                'name': material.product_id.name,
            })

        # Añadir línea de servicio si no hay materiales
        if not self.material_ids:
            # Buscar un producto de servicio genérico o crear línea manual
            service_product = self.env['product.product'].search([
                ('type', '=', 'service'),
                ('name', 'ilike', 'servicio')
            ], limit=1)

            if service_product:
                self.env['sale.order.line'].create({
                    'order_id': quotation.id,
                    'product_id': service_product.id,
                    'product_uom_qty': 1.0,
                    'product_uom': service_product.uom_id.id,
                    'price_unit': service_product.list_price,
                    'name': f"Servicio - {self.description[:50]}...",
                })
            else:
                # Crear línea manual de servicio
                self.env['sale.order.line'].create({
                    'order_id': quotation.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 0.0,
                    'name': f"Servicio de Campo - {self.description[:50]}...",
                })

        # Actualizar la referencia en la orden FSM
        self.sale_order_id = quotation.id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Presupuesto',
            'res_model': 'sale.order',
            'res_id': quotation.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_repair_orders(self):
        """Ver todas las órdenes de reparación relacionadas"""
        self.ensure_one()
        action = self.env.ref('repair.action_repair_order_tree').read()[0]

        if len(self.repair_ids) > 1:
            action['domain'] = [('id', 'in', self.repair_ids.ids)]
        elif self.repair_ids:
            action['views'] = [(self.env.ref('repair.view_repair_order_form').id, 'form')]
            action['res_id'] = self.repair_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action

    def action_view_quotations(self):
        """Ver todos los presupuestos relacionados"""
        self.ensure_one()
        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]

        quotations = self.env['sale.order'].search([
            ('partner_id', '=', self.partner_id.id),
            ('fsm_order_id', '=', self.id)
        ])

        if len(quotations) > 1:
            action['domain'] = [('id', 'in', quotations.ids)]
        elif quotations:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = quotations.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action


class DaruclimeFSMMaterial(models.Model):
    _name = 'daruclima.fsm.material'
    _description = 'Material utilizado en orden de servicio'

    order_id = fields.Many2one(
        'daruclima.fsm.order',
        string='Orden de Servicio',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        required=True
    )
    quantity = fields.Float(
        string='Cantidad',
        default=1.0,
        required=True
    )
    cost_unit = fields.Monetary(
        string='Costo Unitario',
        currency_field='currency_id'
    )
    cost_total = fields.Monetary(
        string='Costo Total',
        compute='_compute_cost_total',
        store=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='order_id.currency_id'
    )

    @api.depends('quantity', 'cost_unit')
    def _compute_cost_total(self):
        for record in self:
            record.cost_total = record.quantity * record.cost_unit

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.cost_unit = self.product_id.standard_price

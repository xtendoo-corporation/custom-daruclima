# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from odoo import fields


class TestDaruclimeFSMIntegration(TransactionCase):
    """Test cases para integración completa del sistema FSM"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Configurar datos completos para tests de integración
        cls.partner = cls.env['res.partner'].create({
            'name': 'Cliente Integración Test',
            'email': 'integracion@test.com',
            'phone': '+34 123 456 789',
        })

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Técnico Integración',
            'work_email': 'tecnico@test.com',
        })

        cls.team = cls.env['daruclima.fsm.team'].create({
            'name': 'Equipo Integración',
            'code': 'INTEG',
        })

        cls.person = cls.env['daruclima.fsm.person'].create({
            'name': 'Técnico FSM Integración',
            'employee_id': cls.employee.id,
            'team_id': cls.team.id,
        })

        cls.location = cls.env['daruclima.fsm.location'].create({
            'name': 'Ubicación Integración',
            'partner_id': cls.partner.id,
            'street': 'Calle Integración 123',
            'city': 'Madrid',
        })

        cls.equipment = cls.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Integración',
            'partner_id': cls.partner.id,
            'location_id': cls.location.id,
            'brand': 'Test Brand',
            'model': 'Test Model',
        })

        cls.product_service = cls.env['product.product'].create({
            'name': 'Servicio de Reparación',
            'type': 'service',
            'is_fsm_service': True,
            'list_price': 100.0,
        })

        cls.product_material = cls.env['product.product'].create({
            'name': 'Material de Reparación',
            'type': 'product',
            'is_fsm_material': True,
            'standard_price': 50.0,
            'list_price': 75.0,
        })

        cls.stage_new = cls.env['daruclima.fsm.stage'].create({
            'name': 'Nuevo',
            'code': 'new',
            'is_default': True,
        })

        cls.stage_done = cls.env['daruclima.fsm.stage'].create({
            'name': 'Completado',
            'code': 'done',
            'is_closed': True,
        })

        cls.tag_urgent = cls.env['daruclima.fsm.tag'].create({
            'name': 'Urgente',
            'color': 1,
        })

    def test_complete_fsm_workflow(self):
        """Test del workflow completo FSM"""
        # 1. Crear orden de servicio
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'location_id': self.location.id,
            'team_id': self.team.id,
            'responsible_id': self.person.id,
            'description': 'Reparación completa del equipo',
            'equipment_ids': [(6, 0, [self.equipment.id])],
            'tag_ids': [(6, 0, [self.tag_urgent.id])],
            'date_scheduled': fields.Datetime.now() + timedelta(hours=2),
        })

        # Verificar creación
        self.assertTrue(order.name)
        self.assertEqual(order.stage_id, self.stage_new)

        # 2. Añadir materiales
        material = self.env['daruclima.fsm.material'].create({
            'order_id': order.id,
            'product_id': self.product_material.id,
            'quantity': 2.0,
            'cost_unit': self.product_material.standard_price,
        })

        # 3. Iniciar trabajo
        order.action_start_work()
        self.assertTrue(order.date_start)

        # 4. Crear orden de venta
        order.action_create_sale_order()
        self.assertTrue(order.sale_order_id)

        # Añadir líneas de servicio
        sale_line = self.env['sale.order.line'].create({
            'order_id': order.sale_order_id.id,
            'product_id': self.product_service.id,
            'product_uom_qty': 3.0,
            'price_unit': self.product_service.list_price,
            'fsm_order_id': order.id,
        })

        # 5. Finalizar trabajo
        order.action_end_work()
        self.assertTrue(order.date_end)

        # 6. Verificar cálculos
        expected_cost = material.cost_total
        expected_sale = sale_line.price_subtotal

        self.assertEqual(order.total_cost, expected_cost)
        self.assertEqual(order.total_sale, expected_sale)
        self.assertEqual(order.margin, expected_sale - expected_cost)

    def test_sale_integration(self):
        """Test integración con módulo de ventas"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test integración ventas',
        })

        # Crear orden de venta
        result = order.action_create_sale_order()
        sale_order = order.sale_order_id

        # Verificar integración
        self.assertTrue(sale_order)
        self.assertEqual(sale_order.partner_id, self.partner)
        self.assertEqual(sale_order.fsm_order_id, order)
        self.assertTrue(sale_order.is_fsm_order)

        # Verificar acción de retorno
        self.assertEqual(result['res_model'], 'sale.order')
        self.assertEqual(result['res_id'], sale_order.id)

    def test_stock_integration(self):
        """Test integración con gestión de stock"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test integración stock',
        })

        # Crear movimiento de stock
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.env.ref('stock.stock_location_stock').id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'fsm_order_id': order.id,
        })

        # Verificar integración
        self.assertEqual(picking.fsm_order_id, order)
        self.assertIn(picking, order.stock_picking_ids)

    def test_timesheet_integration(self):
        """Test integración con hojas de tiempo"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test integración timesheet',
        })

        # Crear proyecto para timesheet
        project = self.env['project.project'].create({
            'name': 'Proyecto FSM Test',
            'allow_timesheets': True,
        })

        # Crear línea de timesheet
        timesheet = self.env['account.analytic.line'].create({
            'name': 'Trabajo realizado',
            'employee_id': self.employee.id,
            'project_id': project.id,
            'unit_amount': 4.0,
            'amount': -200.0,
            'fsm_order_id': order.id,
        })

        # Verificar integración
        self.assertEqual(timesheet.fsm_order_id, order)
        self.assertTrue(timesheet.is_fsm_timesheet)
        self.assertIn(timesheet, order.timesheet_ids)

    def test_repair_integration(self):
        """Test integración con órdenes de reparación"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test integración reparación',
        })

        # Crear orden de reparación
        repair = self.env['repair.order'].create({
            'partner_id': self.partner.id,
            'product_id': self.product_material.id,
            'fsm_order_id': order.id,
            'fsm_equipment_id': self.equipment.id,
        })

        # Verificar integración
        self.assertEqual(repair.fsm_order_id, order)
        self.assertEqual(repair.fsm_equipment_id, self.equipment)
        self.assertIn(repair, order.repair_ids)

    def test_partner_fsm_integration(self):
        """Test integración FSM en contactos"""
        # Verificar que el partner tiene datos FSM
        self.assertEqual(self.partner.fsm_location_count, 1)
        self.assertEqual(self.partner.fsm_equipment_count, 1)

        # Crear orden FSM
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test partner integration',
        })

        # Verificar estadísticas actualizadas
        self.assertEqual(self.partner.fsm_order_count, 1)

        # Test acciones del partner
        action = self.partner.action_view_fsm_orders()
        self.assertEqual(action['res_model'], 'daruclima.fsm.order')
        self.assertIn(('partner_id', '=', self.partner.id), action['domain'])

    def test_product_fsm_integration(self):
        """Test integración FSM en productos"""
        # Verificar campos FSM en productos
        self.assertTrue(self.product_service.is_fsm_service)
        self.assertTrue(self.product_material.is_fsm_material)

        # Verificar herencia en product.product
        self.assertTrue(self.product_service.is_fsm_service)
        self.assertTrue(self.product_material.is_fsm_material)

    def test_project_fsm_integration(self):
        """Test integración con proyectos"""
        # Crear proyecto FSM
        project = self.env['project.project'].create({
            'name': 'Proyecto FSM',
            'is_fsm': True,
            'fsm_team_id': self.team.id,
        })

        # Crear tarea FSM
        task = self.env['project.task'].create({
            'name': 'Tarea FSM',
            'project_id': project.id,
        })

        # Verificar integración
        self.assertTrue(project.is_fsm)
        self.assertEqual(project.fsm_team_id, self.team)
        self.assertTrue(task.is_fsm_task)

    def test_multi_company_support(self):
        """Test soporte multi-compañía"""
        company2 = self.env['res.company'].create({
            'name': 'Compañía 2',
        })

        # Crear datos para la segunda compañía
        team2 = self.env['daruclima.fsm.team'].create({
            'name': 'Equipo Compañía 2',
            'code': 'COMP2',
            'company_id': company2.id,
        })

        stage2 = self.env['daruclima.fsm.stage'].create({
            'name': 'Etapa Compañía 2',
            'code': 'comp2_stage',
            'company_id': company2.id,
        })

        # Verificar aislamiento por compañía
        self.assertNotEqual(self.team.company_id, team2.company_id)
        self.assertNotEqual(self.stage_new.company_id, stage2.company_id)

    def test_portal_access(self):
        """Test acceso al portal del cliente"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test portal access',
        })

        # Verificar URL de acceso
        self.assertTrue(order.access_url)
        self.assertIn('/my/fsm/', order.access_url)
        self.assertIn(str(order.id), order.access_url)

    def test_security_rules(self):
        """Test reglas de seguridad"""
        # Crear usuario FSM básico
        user_fsm = self.env['res.users'].create({
            'name': 'Usuario FSM',
            'login': 'fsm_user',
            'groups_id': [(6, 0, [self.env.ref('daruclima_fsm.group_fsm_user').id])],
        })

        # Crear técnico para este usuario
        employee_fsm = self.env['hr.employee'].create({
            'name': 'Empleado FSM',
            'user_id': user_fsm.id,
        })

        person_fsm = self.env['daruclima.fsm.person'].create({
            'name': 'Técnico Usuario',
            'employee_id': employee_fsm.id,
            'team_id': self.team.id,
        })

        # Crear orden asignada a este técnico
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test seguridad',
            'person_ids': [(6, 0, [person_fsm.id])],
        })

        # Verificar que el usuario puede ver sus órdenes
        orders_user = self.env['daruclima.fsm.order'].with_user(user_fsm).search([
            ('person_ids.user_id', '=', user_fsm.id)
        ])

        self.assertIn(order, orders_user)

    def test_invoice_status_calculation(self):
        """Test cálculo de estado de facturación"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test facturación',
        })

        # Sin líneas de venta
        self.assertEqual(order.invoice_status, 'no')

        # Crear orden de venta
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_order_id': order.id,
        })

        line1 = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product_service.id,
            'product_uom_qty': 1.0,
            'price_unit': 100.0,
            'fsm_order_id': order.id,
        })

        # Con líneas sin facturar
        self.assertEqual(order.invoice_status, 'no')

    def test_equipment_maintenance_workflow(self):
        """Test workflow completo de mantenimiento de equipos"""
        # Programar mantenimiento desde el equipo
        action = self.equipment.action_schedule_maintenance()

        # Verificar que la acción crea una nueva orden
        self.assertEqual(action['res_model'], 'daruclima.fsm.order')
        self.assertIn('default_equipment_ids', action['context'])

        # Crear orden de mantenimiento
        maintenance_order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'location_id': self.location.id,
            'team_id': self.team.id,
            'description': 'Mantenimiento preventivo programado',
            'equipment_ids': [(6, 0, [self.equipment.id])],
        })

        # Verificar asociación
        self.assertIn(self.equipment, maintenance_order.equipment_ids)
        self.assertIn(maintenance_order, self.equipment.order_ids)

    def test_complete_end_to_end_scenario(self):
        """Test escenario completo de extremo a extremo"""
        # 1. Cliente solicita servicio
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'location_id': self.location.id,
            'team_id': self.team.id,
            'description': 'Reparación urgente del aire acondicionado',
            'equipment_ids': [(6, 0, [self.equipment.id])],
            'tag_ids': [(6, 0, [self.tag_urgent.id])],
            'priority': '4',
            'date_scheduled': fields.Datetime.now() + timedelta(hours=4),
        })

        # 2. Asignar técnico
        order.write({
            'person_ids': [(6, 0, [self.person.id])],
            'responsible_id': self.person.id,
        })

        # 3. Técnico inicia trabajo
        order.action_start_work()

        # 4. Añadir materiales utilizados
        self.env['daruclima.fsm.material'].create({
            'order_id': order.id,
            'product_id': self.product_material.id,
            'quantity': 1.0,
            'cost_unit': 50.0,
        })

        # 5. Registrar tiempo trabajado
        project = self.env['project.project'].create({
            'name': 'Servicios FSM',
            'allow_timesheets': True,
        })

        self.env['account.analytic.line'].create({
            'name': 'Reparación realizada',
            'employee_id': self.employee.id,
            'project_id': project.id,
            'unit_amount': 2.5,
            'amount': -125.0,
            'fsm_order_id': order.id,
        })

        # 6. Crear orden de venta para facturación
        order.action_create_sale_order()

        # Añadir servicios facturables
        self.env['sale.order.line'].create({
            'order_id': order.sale_order_id.id,
            'product_id': self.product_service.id,
            'product_uom_qty': 2.5,
            'price_unit': 80.0,
            'fsm_order_id': order.id,
        })

        # 7. Finalizar trabajo
        order.action_end_work()

        # 8. Verificar estado final
        self.assertTrue(order.date_start)
        self.assertTrue(order.date_end)
        self.assertGreater(order.duration, 0)
        self.assertEqual(order.total_cost, 175.0)  # 50 material + 125 tiempo
        self.assertEqual(order.total_sale, 200.0)  # 2.5h * 80€/h
        self.assertEqual(order.margin, 25.0)

        # 9. Cambiar a completado
        order.stage_id = self.stage_done
        self.assertTrue(order.is_closed)

        # Verificar toda la integración funciona correctamente
        self.assertTrue(all([
            order.partner_id == self.partner,
            order.location_id == self.location,
            order.equipment_ids,
            order.person_ids,
            order.sale_order_id,
            order.material_ids,
            order.timesheet_ids,
            order.is_closed,
        ]))

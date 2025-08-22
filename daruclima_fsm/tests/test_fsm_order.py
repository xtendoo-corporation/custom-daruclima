# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from odoo import fields


class TestDaruclimeFSMOrder(TransactionCase):
    """Test cases para órdenes de servicio FSM"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Crear datos de prueba
        cls.partner = cls.env['res.partner'].create({
            'name': 'Cliente Test FSM',
            'email': 'test@daruclima.com',
            'phone': '123456789',
        })

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Técnico Test',
            'work_email': 'tecnico@daruclima.com',
        })

        cls.team = cls.env['daruclima.fsm.team'].create({
            'name': 'Equipo Test',
            'code': 'TEST',
        })

        cls.person = cls.env['daruclima.fsm.person'].create({
            'name': 'Técnico FSM Test',
            'employee_id': cls.employee.id,
            'team_id': cls.team.id,
        })

        cls.location = cls.env['daruclima.fsm.location'].create({
            'name': 'Ubicación Test',
            'partner_id': cls.partner.id,
            'street': 'Calle Test 123',
            'city': 'Madrid',
        })

        cls.stage_new = cls.env['daruclima.fsm.stage'].create({
            'name': 'Nuevo Test',
            'code': 'new_test',
            'sequence': 1,
            'is_default': True,
        })

        cls.stage_done = cls.env['daruclima.fsm.stage'].create({
            'name': 'Completado Test',
            'code': 'done_test',
            'sequence': 2,
            'is_closed': True,
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Material Test',
            'type': 'product',
            'standard_price': 100.0,
        })

    def test_order_creation(self):
        """Test creación de orden FSM"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test de reparación',
        })

        # Verificar que se asignó número automáticamente
        self.assertTrue(order.name)
        self.assertNotEqual(order.name, 'Nuevo')

        # Verificar etapa por defecto
        self.assertEqual(order.stage_id, self.stage_new)

        # Verificar estado inicial
        self.assertFalse(order.is_closed)
        self.assertEqual(order.priority, '2')

    def test_order_workflow(self):
        """Test del workflow de órdenes FSM"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test workflow',
            'responsible_id': self.person.id,
        })

        # Test iniciar trabajo
        self.assertFalse(order.date_start)
        order.action_start_work()
        self.assertTrue(order.date_start)

        # Test finalizar trabajo
        self.assertFalse(order.date_end)
        order.action_end_work()
        self.assertTrue(order.date_end)

        # Verificar duración calculada
        self.assertGreater(order.duration, 0)

    def test_order_materials(self):
        """Test gestión de materiales en órdenes"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test materiales',
        })

        # Añadir material
        material = self.env['daruclima.fsm.material'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'quantity': 2.0,
            'cost_unit': 100.0,
        })

        # Verificar cálculo de costo total
        self.assertEqual(material.cost_total, 200.0)

        # Verificar cálculo en orden
        self.assertEqual(order.total_cost, 200.0)

    def test_order_sale_integration(self):
        """Test integración con ventas"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test ventas',
        })

        # Crear orden de venta
        result = order.action_create_sale_order()

        # Verificar que se creó la orden de venta
        self.assertTrue(order.sale_order_id)
        self.assertEqual(order.sale_order_id.partner_id, self.partner)
        self.assertEqual(order.sale_order_id.origin, order.name)

    def test_order_stage_changes(self):
        """Test cambios de etapa"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test etapas',
        })

        # Cambiar a etapa cerrada
        order.stage_id = self.stage_done

        # Verificar que se marca como cerrada
        self.assertTrue(order.is_closed)

    def test_order_required_fields(self):
        """Test campos requeridos"""
        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.order'].create({
                'description': 'Test sin cliente',
            })

        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.order'].create({
                'partner_id': self.partner.id,
            })

    def test_order_totals_calculation(self):
        """Test cálculo de totales"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test totales',
        })

        # Añadir materiales
        self.env['daruclima.fsm.material'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'quantity': 1.0,
            'cost_unit': 50.0,
        })

        # Crear orden de venta con líneas
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'fsm_order_id': order.id,
        })

        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1.0,
            'price_unit': 150.0,
            'fsm_order_id': order.id,
        })

        order.sale_order_id = sale_order.id

        # Verificar cálculos
        self.assertEqual(order.total_cost, 50.0)
        self.assertEqual(order.total_sale, 150.0)
        self.assertEqual(order.margin, 100.0)
        self.assertAlmostEqual(order.margin_percent, 66.67, places=1)

    def test_order_date_validation(self):
        """Test validación de fechas"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test fechas',
            'date_start': fields.Datetime.now(),
            'date_end': fields.Datetime.now() - timedelta(hours=1),
        })

        # La duración debería ser negativa (caso inválido)
        self.assertLess(order.duration, 0)

    def test_order_portal_access(self):
        """Test acceso al portal"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test portal',
        })

        # Verificar URL de acceso
        self.assertTrue(order.access_url)
        self.assertIn(str(order.id), order.access_url)

    def test_order_assignment(self):
        """Test asignación de técnicos"""
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test asignación',
            'person_ids': [(6, 0, [self.person.id])],
            'responsible_id': self.person.id,
        })

        # Verificar asignación
        self.assertIn(self.person, order.person_ids)
        self.assertEqual(order.responsible_id, self.person)

    def test_order_equipment_tracking(self):
        """Test seguimiento de equipos"""
        equipment = self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Test',
            'partner_id': self.partner.id,
            'location_id': self.location.id,
        })

        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Test equipos',
            'equipment_ids': [(6, 0, [equipment.id])],
        })

        # Verificar asociación
        self.assertIn(equipment, order.equipment_ids)
        self.assertIn(order, equipment.order_ids)

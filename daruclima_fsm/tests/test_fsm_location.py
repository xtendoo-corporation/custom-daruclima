# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestDaruclimeFSMLocation(TransactionCase):
    """Test cases para ubicaciones FSM"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Cliente Ubicaciones',
            'email': 'ubicaciones@test.com',
        })

        cls.contact = cls.env['res.partner'].create({
            'name': 'Contacto Local',
            'parent_id': cls.partner.id,
            'is_company': False,
            'phone': '123456789',
        })

        cls.team = cls.env['daruclima.fsm.team'].create({
            'name': 'Equipo Test',
            'code': 'TEST',
        })

    def test_location_creation(self):
        """Test creación de ubicaciones FSM"""
        location = self.env['daruclima.fsm.location'].create({
            'name': 'Oficina Central Madrid',
            'partner_id': self.partner.id,
            'street': 'Gran Vía 1',
            'city': 'Madrid',
            'zip': '28001',
            'contact_id': self.contact.id,
        })

        self.assertEqual(location.name, 'Oficina Central Madrid')
        self.assertEqual(location.partner_id, self.partner)
        self.assertEqual(location.contact_id, self.contact)
        self.assertEqual(location.street, 'Gran Vía 1')
        self.assertEqual(location.city, 'Madrid')
        self.assertTrue(location.active)

    def test_location_statistics(self):
        """Test estadísticas de ubicaciones"""
        location = self.env['daruclima.fsm.location'].create({
            'name': 'Ubicación Stats',
            'partner_id': self.partner.id,
        })

        # Crear órdenes para la ubicación
        self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'location_id': location.id,
            'team_id': self.team.id,
            'description': 'Orden 1',
        })

        self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'location_id': location.id,
            'team_id': self.team.id,
            'description': 'Orden 2',
        })

        # Crear equipos para la ubicación
        self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo 1',
            'partner_id': self.partner.id,
            'location_id': location.id,
        })

        # Verificar estadísticas
        self.assertEqual(location.order_count, 2)
        self.assertEqual(location.equipment_count, 1)

    def test_location_actions(self):
        """Test acciones de ubicaciones"""
        location = self.env['daruclima.fsm.location'].create({
            'name': 'Ubicación Acciones',
            'partner_id': self.partner.id,
        })

        # Test acción ver órdenes
        action_orders = location.action_view_orders()
        self.assertEqual(action_orders['type'], 'ir.actions.act_window')
        self.assertEqual(action_orders['res_model'], 'daruclima.fsm.order')
        self.assertIn(('location_id', '=', location.id), action_orders['domain'])

        # Test acción ver equipos
        action_equipment = location.action_view_equipment()
        self.assertEqual(action_equipment['type'], 'ir.actions.act_window')
        self.assertEqual(action_equipment['res_model'], 'daruclima.fsm.equipment')
        self.assertIn(('location_id', '=', location.id), action_equipment['domain'])

    def test_location_geolocation(self):
        """Test geolocalización de ubicaciones"""
        location = self.env['daruclima.fsm.location'].create({
            'name': 'Ubicación GPS',
            'partner_id': self.partner.id,
            'partner_latitude': 40.4168,
            'partner_longitude': -3.7038,
        })

        self.assertEqual(location.partner_latitude, 40.4168)
        self.assertEqual(location.partner_longitude, -3.7038)

    def test_location_access_info(self):
        """Test información de acceso"""
        access_instructions = "Código de acceso: 1234. Llamar al timbre 3 veces."

        location = self.env['daruclima.fsm.location'].create({
            'name': 'Ubicación Acceso',
            'partner_id': self.partner.id,
            'access_info': access_instructions,
        })

        self.assertEqual(location.access_info, access_instructions)

    def test_location_required_fields(self):
        """Test campos requeridos de ubicaciones"""
        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.location'].create({
                'name': 'Ubicación sin cliente',
            })

        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.location'].create({
                'partner_id': self.partner.id,
            })


class TestDaruclimeFSMEquipment(TransactionCase):
    """Test cases para equipos FSM"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Cliente Equipos',
        })

        cls.location = cls.env['daruclima.fsm.location'].create({
            'name': 'Ubicación Equipos',
            'partner_id': cls.partner.id,
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Aire Acondicionado',
            'type': 'product',
        })

        cls.team = cls.env['daruclima.fsm.team'].create({
            'name': 'Equipo Test',
            'code': 'TEST',
        })

    def test_equipment_creation(self):
        """Test creación de equipos FSM"""
        equipment = self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Prueba',
            'partner_id': self.partner.id,
            'location_id': self.location.id,
            'code': 'EQ001',
            'brand': 'Samsung',
            'model': 'AR12000',
            'serial_number': 'SN123456789',
        })

        self.assertEqual(equipment.name, 'Equipo Prueba')
        self.assertEqual(equipment.partner_id, self.partner)
        self.assertEqual(equipment.location_id, self.location)
        self.assertEqual(equipment.code, 'EQ001')
        self.assertEqual(equipment.brand, 'Samsung')
        self.assertEqual(equipment.model, 'AR12000')
        self.assertEqual(equipment.status, 'active')
        self.assertTrue(equipment.active)

    def test_equipment_maintenance_calculation(self):
        """Test cálculo de mantenimiento"""
        equipment = self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Mantenimiento',
            'partner_id': self.partner.id,
            'location_id': self.location.id,
            'maintenance_frequency': 90,  # 90 días
            'last_maintenance_date': date.today() - timedelta(days=30),
        })

        # Verificar cálculo de próximo mantenimiento
        expected_date = equipment.last_maintenance_date + timedelta(days=90)
        self.assertEqual(equipment.next_maintenance_date, expected_date)

    def test_equipment_statistics(self):
        """Test estadísticas de equipos"""
        equipment = self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Stats',
            'partner_id': self.partner.id,
            'location_id': self.location.id,
        })

        # Crear órdenes relacionadas con el equipo
        order1 = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Reparación general',
            'equipment_ids': [(6, 0, [equipment.id])],
        })

        order2 = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Mantenimiento preventivo',
            'equipment_ids': [(6, 0, [equipment.id])],
        })

        # Verificar estadísticas
        self.assertEqual(equipment.order_count, 2)
        self.assertEqual(equipment.maintenance_count, 1)  # Una orden contiene "mantenimiento"

    def test_equipment_actions(self):
        """Test acciones de equipos"""
        equipment = self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Acciones',
            'partner_id': self.partner.id,
            'location_id': self.location.id,
        })

        # Test acción ver órdenes
        action_orders = equipment.action_view_orders()
        self.assertEqual(action_orders['type'], 'ir.actions.act_window')
        self.assertEqual(action_orders['res_model'], 'daruclima.fsm.order')
        self.assertIn(('equipment_ids', 'in', [equipment.id]), action_orders['domain'])

        # Test acción programar mantenimiento
        action_maintenance = equipment.action_schedule_maintenance()
        self.assertEqual(action_maintenance['type'], 'ir.actions.act_window')
        self.assertEqual(action_maintenance['res_model'], 'daruclima.fsm.order')
        self.assertIn('default_equipment_ids', action_maintenance['context'])

    def test_equipment_status_workflow(self):
        """Test workflow de estados del equipo"""
        equipment = self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Estado',
            'partner_id': self.partner.id,
            'location_id': self.location.id,
            'status': 'active',
        })

        # Cambiar a mantenimiento
        equipment.status = 'maintenance'
        self.assertEqual(equipment.status, 'maintenance')

        # Cambiar a inactivo
        equipment.status = 'inactive'
        self.assertEqual(equipment.status, 'inactive')

        # Retirar equipo
        equipment.status = 'retired'
        self.assertEqual(equipment.status, 'retired')

    def test_equipment_warranty_tracking(self):
        """Test seguimiento de garantía"""
        warranty_date = date.today() + timedelta(days=365)

        equipment = self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Garantía',
            'partner_id': self.partner.id,
            'location_id': self.location.id,
            'purchase_date': date.today() - timedelta(days=30),
            'installation_date': date.today() - timedelta(days=15),
            'warranty_expiry': warranty_date,
        })

        self.assertEqual(equipment.warranty_expiry, warranty_date)
        self.assertTrue(equipment.warranty_expiry > date.today())

    def test_equipment_product_relation(self):
        """Test relación con productos"""
        equipment = self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Producto',
            'partner_id': self.partner.id,
            'location_id': self.location.id,
            'product_id': self.product.id,
        })

        self.assertEqual(equipment.product_id, self.product)

    def test_equipment_specifications(self):
        """Test especificaciones técnicas"""
        specs = "Potencia: 12000 BTU\nVoltaje: 220V\nFrecuencia: 50Hz"
        manual_url = "https://manual.example.com/ar12000"

        equipment = self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Specs',
            'partner_id': self.partner.id,
            'location_id': self.location.id,
            'specifications': specs,
            'manual_url': manual_url,
        })

        self.assertEqual(equipment.specifications, specs)
        self.assertEqual(equipment.manual_url, manual_url)

    def test_equipment_required_fields(self):
        """Test campos requeridos de equipos"""
        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.equipment'].create({
                'name': 'Equipo sin cliente',
                'location_id': self.location.id,
            })

        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.equipment'].create({
                'partner_id': self.partner.id,
                'location_id': self.location.id,
            })

    def test_equipment_maintenance_frequency_validation(self):
        """Test validación de frecuencia de mantenimiento"""
        equipment = self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Frecuencia',
            'partner_id': self.partner.id,
            'location_id': self.location.id,
            'maintenance_frequency': 0,
        })

        # Con frecuencia 0, no debería calcular próximo mantenimiento
        self.assertFalse(equipment.next_maintenance_date)

    def test_equipment_order_association(self):
        """Test asociación con órdenes FSM"""
        equipment = self.env['daruclima.fsm.equipment'].create({
            'name': 'Equipo Órdenes',
            'partner_id': self.partner.id,
            'location_id': self.location.id,
        })

        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Trabajo en equipo',
            'equipment_ids': [(6, 0, [equipment.id])],
        })

        # Verificar asociación bidireccional
        self.assertIn(equipment, order.equipment_ids)
        self.assertIn(order, equipment.order_ids)

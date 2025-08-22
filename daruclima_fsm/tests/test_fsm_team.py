# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestDaruclimeFSMTeam(TransactionCase):
    """Test cases para equipos FSM"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Cliente Test',
        })

        cls.employee1 = cls.env['hr.employee'].create({
            'name': 'Técnico 1',
        })

        cls.employee2 = cls.env['hr.employee'].create({
            'name': 'Técnico 2',
        })

    def test_team_creation(self):
        """Test creación de equipos FSM"""
        team = self.env['daruclima.fsm.team'].create({
            'name': 'Equipo Madrid',
            'code': 'MAD',
            'description': 'Equipo de servicios de Madrid',
        })

        self.assertEqual(team.name, 'Equipo Madrid')
        self.assertEqual(team.code, 'MAD')
        self.assertTrue(team.active)
        self.assertEqual(team.sequence, 10)

    def test_team_display_name(self):
        """Test nombre de visualización del equipo"""
        team = self.env['daruclima.fsm.team'].create({
            'name': 'Equipo Test',
            'code': 'TEST',
        })

        # El display_name debe incluir el código
        expected_name = '[TEST] Equipo Test'
        self.assertEqual(team.display_name, expected_name)

    def test_team_statistics(self):
        """Test estadísticas del equipo"""
        team = self.env['daruclima.fsm.team'].create({
            'name': 'Equipo Estadísticas',
            'code': 'STATS',
        })

        # Crear órdenes para el equipo
        stage_new = self.env['daruclima.fsm.stage'].create({
            'name': 'Nuevo',
            'code': 'new',
            'is_closed': False,
        })

        stage_done = self.env['daruclima.fsm.stage'].create({
            'name': 'Completado',
            'code': 'done',
            'is_closed': True,
        })

        # Orden activa
        self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': team.id,
            'stage_id': stage_new.id,
            'description': 'Orden activa',
        })

        # Orden completada
        self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': team.id,
            'stage_id': stage_done.id,
            'description': 'Orden completada',
        })

        # Verificar estadísticas
        self.assertEqual(team.order_count, 2)
        self.assertEqual(team.order_active_count, 1)
        self.assertEqual(team.order_completed_count, 1)

    def test_team_action_view_orders(self):
        """Test acción para ver órdenes del equipo"""
        team = self.env['daruclima.fsm.team'].create({
            'name': 'Equipo Vista',
            'code': 'VIEW',
        })

        action = team.action_view_orders()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'daruclima.fsm.order')
        self.assertIn(('team_id', '=', team.id), action['domain'])

    def test_team_required_fields(self):
        """Test campos requeridos del equipo"""
        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.team'].create({
                'code': 'TEST',
            })

        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.team'].create({
                'name': 'Equipo Sin Código',
            })


class TestDaruclimeFSMPerson(TransactionCase):
    """Test cases para técnicos FSM"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({
            'name': 'Cliente Test',
        })

        cls.team = cls.env['daruclima.fsm.team'].create({
            'name': 'Equipo Test',
            'code': 'TEST',
        })

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Juan Técnico',
            'work_phone': '123456789',
            'mobile_phone': '987654321',
            'work_email': 'juan@daruclima.com',
        })

        cls.user = cls.env['res.users'].create({
            'name': 'Usuario Técnico',
            'login': 'tecnico_test',
            'email': 'tecnico@test.com',
        })

        cls.employee.user_id = cls.user.id

    def test_person_creation(self):
        """Test creación de técnicos FSM"""
        person = self.env['daruclima.fsm.person'].create({
            'name': 'Técnico Test',
            'employee_id': self.employee.id,
            'team_id': self.team.id,
        })

        self.assertEqual(person.name, 'Técnico Test')
        self.assertEqual(person.employee_id, self.employee)
        self.assertEqual(person.team_id, self.team)
        self.assertTrue(person.active)
        self.assertTrue(person.is_available)

    def test_person_related_fields(self):
        """Test campos relacionados del técnico"""
        person = self.env['daruclima.fsm.person'].create({
            'name': 'Técnico Campos',
            'employee_id': self.employee.id,
            'team_id': self.team.id,
        })

        # Verificar campos relacionados del empleado
        self.assertEqual(person.phone, self.employee.work_phone)
        self.assertEqual(person.mobile, self.employee.mobile_phone)
        self.assertEqual(person.email, self.employee.work_email)
        self.assertEqual(person.user_id, self.employee.user_id)

    def test_person_statistics(self):
        """Test estadísticas del técnico"""
        person = self.env['daruclima.fsm.person'].create({
            'name': 'Técnico Stats',
            'employee_id': self.employee.id,
            'team_id': self.team.id,
        })

        stage_new = self.env['daruclima.fsm.stage'].create({
            'name': 'Nuevo',
            'code': 'new',
            'is_closed': False,
        })

        stage_done = self.env['daruclima.fsm.stage'].create({
            'name': 'Completado',
            'code': 'done',
            'is_closed': True,
        })

        # Crear órdenes asignadas al técnico
        order1 = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'stage_id': stage_new.id,
            'description': 'Orden activa',
            'person_ids': [(6, 0, [person.id])],
        })

        order2 = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'stage_id': stage_done.id,
            'description': 'Orden completada',
            'person_ids': [(6, 0, [person.id])],
        })

        # Crear timesheet
        project = self.env['project.project'].create({
            'name': 'Proyecto Test',
            'allow_timesheets': True,
        })

        self.env['account.analytic.line'].create({
            'name': 'Trabajo realizado',
            'employee_id': self.employee.id,
            'project_id': project.id,
            'unit_amount': 5.0,
            'fsm_order_id': order1.id,
        })

        # Verificar estadísticas
        self.assertEqual(person.order_count, 2)
        self.assertEqual(person.order_active_count, 1)
        self.assertEqual(person.order_completed_count, 1)
        self.assertEqual(person.hours_total, 5.0)

    def test_person_actions(self):
        """Test acciones del técnico"""
        person = self.env['daruclima.fsm.person'].create({
            'name': 'Técnico Acciones',
            'employee_id': self.employee.id,
            'team_id': self.team.id,
        })

        # Test acción ver órdenes
        action_orders = person.action_view_orders()
        self.assertEqual(action_orders['type'], 'ir.actions.act_window')
        self.assertEqual(action_orders['res_model'], 'daruclima.fsm.order')

        # Test acción ver agenda
        action_schedule = person.action_view_schedule()
        self.assertEqual(action_schedule['type'], 'ir.actions.act_window')
        self.assertEqual(action_schedule['res_model'], 'daruclima.fsm.order')
        self.assertIn('calendar', action_schedule['view_mode'])

    def test_person_required_fields(self):
        """Test campos requeridos del técnico"""
        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.person'].create({
                'name': 'Técnico Sin Empleado',
                'team_id': self.team.id,
            })

        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.person'].create({
                'employee_id': self.employee.id,
                'team_id': self.team.id,
            })

    def test_person_availability(self):
        """Test disponibilidad del técnico"""
        person = self.env['daruclima.fsm.person'].create({
            'name': 'Técnico Disponibilidad',
            'employee_id': self.employee.id,
            'team_id': self.team.id,
            'is_available': True,
        })

        # Cambiar disponibilidad
        person.is_available = False
        self.assertFalse(person.is_available)

        # Verificar que sigue activo pero no disponible
        self.assertTrue(person.active)
        self.assertFalse(person.is_available)

    def test_person_skills_and_categories(self):
        """Test habilidades y categorías del técnico"""
        # Crear habilidad
        skill = self.env['hr.skill'].create({
            'name': 'Reparación HVAC',
        })

        # Crear categoría FSM
        category = self.env['daruclima.fsm.tag'].create({
            'name': 'Aire Acondicionado',
        })

        person = self.env['daruclima.fsm.person'].create({
            'name': 'Técnico Especialista',
            'employee_id': self.employee.id,
            'team_id': self.team.id,
            'skill_ids': [(6, 0, [skill.id])],
            'category_ids': [(6, 0, [category.id])],
        })

        # Verificar asignación
        self.assertIn(skill, person.skill_ids)
        self.assertIn(category, person.category_ids)

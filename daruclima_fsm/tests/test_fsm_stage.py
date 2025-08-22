# Copyright 2025 Xtendoo Software SLU
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestDaruclimeFSMStage(TransactionCase):
    """Test cases para etapas FSM"""

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

    def test_stage_creation(self):
        """Test creación de etapas FSM"""
        stage = self.env['daruclima.fsm.stage'].create({
            'name': 'En Proceso',
            'code': 'in_process',
            'sequence': 5,
            'color': '#FFD700',
            'description': 'Trabajo en progreso',
        })

        self.assertEqual(stage.name, 'En Proceso')
        self.assertEqual(stage.code, 'in_process')
        self.assertEqual(stage.sequence, 5)
        self.assertEqual(stage.color, '#FFD700')
        self.assertFalse(stage.is_closed)
        self.assertFalse(stage.is_default)
        self.assertTrue(stage.active)

    def test_stage_default_validation(self):
        """Test validación de etapa por defecto"""
        # Crear primera etapa por defecto
        stage1 = self.env['daruclima.fsm.stage'].create({
            'name': 'Etapa 1',
            'code': 'stage1',
            'is_default': True,
        })

        self.assertTrue(stage1.is_default)

        # Crear segunda etapa por defecto
        stage2 = self.env['daruclima.fsm.stage'].create({
            'name': 'Etapa 2',
            'code': 'stage2',
            'is_default': True,
        })

        # Verificar que solo una puede ser por defecto
        stage1.refresh()
        self.assertFalse(stage1.is_default)
        self.assertTrue(stage2.is_default)

    def test_stage_order_count(self):
        """Test conteo de órdenes por etapa"""
        stage = self.env['daruclima.fsm.stage'].create({
            'name': 'Etapa Test',
            'code': 'test_stage',
        })

        # Crear órdenes en esta etapa
        self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'stage_id': stage.id,
            'description': 'Orden 1',
        })

        self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'stage_id': stage.id,
            'description': 'Orden 2',
        })

        # Verificar conteo
        self.assertEqual(stage.order_count, 2)

    def test_stage_closed_functionality(self):
        """Test funcionalidad de etapas cerradas"""
        closed_stage = self.env['daruclima.fsm.stage'].create({
            'name': 'Completado',
            'code': 'completed',
            'is_closed': True,
        })

        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'stage_id': closed_stage.id,
            'description': 'Orden completada',
        })

        # Verificar que la orden se marca como cerrada
        self.assertTrue(order.is_closed)

    def test_stage_required_fields(self):
        """Test campos requeridos de etapas"""
        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.stage'].create({
                'code': 'test',
            })

        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.stage'].create({
                'name': 'Etapa sin código',
            })

    def test_stage_write_default_validation(self):
        """Test validación al escribir etapa por defecto"""
        stage1 = self.env['daruclima.fsm.stage'].create({
            'name': 'Etapa 1',
            'code': 'stage1',
            'is_default': True,
        })

        stage2 = self.env['daruclima.fsm.stage'].create({
            'name': 'Etapa 2',
            'code': 'stage2',
            'is_default': False,
        })

        # Cambiar la segunda etapa a por defecto
        stage2.write({'is_default': True})

        # Verificar que la primera ya no es por defecto
        stage1.refresh()
        self.assertFalse(stage1.is_default)
        self.assertTrue(stage2.is_default)


class TestDaruclimeFSMTag(TransactionCase):
    """Test cases para etiquetas FSM"""

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

    def test_tag_creation(self):
        """Test creación de etiquetas FSM"""
        tag = self.env['daruclima.fsm.tag'].create({
            'name': 'Urgente',
            'description': 'Servicios de alta prioridad',
            'color': 1,
        })

        self.assertEqual(tag.name, 'Urgente')
        self.assertEqual(tag.description, 'Servicios de alta prioridad')
        self.assertEqual(tag.color, 1)
        self.assertTrue(tag.active)

    def test_tag_order_count(self):
        """Test conteo de órdenes por etiqueta"""
        tag = self.env['daruclima.fsm.tag'].create({
            'name': 'Mantenimiento',
            'color': 2,
        })

        # Crear órdenes con esta etiqueta
        self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Orden 1',
            'tag_ids': [(6, 0, [tag.id])],
        })

        self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Orden 2',
            'tag_ids': [(6, 0, [tag.id])],
        })

        # Verificar conteo
        self.assertEqual(tag.order_count, 2)

    def test_tag_action_view_orders(self):
        """Test acción para ver órdenes de etiqueta"""
        tag = self.env['daruclima.fsm.tag'].create({
            'name': 'Test Tag',
            'color': 3,
        })

        action = tag.action_view_orders()

        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'daruclima.fsm.order')
        self.assertIn(('tag_ids', 'in', [tag.id]), action['domain'])
        self.assertIn('default_tag_ids', action['context'])

    def test_tag_required_fields(self):
        """Test campos requeridos de etiquetas"""
        with self.assertRaises(ValidationError):
            self.env['daruclima.fsm.tag'].create({
                'color': 1,
            })

    def test_tag_translation(self):
        """Test traducción de etiquetas"""
        tag = self.env['daruclima.fsm.tag'].create({
            'name': 'Emergency',
            'description': 'Emergency services',
        })

        # Verificar que los campos son traducibles
        self.assertTrue(hasattr(tag._fields['name'], 'translate'))
        self.assertEqual(tag.name, 'Emergency')

    def test_tag_color_functionality(self):
        """Test funcionalidad de colores"""
        colors = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

        for color in colors:
            tag = self.env['daruclima.fsm.tag'].create({
                'name': f'Tag Color {color}',
                'color': color,
            })
            self.assertEqual(tag.color, color)

    def test_tag_multiple_orders(self):
        """Test etiquetas en múltiples órdenes"""
        tag1 = self.env['daruclima.fsm.tag'].create({
            'name': 'Tag 1',
            'color': 1,
        })

        tag2 = self.env['daruclima.fsm.tag'].create({
            'name': 'Tag 2',
            'color': 2,
        })

        # Crear orden con múltiples etiquetas
        order = self.env['daruclima.fsm.order'].create({
            'partner_id': self.partner.id,
            'team_id': self.team.id,
            'description': 'Orden con múltiples tags',
            'tag_ids': [(6, 0, [tag1.id, tag2.id])],
        })

        # Verificar asociación
        self.assertIn(tag1, order.tag_ids)
        self.assertIn(tag2, order.tag_ids)
        self.assertEqual(tag1.order_count, 1)
        self.assertEqual(tag2.order_count, 1)

    def test_tag_company_isolation(self):
        """Test aislamiento por compañía"""
        company1 = self.env.company
        company2 = self.env['res.company'].create({
            'name': 'Company 2',
        })

        tag1 = self.env['daruclima.fsm.tag'].create({
            'name': 'Tag Company 1',
            'company_id': company1.id,
        })

        tag2 = self.env['daruclima.fsm.tag'].create({
            'name': 'Tag Company 2',
            'company_id': company2.id,
        })

        # Verificar que cada etiqueta pertenece a su compañía
        self.assertEqual(tag1.company_id, company1)
        self.assertEqual(tag2.company_id, company2)

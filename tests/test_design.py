import hashlib
import json
import unittest
from pathlib import Path

from ab import Brain
from design_brain import ROOT, create_brain
from goals.contracts import INPUT_SIZES, OUTPUT_SIZES
from goals.application import WORLD_PATH


class InteractionDesignTests(unittest.TestCase):
    def setUp(self):
        self.design = create_brain().to_dict()
        self.nodes = {n['name']: n for n in self.design['nodes']}
        self.edges = {(e['from'], e['to']): e for e in self.design['connections']}

    def test_saved_design_is_the_documented_construction(self):
        self.assertEqual(Brain.load(ROOT / 'brain.abdesign.json').to_dict(), self.design)
        for kind, contract in (('input', INPUT_SIZES), ('output', OUTPUT_SIZES)):
            self.assertEqual({n['name']: n['neurons'] for n in self.nodes.values() if n['kind'] == kind}, contract)
        self.assertEqual((len(self.nodes), len(self.edges)), (55, 74))

    def test_behavioral_topology_matches_audited_experiment(self):
        topology = sorted((e['from'], e['to'], e['type']) for e in self.edges.values()
                          if not e['from'].startswith('TRANSPORT_ACK'))
        self.assertEqual(len(topology), 69)
        self.assertEqual(hashlib.sha256(json.dumps(topology, separators=(',', ':')).encode()).hexdigest(),
                         'be4b6a02c7944419432a7af16e6b9a2a5c1208743fd81098da72fc249ff1d324')

    def test_front_turns_actuate_and_side_evidence_only_gates(self):
        for side, opposite in (('LEFT', 'RIGHT'), ('RIGHT', 'LEFT')):
            self.assertEqual(self.edges[(f'FRONT_{side}_T2', f'A_TURN_{opposite}')]['type'], 'exc')
            self.assertEqual(self.edges[(f'A_TURN_{side}', f'WHEEL_{side}')]['type'], 'inh')
            self.assertEqual(self.edges[(f'A_TURN_{side}', f'FORWARD_{side}')]['type'], 'inh')
            self.assertIn((f'SIDE_TURN_{opposite}', f'BLOCK_LIGHT_{side}'), self.edges)
            self.assertEqual(self.edges[(f'BLOCK_LIGHT_{side}', f'LIGHT_{side}_T2')]['type'], 'inh')
        self.assertFalse(any(a.startswith('SIDE_') and b.startswith(('WHEEL_', 'FORWARD_')) for a,b in self.edges))

    def test_comparison_terms_are_equal_opposing_operands(self):
        for side, opposite in (('LEFT', 'RIGHT'), ('RIGHT', 'LEFT')):
            for source, kind in ((side, 'exc'), (opposite, 'inh')):
                e = self.edges[(f'LIGHT_VALUE_{source}', f'LIGHT_COMPARE_{side}')]
                self.assertEqual((e['type'], e['role'], e['units'], e.get('strength', 1)), (kind, 'operand', 1, 1))
            self.assertEqual(self.nodes[f'LIGHT_COMPARE_{side}']['tnorm'], 3)
        operators = ('FRONT_ANY','BLOCK_LIGHT_LEFT','BLOCK_LIGHT_RIGHT','SIDE_ANY','LIGHT_ANY','OBSTACLE_ANY','ANY_GOAL')
        for name in operators:
            incoming = [e for e in self.edges.values() if e['to'] == name]
            self.assertEqual(len(incoming), 2)
            self.assertTrue(all(e['type']=='exc' and e['role']=='operand' and e['units']==1 for e in incoming))
            self.assertEqual(self.nodes[name]['tnorm'], 8)

    def test_search_yields_through_inhibition_of_the_reset(self):
        self.assertEqual(self.nodes['SEARCH_RESET']['tnorm'], 2)
        self.assertEqual(self.edges[('ANY_GOAL','SEARCH_RESET')]['strength'], 2.5)
        self.assertEqual(self.edges[('SEARCH_RESET','CAMERA_T2_RIGHT')]['role'], 'feedback')
        self.assertEqual(self.edges[('SEARCH_RESET','WHEEL_RIGHT')]['type'], 'inh')
        self.assertNotIn(('SEARCH_RESET','CAMERA_T2_LEFT'), self.edges)

    def test_sensory_and_motor_operating_points(self):
        for n in self.nodes.values():
            name = n['name']
            if name.endswith('_T1'): self.assertEqual((n['rhythm'],n['tnorm']), ('theta',3))
            if name.endswith('_T2') or name.startswith('CAMERA_T2_'):
                self.assertEqual((n['rhythm'],n['tnorm']), ('theta',2.01))
            if name.startswith(('A_TURN_','SIDE_TURN_','LIGHT_VALUE_','FORWARD_')):
                self.assertEqual((n['rhythm'],n['tnorm']), ('beta',5))

    def test_world_preserves_course_robot_and_light_geometry(self):
        world = WORLD_PATH.read_bytes()
        self.assertTrue(world.startswith(b'#VRML_SIM R2025a'))
        self.assertNotIn(b'EXTERNPROTO', world)
        self.assertIn(b'controller "interacting_goals"', world)
        self.assertIn(b'controller "light_stimulus"', world)
        self.assertEqual(hashlib.sha256(world).hexdigest(),
                         '75bbcecd44dfb9467208f923d51f51b897fd9224933dfed005107db1ce17a88d')


if __name__ == '__main__':
    unittest.main()

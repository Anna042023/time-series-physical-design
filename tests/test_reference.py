"""Tests for the standalone small-instance reference, not paper benchmarks."""
import json, random, unittest
from itertools import product
from pathlib import Path
from reference_impl.replay_core import RetentionInstance, Profile
FIXTURES=Path(__file__).resolve().parents[1]/'data'/'examples'
def load(name): return json.loads((FIXTURES/name).read_text(encoding='utf8'))

class TestB(unittest.TestCase):
    def test_optimum_invariant_under_local_compression(self):
        instance=RetentionInstance(load('replay_profiles.json'))
        raw=instance.optimize()
        for compression in ('quotient','skyline'):
            other=instance.optimize(compressed=compression)
            self.assertEqual((raw['status'],raw['utility'],raw['cost']),
                             (other['status'],other['utility'],other['cost']))
        self.assertEqual(raw['utility'],16)
        self.assertEqual(raw['cost'],9)
        self.assertEqual(len(instance.quotient()['speed']),2)

    def test_price(self):
        inst=RetentionInstance(load('replay_profiles.json'))
        for price in (0,1,2,5):
            a=inst.optimize(mode='price',price=price)
            b=inst.optimize(mode='price',price=price,compressed='skyline')
            self.assertEqual((a['score'],a['cost']),(b['score'],b['cost']))

    def test_piecewise_requirements(self):
        p=Profile.parse({'id':'a','cost':1,'segments':[[0,3,2],[3,10,1]]})
        self.assertTrue(p.satisfies(((0,3,2),)))
        self.assertFalse(p.satisfies(((0,4,2),)))
        self.assertFalse(p.satisfies(((9,11,1),)))
        with self.assertRaises(ValueError):Profile.parse({'id':'a','cost':1,'segments':[[1,3,2]]})

    def test_infeasible(self):
        a=load('replay_profiles.json');a['budget']=0
        self.assertEqual(RetentionInstance(a).optimize()['status'],'infeasible')
        with self.assertRaises(OverflowError):RetentionInstance(a).optimize(cap=1)

    def test_random_small_exact(self):
        rng=random.Random(813)
        for _ in range(20):
            a=load('replay_profiles.json')
            for profiles in a['sensors'].values():
                for p in profiles:p['cost']=rng.randrange(1,7)
            a['budget']=rng.randrange(3,15)
            inst=RetentionInstance(a)
            x=inst.optimize();y=inst.optimize(compressed='skyline')
            self.assertEqual(x['status'],y['status'])
            if x['status']!='infeasible':
                self.assertEqual((x['utility'],x['cost']),(y['utility'],y['cost']))

class TestIndependentOracle(unittest.TestCase):
    def test_independent_brute(self):
        inst = RetentionInstance(load('replay_profiles.json'))
        expected = (-1, -1)
        for speed, volume in product(inst.sensors['speed'], inst.sensors['volume']):
            utility, cost, _ = inst.evaluate({'speed': speed, 'volume': volume})
            if cost <= inst.budget:
                expected = max(expected, (utility, -cost))
        result = inst.optimize(compressed='skyline')
        self.assertEqual((result['utility'], -result['cost']), expected)

class TestExpectedOutput(unittest.TestCase):
    def test_example_matches_expected_json(self):
        inst = RetentionInstance(load('replay_profiles.json'))
        results = {'status': 'small_instance_reference_only'}
        results.update({
            'raw': inst.optimize(),
            'quotient': inst.optimize(compressed='quotient'),
            'skyline': inst.optimize(compressed='skyline'),
        })
        self.assertEqual(results, load('expected_output.json'))


if __name__ == '__main__':
    unittest.main()


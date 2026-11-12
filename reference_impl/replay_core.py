"""Small-instance exhaustive reference for replay-aware retention profiles.

A profile assigns retained sampling rates to half-open age intervals. Every
incident specifies minimum rates over its required sensor windows. Costs are
explicit nonnegative integers supplied with the input catalog.

This module implements exhaustive search and local profile pruning. It does not
implement the paper's replay-core contraction, tree-decomposition DP or MILP.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from typing import Any


@dataclass(frozen=True)
class Profile:
    name: str
    cost: int
    segments: tuple[tuple[int, int, int], ...]

    @classmethod
    def parse(cls, obj: dict[str, Any]) -> 'Profile':
        name, cost = str(obj['id']), int(obj['cost'])
        segments = tuple(tuple(map(int, x)) for x in obj['segments'])
        if cost < 0 or not segments:
            raise ValueError('nonnegative cost and nonempty segments required')
        last = 0
        for a, b, rate in segments:
            if a != last or b <= a or rate < 0:
                raise ValueError('segments must be contiguous [0,h), with positive widths')
            last = b
        return cls(name, cost, segments)

    def satisfies(self, required: tuple[tuple[int, int, int], ...]) -> bool:
        for a, b, minimum in required:
            if a < 0 or b <= a or minimum < 0:
                raise ValueError('invalid incident requirement')
            # Fully cover requirement with qualifying segments, disallow silent gaps.
            position = a
            for left, right, rate in self.segments:
                if right <= position or left >= b:
                    continue
                if left > position or rate < minimum:
                    return False
                position = min(b, right)
                if position == b:
                    break
            if position != b:
                return False
        return True


@dataclass(frozen=True)
class Incident:
    name: str
    weight: int
    requirements: dict[str, tuple[tuple[int, int, int], ...]]

    @classmethod
    def parse(cls, obj: dict[str, Any]) -> 'Incident':
        w = int(obj['weight'])
        if w < 0:
            raise ValueError('nonnegative incident weights required')
        return cls(str(obj['id']), w, {
            str(g): tuple(tuple(map(int, x)) for x in windows)
            for g, windows in obj.get('requirements', {}).items()
        })


class RetentionInstance:
    def __init__(self, data: dict[str, Any]):
        self.sensors: dict[str, tuple[Profile, ...]] = {}
        for sensor, raw_profiles in data['sensors'].items():
            if not raw_profiles:
                raise ValueError('sensor has no profiles')
            profiles = tuple(Profile.parse(p) for p in raw_profiles)
            if len({p.name for p in profiles}) != len(profiles):
                raise ValueError('duplicate profile ids')
            self.sensors[str(sensor)] = profiles
        self.incidents = tuple(Incident.parse(i) for i in data['incidents'])
        if len({inc.name for inc in self.incidents}) != len(self.incidents):
            raise ValueError('duplicate incident IDs')
        if any(not set(inc.requirements).issubset(self.sensors) for inc in self.incidents):
            raise ValueError('incident references undefined sensor')
        self.budget = int(data['budget'])
        if self.budget < 0:
            raise ValueError('negative storage budget')

    def signature(self, sensor: str, profile: Profile) -> tuple[bool, ...]:
        return tuple(profile.satisfies(inc.requirements[sensor])
                     if sensor in inc.requirements else True for inc in self.incidents)

    def quotient(self) -> dict[str, tuple[Profile, ...]]:
        """Keep min-cost (then lexicographically first) per satisfaction signature."""
        result: dict[str, tuple[Profile, ...]] = {}
        for sensor, profiles in self.sensors.items():
            grouped: dict[tuple[bool, ...], Profile] = {}
            for p in profiles:
                sig = self.signature(sensor, p)
                if sig not in grouped or (p.cost, p.name) < (grouped[sig].cost, grouped[sig].name):
                    grouped[sig] = p
            result[sensor] = tuple(sorted(grouped.values(), key=lambda p: p.name))
        return result

    def skyline(self) -> dict[str, tuple[Profile, ...]]:
        """Discard options dominated on all incident satisfaction bits and cost."""
        quot = self.quotient()
        output = {}
        for sensor, profiles in quot.items():
            retained = []
            for p in profiles:
                sig = self.signature(sensor, p)
                dominated = any(q is not p and q.cost <= p.cost and
                                all((not bit) or better for bit, better in zip(sig, self.signature(sensor, q)))
                                and (q.cost < p.cost or self.signature(sensor, q) != sig)
                                for q in profiles)
                if not dominated:
                    retained.append(p)
            output[sensor] = tuple(retained)
        return output

    def evaluate(self, assignment: dict[str, Profile]) -> tuple[int, int, tuple[str, ...]]:
        if set(assignment) != set(self.sensors):
            raise ValueError('assignment must choose one profile per sensor')
        cost = sum(p.cost for p in assignment.values())
        covered = []
        for inc in self.incidents:
            if all(assignment[s].satisfies(r) for s, r in inc.requirements.items()):
                covered.append(inc.name)
        weighted = sum(inc.weight for inc in self.incidents if inc.name in covered)
        return weighted, cost, tuple(covered)

    def optimize(self, mode: str = 'budget', price: int = 0, compressed: str = 'none',
                 cap: int = 1000000) -> dict[str, Any]:
        if mode not in ('budget', 'price') or compressed not in ('none', 'quotient', 'skyline'):
            raise ValueError('invalid optimization mode or compression')
        if price < 0:
            raise ValueError('price must be nonnegative')
        profiles = {'none': self.sensors, 'quotient': self.quotient,
                    'skyline': self.skyline}[compressed]
        if callable(profiles):
            profiles = profiles()
        keys = tuple(sorted(profiles))
        combinations = 1
        for k in keys:
            combinations *= len(profiles[k])
        if combinations > cap:
            raise OverflowError(f'{combinations} options exceed reference cap={cap}')
        best: tuple[int, int] | None = None
        best_names: tuple[str, ...] | None = None
        best_data = None
        for choice in product(*(profiles[k] for k in keys)):
            assignment = dict(zip(keys, choice))
            utility, cost, covered = self.evaluate(assignment)
            if mode == 'budget' and cost > self.budget:
                continue
            score = utility if mode == 'budget' else utility - price * cost
            tie = (score, -cost)
            names = tuple(p.name for p in choice)
            if best is None or tie > best or (tie == best and names < best_names):
                best = tie
                best_names = names
                best_data = dict(score=score, utility=utility, cost=cost,
                                 covered_incidents=list(covered), selection={k: p.name for k, p in assignment.items()})
        if best_data is None:
            return {'status': 'infeasible', 'search_space': combinations, 'compression': compressed}
        return {'status': 'optimal_in_enumerated_space', 'search_space': combinations,
                'compression': compressed, 'mode': mode, **best_data}

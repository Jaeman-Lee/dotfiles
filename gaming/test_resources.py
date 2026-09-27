#!/usr/bin/python3
"""Exercise rollback and existing-limit preservation without touching cgroups."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('profile', Path(__file__).with_name('cs2-resources.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class ResourcesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        p.STATE = self.root / 'state.json'
        p.group = lambda unit: self.root / unit
        for unit, values in p.UNITS.items():
            d = p.group(unit)
            d.mkdir()
            for key in values:
                (d / key).write_text({'cpu.max': 'max 100000', 'cpu.weight': '430', 'memory.high': 'max'}[key])
            (d / 'memory.current').write_text('70000000')
        p.set_value = lambda unit, key, value: (p.group(unit) / key).write_text(value)

    def tearDown(self):
        self.tmp.cleanup()

    def test_roundtrip(self):
        p.apply()
        self.assertEqual((p.group('kubepods.slice')/'cpu.max').read_text(), '400000 100000')
        p.restore()
        self.assertEqual((p.group('kubepods.slice')/'cpu.max').read_text(), 'max 100000')
        self.assertFalse(p.STATE.exists())

    def test_existing_stricter_limits_and_external_change(self):
        d = p.group('kubepods.slice')
        (d/'cpu.max').write_text('200000 100000')
        (d/'memory.high').write_text(str(4*1024**3))
        p.apply()
        self.assertEqual((d/'cpu.max').read_text(), '200000 100000')
        self.assertEqual((d/'memory.high').read_text(), str(4*1024**3))
        (d/'cpu.weight').write_text('70')
        p.restore()
        self.assertEqual((d/'cpu.weight').read_text(), '70')

    def test_skip_memory_throttle_when_busy(self):
        d = p.group('kubepods.slice')
        (d/'memory.current').write_text(str(7*1024**3))
        p.apply()
        self.assertEqual((d/'memory.high').read_text(), 'max')
        p.restore()

    def test_partial_failure_rolls_back(self):
        def fail_once(unit, key, value):
            if key == 'memory.high' and value != 'max':
                raise RuntimeError('simulated write failure')
            (p.group(unit)/key).write_text(value)
        p.set_value = fail_once
        with self.assertRaises(RuntimeError):
            p.apply()
        self.assertEqual((p.group('kubepods.slice')/'cpu.max').read_text(), 'max 100000')
        self.assertFalse(p.STATE.exists())

if __name__ == '__main__':
    unittest.main()

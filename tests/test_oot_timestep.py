"""Run the Ocarina time-step veneers, including the water loop, on ARM64."""
import platform
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'requires arm64 macOS')
class Timestep(unittest.TestCase):
    def test_native_veneers(self):
        with tempfile.TemporaryDirectory() as work:
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'games/oot/tests/oot_timestep_native.py'), '--work-dir', work],
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('water substeps', result.stdout)

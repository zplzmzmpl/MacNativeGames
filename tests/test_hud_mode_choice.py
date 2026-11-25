"""The Mac settings and shared FPS overlay agree on HUD modes."""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NVN = ROOT / 'shared/third_party/d2r_gfx/gfx/nvn'
ORDER = ['HUD_MODE_OFF', 'HUD_MODE_BARE', 'HUD_MODE_MINIMAL', 'HUD_MODE_ALL', 'HUD_MODE_FULL']   # the Mac panel's


def enum():
    body = re.search(r'enum \{ (HUD_MODE_OFF[^}]*)\}', (NVN / 'fps_overlay.h').read_text()).group(1)
    return {k: int(v) for k, v in re.findall(r'(HUD_MODE_\w+) = (\d+)', body)}


class Choices(unittest.TestCase):
    def test_mac_panel_order(self):
        mac = (ROOT / 'games/oot/runtime/settings_game.h').read_text()
        self.assertIn('@[' + ','.join(f'@({m})' for m in ORDER) + ']', mac)


class StartsOnTheChoice(unittest.TestCase):
    def build(self):
        cc = shutil.which('cc')
        if not cc: self.skipTest('a C compiler is required')
        d = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, d)
        exe = d / 'probe'
        r = subprocess.run([cc, '-I', str(NVN), str(ROOT / 'tests/hud_mode_probe.c'), str(NVN / 'fps_overlay.c'),
                            '-framework', 'CoreText', '-framework', 'CoreGraphics', '-framework', 'CoreFoundation', '-o', str(exe)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return exe

    def test_env(self):
        exe, values = self.build(), enum()
        run = lambda env: int(subprocess.run([str(exe)], capture_output=True, text=True, env=env).stdout)
        self.assertEqual(run({}), values['HUD_MODE_ALL'])
        for m in ORDER:
            self.assertEqual(run({'TOTK_HUD_MODE': str(values[m])}), values[m], m)
        self.assertEqual(run({'TOTK_HUD_MODE': '9'}), values['HUD_MODE_ALL'], 'a value it does not know is ignored')
        self.assertEqual(run({'TOTK_HUD_MODE': 'off'}), values['HUD_MODE_ALL'])


if __name__ == '__main__':
    unittest.main()

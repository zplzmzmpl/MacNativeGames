from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

import build_app


GAME = Path(__file__).resolve().parents[1] / 'games/oot'
spec = importlib.util.spec_from_file_location('oot_build_app_icon', GAME / 'build.py')
oot_build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oot_build)


class AppIcon(unittest.TestCase):
    def setUp(self):
        self.tree = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.icon = self.tree / 'build/AppIcon.icns'
        self.icon.parent.mkdir()

    def test_failed_conversion_discards_a_cached_icon(self):
        self.icon.write_bytes(b'previous icon')
        run = Mock(side_effect=subprocess.CalledProcessError(1, 'extract_app_icon.py'))
        with redirect_stdout(io.StringIO()) as output:
            oot_build.prepare_app_icon(Path('venv/bin/python'), self.tree, run)
        run.assert_called_once()
        self.assertFalse(self.icon.exists())
        self.assertIn('logs/app-icon.log', output.getvalue())

    def test_device_build_record_omits_a_missing_icon(self):
        out = self.tree / 'OcarinaOfTime.ipa'
        out.touch()
        (self.tree / 'ios/Gen/totk/shader-seed').mkdir(parents=True)
        (self.tree / 'ios/Gen/ios_embed.h').touch()
        seed = self.tree / 'build/shader-seed/oot/seed-manifest.json'
        seed.parent.mkdir(parents=True)
        seed.write_text('{}')
        game = dict(version='oot', expected={}, folder=GAME, depth_mode='runtime-device-state', shader_chain='oot')
        args = build_app.parse_args(['game.nup', '--platform', 'ios'])
        record = out.with_name('OcarinaOfTime-build-record.json')

        build_app.record_ns2_device_build(self.tree, out, game, args)
        self.assertNotIn('app_icon', json.loads(record.read_text()))

        self.icon.write_bytes(b'converted icon')
        build_app.record_ns2_device_build(self.tree, out, game, args)
        self.assertEqual(json.loads(record.read_text())['app_icon']['icns_sha256'], build_app.sha256(self.icon))

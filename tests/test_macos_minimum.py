"""Check the macOS release guard with small native fixtures."""
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from tools import macho_minos
from tools.deps import offline_pack

ROOT = Path(__file__).resolve().parents[1]
HAS_CLANG = (sys.platform == 'darwin' and shutil.which('xcrun') is not None and
             subprocess.run(['xcrun', '--find', 'clang'], capture_output=True).returncode == 0)


@unittest.skipUnless(HAS_CLANG, 'requires the macOS command line tools')
class MacOSMinimum(unittest.TestCase):
    def test_refuses_newer_executables_and_archive_members(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            main = b'int main(void) { return 0; }\n'
            for name, version, options in [('supported', '26.0', []), ('newer.o', '27.0', ['-c'])]:
                subprocess.run(['xcrun', 'clang', f'-mmacosx-version-min={version}', *options,
                                '-x', 'c', '-', '-o', str(root / name)], input=main, capture_output=True, check=True)
            subprocess.run(['xcrun', 'ar', 'rcs', str(root / 'library.a'), str(root / 'newer.o')], check=True)
            with tarfile.open(root / 'offline.tar', 'w') as archive:
                archive.add(root / 'library.a', arcname='built/library.a')
            self.assertEqual(macho_minos.scan(root / 'supported'), [(str(root / 'supported'), '26.0')])
            macho_minos.require_supported([root / 'supported'])
            self.assertEqual(macho_minos.too_new([root / 'offline.tar']),
                             [(f'{root}/offline.tar!built/library.a(newer.o)', '27.0')])
            with self.assertRaisesRegex(ValueError, r'newer than 26\.0'):
                offline_pack.verify_built_macos(root)

    def test_make_exports_the_minimum_to_both_shipped_programs(self):
        with tempfile.TemporaryDirectory() as directory:
            compiler = Path(directory) / 'xcrun'
            compiler.write_text('#!/bin/sh\nwhile [ "$#" -gt 1 ]; do shift; done\n'
                                'printf "%s %s\\n" "$MACOSX_DEPLOYMENT_TARGET" "$1"\n')
            compiler.chmod(0o755)
            env = dict(os.environ, MACOSX_DEPLOYMENT_TARGET='27.0', PATH=f'{directory}{os.pathsep}{os.environ["PATH"]}')
            result = subprocess.run(
                ['make', '-s', 'runtime', f'WORK={directory}', 'OPUS_PREFIX=/unused',
                 'VPX_PREFIX=/unused', 'DAV1D_PREFIX=/unused'], cwd=ROOT / 'games/oot',
                env=env, capture_output=True, text=True, check=True,
            )
            commands = result.stdout.splitlines()
            for name in ('oot-native', 'pool-sources-list'):
                self.assertIn(f'26.0 {directory}/build/{name}', commands)
            self.assertTrue(any('/obj/' in command for command in commands))
            self.assertTrue(all(command.startswith('26.0 ') for command in commands), result.stdout)

"""tools/prebuilt.py: a build from a release's source takes the programs the release compiled from the same commit, so a
player's Mac needs no Xcode command line tools (user 2026-11-17: "做 1"). A program is taken only when the folder is of
this source's commit and the file is the manifest's; otherwise the build compiles, as before."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_app  # noqa: E402
from tools import prebuilt  # noqa: E402
# a release's source.tar.gz carrying .prebuilt (make_app.source_archive) is checked in MNG-Launcher, the Launcher's own
# repository since 2026-11-20 (tests/test_porting_contract.py SourceArchive)


def source_with(root, programs, commit='c0ffee', manifest_commit=None):
    """A release source folder: .mng-source-commit and .prebuilt with these {name: bytes}."""
    (root / '.mng-source-commit').write_text(commit + '\n')
    folder = root / prebuilt.FOLDER
    folder.mkdir(parents=True)
    files = {}
    for name, data in programs.items():
        (folder / name).write_bytes(data)
        files[name] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    (folder / 'manifest.json').write_text(json.dumps({'schema': prebuilt.SCHEMA, 'commit': manifest_commit or commit,
                                                      'files': files}))
    return root










class RuntimeSignature(unittest.TestCase):
    """A runtime maps guest code at start (mprotect to PROT_EXEC); signed with the hardened runtime without the
    entitlements that permit it, macOS kills it (SIGKILL, exit 137) and every update's runtime probe fails."""

    def _macho(self, root, *, runtime=False, entitlements=None):
        """A real Mach-O (the system's true) signed as asked; its bytes."""
        src = shutil.which('true')
        if not src or not shutil.which('codesign'):
            self.skipTest('codesign and a Mach-O are needed to test the signature')
        p = root / 'true'
        p.write_bytes(Path(src).read_bytes())
        args = ['codesign', '--force', '--sign', '-']
        if runtime:
            args += ['--options', 'runtime']
        if entitlements is not None:
            ent = root / 'ent.plist'
            ent.write_text(entitlements)
            args += ['--entitlements', str(ent)]
        args.append(str(p))
        subprocess.run(args, check=True, capture_output=True)
        return p

    def test_runtime_signature_ok_for_the_three_forms(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertTrue(prebuilt.runtime_signature_ok(self._macho(root)))
            self.assertFalse(prebuilt.runtime_signature_ok(self._macho(root, runtime=True)))
            disabled = prebuilt.RUNTIME_ENTITLEMENTS.replace('<true/>', '<false/>', 1)
            self.assertFalse(prebuilt.runtime_signature_ok(self._macho(root, runtime=True, entitlements=disabled)))
            good = self._macho(root, runtime=True, entitlements=prebuilt.RUNTIME_ENTITLEMENTS)
            self.assertTrue(prebuilt.runtime_signature_ok(good))

    def test_program_takes_a_runtime_only_when_its_signature_permits_guest_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = self._macho(root, runtime=True)   # hardened runtime, no entitlements
            src = root / 'src'; src.mkdir()
            source_with(src, {'oot-native': bad.read_bytes()})
            self.assertIsNone(prebuilt.program(src, 'oot-native'))
            good = self._macho(root, runtime=True, entitlements=prebuilt.RUNTIME_ENTITLEMENTS)
            src2 = root / 'src2'; src2.mkdir()
            source_with(src2, {'oot-native': good.read_bytes()})
            self.assertEqual(prebuilt.program(src2, 'oot-native'), src2 / '.prebuilt/oot-native')

    def test_a_non_macho_stand_in_is_left_alone(self):
        """The tests' stand-in programs are a few bytes, not Mach-O: codesign cannot read them, so they are taken."""
        with tempfile.TemporaryDirectory() as tmp:
            src = source_with(Path(tmp), {'oot-native': b'runtime'})
            self.assertEqual(prebuilt.program(src, 'oot-native'), src / '.prebuilt/oot-native')


if __name__ == '__main__':
    unittest.main()

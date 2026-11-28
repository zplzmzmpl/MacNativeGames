"""update_runtime.py --plan for an Ocarina of Time app answers what its update would do (games/oot/build.py update_blocker,
the checks update_runtime makes first): "full" when the work folder cannot take an express update. 2026-11-13: --plan said
"express" for every OOT app, so after the chain moved to v27 MNG Launcher and tools/mng.py started an express update that
stopped at once ("the shaders need the full build")."""
from functools import partial
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import update_runtime  # noqa: E402


def oot_app(root, work):
    app = root / 'Ocarina of Time.app'
    (app / 'Contents').mkdir(parents=True)
    (app / 'Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleExecutable': 'OcarinaOfTime', 'MNGWorkFolder': str(work)}))
    return app


class OcarinaPlan(unittest.TestCase):
    def setUp(self):
        # a Mac with Xcode's Metal compiler (the plan asks for it first: OotNeedsMetal below)
        patch = mock.patch.object(update_runtime.build_app, 'metal_compiler', return_value=('metal', 'v', {}))
        patch.start()
        self.addCleanup(patch.stop)

    def test_a_work_folder_without_its_build_files_needs_the_full_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); work = root / 'work'; work.mkdir()
            plan = update_runtime.plan(oot_app(root, work))
        self.assertEqual((plan['kind'], plan['game']), ('full', 'oot'))
        self.assertIn('is missing', plan['reason'])

    def test_a_mounted_volume_can_recreate_a_deleted_work_folder_and_its_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            volumes = root / 'Volumes'
            volume = volumes / 'External'
            volume.mkdir(parents=True)
            work = volume / 'missing/parent/work'
            app = oot_app(root, work)
            builder = update_runtime.build_app
            recorded = partial(builder._recorded_work_path, volumes=volumes, mounted=lambda p: p == volume)
            with mock.patch.object(builder, '_recorded_work_path', side_effect=recorded):
                plan = update_runtime.plan(app)
            self.assertEqual((plan['kind'], plan['work']), ('full', str(work)))
            self.assertIn('made again there', plan['work_why'])
            self.assertFalse(work.exists())

    def test_an_unmounted_volume_is_refused_even_if_its_directories_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            volumes = root / 'Volumes'
            work = volumes / 'External/work'
            work.parent.mkdir(parents=True)
            app = oot_app(root, work)
            builder = update_runtime.build_app
            recorded = partial(builder._recorded_work_path, volumes=volumes, mounted=lambda p: False)
            with mock.patch.object(builder, '_recorded_work_path', side_effect=recorded):
                missing_plan = update_runtime.plan(app)
                work.mkdir()
                existing_plan = update_runtime.plan(app)
            for plan in (missing_plan, existing_plan):
                self.assertEqual(plan['kind'], 'error')
                self.assertIn('not mounted', plan['reason'])

    def test_launcher_full_build_uses_the_same_recorded_volume_check(self):
        from tools.builder_jobs import build_job
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            volumes = root / 'Volumes'
            work = volumes / 'External' / 'missing' / 'work'
            request = {'app': str(oot_app(root, work)), 'plan': {'game': 'oot', 'base': 'game.nup'}}
            builder = build_job.repo.build_app()
            for mounted in (False, True):
                recorded = partial(builder._recorded_work_path, volumes=volumes, mounted=lambda p: mounted)
                with mock.patch.object(builder, '_recorded_work_path', side_effect=recorded), \
                     mock.patch.object(build_job, 'express_plan', return_value={'kind': 'full'}):
                    if not mounted:
                        with self.assertRaisesRegex(build_job.Refused, 'not mounted'):
                            build_job.command(request)
                    else:
                        _, _, selected, _, kind, _ = build_job.command(request)
                        self.assertEqual((selected, kind), (work, 'full'))

    def test_the_plan_takes_the_update_s_own_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); work = root / 'work'; work.mkdir()
            app = oot_app(root, work)
            for answer, kind in (('the translation chain or the translator changed', 'full'), ('', 'express')):
                with self.subTest(answer=answer), mock.patch.object(update_runtime, 'oot_update_blocker', return_value=answer):
                    plan = update_runtime.plan(app)
                    self.assertEqual(plan['kind'], kind, plan)

    def test_the_update_refuses_with_the_same_check(self):
        text = (ROOT / 'games/oot/build.py').read_text()
        self.assertIn('blocker=update_blocker(work,mode,remake=remake)\n    if blocker:raise ValueError(blocker)', text)

    def test_launcher_disables_an_update_only_when_both_inputs_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source'
            listfile = source / 'games/oot/assets/shader_list.tsv'
            listfile.parent.mkdir(parents=True)
            listfile.write_text('bundled list\n')
            (source / '.mng-source-commit').write_text('123456789abcdef\n')
            digest = update_runtime.sha256(listfile)
            app = oot_app(root, root / 'work')
            plist = app / 'Contents/Info.plist'
            base = plistlib.loads(plist.read_bytes())
            cases = (('1234567', digest, 'current'), ('abcdef0', digest, 'express'),
                     ('1234567', 'older-list', 'express'), ('1234567', None, 'express'))
            with mock.patch.object(update_runtime.build_app, 'REPO', source), \
                 mock.patch.object(update_runtime, 'oot_update_blocker', return_value=''):
                for commit, checksum, expected in cases:
                    with self.subTest(commit=commit, checksum=checksum):
                        info = dict(base, MNGSourceCommit=commit)
                        if checksum is not None:
                            info['MNGShaderListSHA256'] = checksum
                        plist.write_bytes(plistlib.dumps(info))
                        result = update_runtime.plan(app, check_current=True)
                        self.assertEqual(result['kind'], expected, result)
                        self.assertEqual(update_runtime.plan(app)['kind'], 'express')

    def test_launcher_refuses_a_repeat_request_from_an_outdated_card(self):
        from tools.builder_jobs import build_job
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app = oot_app(root, root / 'work')
            plist = app / 'Contents/Info.plist'
            info = plistlib.loads(plist.read_bytes())
            plist.write_bytes(plistlib.dumps(dict(info, CFBundleIdentifier='org.macnativegames.oot')))
            with mock.patch.object(build_job, 'express_plan',
                                   return_value={'kind': 'current', 'reason': 'Up to date'}) as chosen:
                with self.assertRaisesRegex(build_job.Refused, 'Up to date'):
                    build_job.command({'update': str(app)})
                chosen.assert_called_once_with(app, sys.executable, None, quick=False, check_current=True)

    def test_a_new_chain_is_a_fast_update(self):
        """User 2026-11-17 "oot 加上": when only the chain or translator stops the express update and the work folder can
        translate every shader again, the plan is the fast update (--seed), not the full build."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); work = root / 'work'; work.mkdir()
            app = oot_app(root, work)
            chain = 'the translation chain or the translator changed'
            def answer(folder, app=None, remake=False):
                return '' if remake else chain
            with mock.patch.object(update_runtime, 'oot_update_blocker', side_effect=answer):
                plan = update_runtime.plan(app)
            self.assertEqual(plan['kind'], 'fast', plan)
            self.assertIn('translated again from the work folder', plan['reason'])
            self.assertNotIn('full build', plan['reason'])


class OotNeedsMetal(unittest.TestCase):
    """Ocarina of Time compiles its shader libraries with Xcode's Metal compiler (build_shader_libs.py stops without it,
    after the translation); the command line tools alone have none. MNG Launcher says so before a build or an update
    starts (user 2026-11-17: "修"), and only for Ocarina of Time."""

    def test_an_update_says_so_instead_of_starting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); work = root / 'work'; work.mkdir()
            with mock.patch.object(update_runtime.build_app, 'metal_compiler', return_value=None), \
                    mock.patch.object(update_runtime, 'oot_update_blocker', return_value='') as blocker:
                plan = update_runtime.plan(oot_app(root, work))
            self.assertEqual(plan['kind'], 'error', plan)
            self.assertIn('Metal toolchain', plan['reason'])
            blocker.assert_not_called()

    def test_a_build_says_so_in_step_three_for_ocarina_of_time_only(self):
        from tools.builder_jobs import classify
        with tempfile.TemporaryDirectory() as tmp:
            dump = str(Path(tmp) / 'dump')
            for found, game, blocked in ((None, 'oot', True), (('metal', 'v', {}), 'oot', False), (None, 'dkb', False)):
                with self.subTest(found=found, game=game), \
                        mock.patch.object(classify, 'no_metal_compiler', return_value=found is None):
                    p = classify.plan([classify.Item(dump, 'ns2_dump', game)])
                    self.assertEqual(any('Metal' in b for b in p.blocks), blocked, p.blocks)
                    # the Launcher shows it on its build page, with this Mac's needs, not with the files (tool_blocks)
                    self.assertEqual(p.tool_blocks, [b for b in p.blocks if 'Metal' in b])


def oot_build():
    import importlib.util
    spec = importlib.util.spec_from_file_location('oot_build_fast_test', ROOT / 'games/oot/build.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FastUpdateBlocker(unittest.TestCase):
    """games/oot/build.py update_blocker(remake=True): the fast update needs the work folder's game files and this
    repository's rewritten modules, not the old seed or the same chain."""

    def work_folder(self, root, context='an older chain'):
        import json
        tree = root / 'work/oot'
        (tree / 'extracted/oot/romfs').mkdir(parents=True)
        (tree / 'extracted/oot/romfs/index.json').write_text('{}')
        (tree / 'rewritten/oot').mkdir(parents=True)
        build = oot_build()
        seed, libraries, _ = build.shader_dirs(tree, 'full')
        seed.mkdir(parents=True); libraries.mkdir(parents=True)
        (seed / 'seed-manifest.json').write_text(json.dumps({'translation_context_sha256': context, 'nvn_depth_mode': 'minus-w'}))
        (libraries / 'libraries-manifest.json').write_text('{}')
        expected = json.loads((ROOT / 'games/oot/assets/expected-v131072.json').read_text())['rewritten_sha256']
        return build, root / 'work', expected

    def test_a_changed_chain_stops_the_express_update_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            build, work, expected = self.work_folder(Path(tmp))
            with mock.patch.object(build, 'sha', side_effect=lambda p: expected[Path(p).name]):
                self.assertIn('translation chain', build.update_blocker(work, 'full'))
                self.assertEqual(build.update_blocker(work, 'full', remake=True), '')

    def test_the_fast_update_still_needs_the_game_files_and_the_rewritten_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            build, work, expected = self.work_folder(Path(tmp))
            with mock.patch.object(build, 'sha', side_effect=lambda p: 'other'):
                self.assertIn('rewritten module differs', build.update_blocker(work, 'full', remake=True))
            (work / 'oot/extracted/oot/romfs/index.json').unlink()
            self.assertIn('is missing', build.update_blocker(work, 'full', remake=True))

    def test_update_runtime_takes_seed_for_ocarina_of_time(self):
        text = (ROOT / 'update_runtime.py').read_text()
        self.assertIn('return update_ocarina(app, work, remake=args.seed, shared=listfile)', text)
        self.assertNotIn("'Ocarina of Time: --seed and --native-5k are not supported", text)


if __name__ == '__main__':
    unittest.main()

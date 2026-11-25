"""The drag-and-drop builder's job layer (tools/builder_jobs): what a dropped file is, the plan, the progress record and a
whole build run against a stand-in build_app.py (events, a failure, a cancel)."""
import io
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.builder_jobs import build_job, checks, history, repo  # noqa: E402
from tools.builder_jobs.events import Emitter  # noqa: E402
sys.path.insert(0, str(ROOT / 'tests'))

class StepCounter(unittest.TestCase):
    def setUp(self):
        self.logs = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.logs)
        self.steps = build_job.Steps(self.logs, 0)
        self.log = self.logs / 'compute-pipelines.log'

    def test_the_counter_stays_while_other_lines_fill_the_end_of_the_log(self):
        self.assertIsNone(self.steps.count('compute-pipelines'))   # no log yet
        self.log.write_text('[pipeline-archive] 6144 / 29300 pipelines checked or built\n')
        self.assertEqual(self.steps.count('compute-pipelines'), (6144, 29300))
        with self.log.open('a') as f:   # the tool's other lines: more than the 4 KB the Launcher reads each second
            f.write('[par] pipeline written to its archive\n' * 400)
        self.assertEqual(self.steps.count('compute-pipelines'), (6144, 29300))
        with self.log.open('a') as f:
            f.write('[pipeline-archive] 6656 / 29300 pipelines checked or built\n')
        self.assertEqual(self.steps.count('compute-pipelines'), (6656, 29300))

    def test_a_counter_is_its_own_steps(self):
        self.log.write_text('prepared 5/9\n')
        self.steps.count('compute-pipelines')
        (self.logs / 'next.log').write_text('no counter here\n')
        self.assertIsNone(self.steps.count('next'))


class StayAwake(unittest.TestCase):
    def test_caffeinate_waits_for_the_build_and_its_absence_is_no_error(self):
        with mock.patch.object(build_job.subprocess, 'Popen') as popen:
            build_job.stay_awake(4242)
        self.assertEqual(popen.call_args.args[0], ['/usr/bin/caffeinate', '-i', '-w', '4242'])
        with mock.patch.object(build_job.subprocess, 'Popen', side_effect=FileNotFoundError):
            build_job.stay_awake(4242)


class History(unittest.TestCase):
    def test_measured_fraction_and_skipped_steps(self):
        e = history.Estimator([('a', 10.0), ('b', 30.0), ('c', 60.0)])
        self.assertEqual(e.update('a', 5, 1)[:2], (0.05, 95.0))
        self.assertEqual(e.update('c', 0, 3)[:2], (0.4, 60.0))   # b skipped (inputs unchanged): counted as done
        self.assertEqual(e.update('c', 600, 3)[0], 0.99)         # never 1 before the build ends
        self.assertEqual(e.update('zzz', 1, 3), (0.99, None, True, None))

    def test_without_a_record_the_stage(self):
        e = history.Estimator(None)
        self.assertEqual(e.update('x', 5, 3), (history.STAGE_STARTS[3], None, False, None))

    def test_record_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'r.json'
            history.record(path, [('a', 100.0), ('b', 110.0)], 150.0)
            self.assertEqual(history.load(path), [('a', 10.0), ('b', 40.0)])
            path.write_text('{damaged')
            self.assertIsNone(history.load(path))


class Checks(unittest.TestCase):
    def test_no_homebrew_package_is_needed(self):
        source = repo.BUILD_APP.read_text()
        start = source.index('def developer_tools(')   # the checks of a build that compiles (prerequisites calls it)
        body = source[start:source.index('\n\n\n', start)]   # the function alone, not the comment after it
        self.assertNotIn('libvpx', body)          # built from pinned sources (codec_libraries), not checked in Homebrew
        self.assertIn("codec_libraries(getattr(args, 'platform', 'macos'))", body)
        # Ocarina of Time links dav1d statically from that build and needs no llvm or ffmpeg (2026-11-12), so the window
        # asks for nothing from Homebrew: a Homebrew path back in its build has to come with a check here.
        oot = (repo.REPO / 'games/oot/Makefile').read_text() + (repo.REPO / 'games/oot/build.py').read_text()
        for gone in ('opt/dav1d', 'libdav1d.dylib', 'llvm@23', 'llvm-objcopy', 'ffmpeg'):
            self.assertNotIn(gone, oot)

    def test_every_check_has_text(self):
        for c in checks.checks(tempfile.gettempdir()):
            self.assertTrue(c['text'])
            self.assertTrue(c['ok'] or c['fix'], c['id'])


FAKE_BUILD = textwrap.dedent('''
    import sys, time, pathlib
    args = sys.argv[1:]
    work = pathlib.Path(args[args.index('--work') + 1])
    (work / 'logs').mkdir(parents=True, exist_ok=True)
    def say(m): print(f'[{time.strftime("%H:%M:%S")}] {m}', flush=True)
    say('1/4 code: rewriting main')
    (work / 'logs/rewrite-main.log').write_text('x')
    time.sleep(1.2)
    say('3/4 shaders: translating')
    (work / 'logs/prepare-shader-seed.log').write_text('prepared 100/400, skipped 0; 1.0s\\nprepared 300/400, skipped 0; 2.0s\\n')
    time.sleep(1.5)
    mode = (work / 'mode').read_text() if (work / 'mode').exists() else 'ok'
    if mode == 'fail':
        print('\\nERROR: tool failed (exit 3); full output: ' + str(work / 'logs/prepare-shader-seed.log'), file=sys.stderr)
        print('last line of the tool', file=sys.stderr)
        sys.exit(1)
    if mode == 'slow':
        time.sleep(30)
    say('done in 0 min: ' + args[args.index('-o') + 1])
''')


class Run(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.script = self.dir / 'build_app.py'
        self.script.write_text(FAKE_BUILD)
        self.logs = mock.patch.object(build_job, 'LOGS', self.dir / 'logs')
        self.logs.start()
        self.request = dict(plan=dict(game='oot', base=str(self.dir), blocks=[]), output_dir=str(self.dir / 'out'),
                            work_root=str(self.dir / 'work'))

    def tearDown(self):
        self.logs.stop()
        self.tmp.cleanup()

    def events(self, mode='ok'):
        (self.dir / 'work/oot').mkdir(parents=True, exist_ok=True)
        (self.dir / 'work/oot/mode').write_text(mode)
        out = io.StringIO()
        code = build_job.run(self.request, Emitter(out), self.dir / 'history', script=self.script)
        return code, [json.loads(line) for line in out.getvalue().splitlines()]

    def test_a_build_reports_stages_steps_progress_and_records_its_times(self):
        code, events = self.events()
        kinds = [e['event'] for e in events]
        self.assertEqual(code, 0)
        self.assertEqual(kinds[0], 'plan')
        self.assertEqual([e['index'] for e in events if e['event'] == 'stage'], [1, 3])
        self.assertEqual([e['name'] for e in events if e['event'] == 'step'], ['rewrite-main', 'prepare-shader-seed'])
        self.assertIn('progress', kinds)
        self.assertIn((300, 400), [(e.get('step_done'), e.get('step_total')) for e in events if e['event'] == 'progress'])
        self.assertEqual(events[-1]['event'], 'done')
        self.assertTrue(events[-1]['ok'])
        steps = history.load(history.record_path(self.dir / 'history', 'oot', 'macos'))
        self.assertEqual([n for n, _ in steps], ['rewrite-main', 'prepare-shader-seed'])
        _, again = self.events()   # the second build's bar comes from the first one's times
        self.assertTrue(again[0]['measured'])
        self.assertTrue(any(e['event'] == 'progress' and e['left'] is not None for e in again))

    def test_a_failure_names_the_error_and_the_step_log(self):
        code, events = self.events('fail')
        done = events[-1]
        self.assertNotEqual(code, 0)
        self.assertFalse(done['ok'])
        self.assertTrue(done['message'].startswith('tool failed (exit 3)'))
        self.assertIn('last line of the tool', done['detail'])
        self.assertTrue(done['step_log'].endswith('prepare-shader-seed.log'))
        self.assertTrue(Path(done['log']).is_file())

    def test_a_cancel_stops_the_build_group(self):
        (self.dir / 'work/oot').mkdir(parents=True)
        (self.dir / 'work/oot/mode').write_text('slow')
        request = self.dir / 'request.json'
        request.write_text(json.dumps(self.request))
        runner = textwrap.dedent(f'''
            import sys; sys.path.insert(0, {str(ROOT)!r})
            from unittest import mock; from pathlib import Path
            from tools.builder_jobs import build_job
            from tools.builder_jobs.events import Emitter
            import json
            build_job.LOGS = Path({str(self.dir / 'logs')!r})
            sys.exit(build_job.run(json.loads(Path({str(request)!r}).read_text()), Emitter(sys.stdout),
                                   Path({str(self.dir / 'history')!r}), script=Path({str(self.script)!r})))
        ''')
        p = subprocess.Popen([sys.executable, '-c', runner], stdout=subprocess.PIPE, text=True)
        lines = []
        for line in p.stdout:
            lines.append(json.loads(line))
            if lines[-1]['event'] == 'step' and lines[-1]['name'] == 'prepare-shader-seed':
                p.send_signal(signal.SIGINT)
        p.wait(timeout=20)
        self.assertIn('cancelling', [e['event'] for e in lines])
        self.assertFalse(lines[-1]['ok'])
        self.assertTrue(lines[-1]['cancelled'])


if __name__ == '__main__':
    unittest.main()

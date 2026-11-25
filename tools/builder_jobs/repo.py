"""build_app.py imported once, as the one source of what the games are and how their files are read (title IDs, the
Switch 2 dump layout, the shared fonts check). Importing it reads its expected-value files and runs nothing else."""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BUILD_APP = REPO / 'build_app.py'
UPDATE_RUNTIME = REPO / 'update_runtime.py'
SHADER_UPDATE = REPO / 'shader_update.py'

_module = None


def build_app():
    global _module
    if _module is None:
        spec = importlib.util.spec_from_file_location('mng_build_app', BUILD_APP)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _module = module
    return _module


GAMES = {'oot': 'Ocarina of Time'}
OOT_TITLE = '0400486024DEC000'
GAME_FOLDERS = {'oot': ('oot', 'totk')}
NOT_IN_LAUNCHER = {}


def game_of_title(title):
    """Return the one title this fork packages."""
    return 'oot' if title.upper() == OOT_TITLE else None

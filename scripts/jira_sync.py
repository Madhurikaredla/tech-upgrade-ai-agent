from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


_SPEC = spec_from_file_location(
    "scripts.jira_sync_cli",
    Path(__file__).with_name("jira-sync.py"),
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("Could not load scripts/jira-sync.py")

_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

for _name in dir(_MODULE):
    if not _name.startswith("_") or _name in {"__doc__", "__all__"}:
        globals()[_name] = getattr(_MODULE, _name)

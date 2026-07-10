import ast
from pathlib import Path

import tmis.collaboration as collaboration_package

_COLLABORATION_ROOT = Path(collaboration_package.__file__).parent


def _imported_module_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_no_module_under_tmis_collaboration_imports_tmis_ai() -> None:
    """The sprint's core constraint: 'Le moteur doit être indépendant de
    l'IA' / 'Il doit fonctionner indépendamment du TMIS AI Kernel' (see
    docs/33-legal-collaboration.md). This statically verifies it instead
    of relying on code review alone."""
    offending: list[str] = []

    for path in _COLLABORATION_ROOT.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        for name in _imported_module_names(source):
            if name == "tmis.ai" or name.startswith("tmis.ai."):
                offending.append(f"{path.relative_to(_COLLABORATION_ROOT)} imports {name!r}")

    assert offending == [], "\n".join(offending)

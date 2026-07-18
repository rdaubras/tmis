"""Audit d'usage machine-verifiable de la famille plateforme/IA transverse.

Sprint Axe B-1 (T1). Construit le graphe d'imports de tout `backend/src` et
`backend/tests` par analyse AST (aucune execution de code), puis pour chaque
sous-module direct des paquets audites calcule :

- le nombre de consommateurs externes (fichiers hors du sous-module qui en
  importent un symbole) ;
- si le sous-module est atteint par une fermeture transitive d'imports depuis
  `tmis.main` (donc reellement monte dans l'application) ;
- s'il est reference par au moins un fichier sous `backend/tests`.

Usage:
    cd backend && python scripts/audit_platform_usage.py [--format md|csv]

Le graphe est resolu uniquement a partir des imports absolus `tmis.*` (le
depot n'utilise pas d'imports relatifs, verifie par
`grep -rn "^from \\." src/tmis`).
"""

from __future__ import annotations

import argparse
import ast
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = BACKEND_ROOT / "src"
TESTS_ROOT = BACKEND_ROOT / "tests"
PACKAGE_ROOT = SRC_ROOT / "tmis"

AUDITED_PACKAGES = [
    "ai_fabric",
    "ai_team",
    "ai_governance",
    "platform",
    "runtime_platform",
    "cloud_operations",
    "platform_sdk",
]

ENTRYPOINT_MODULE = "tmis.main"


def module_name_for(path: Path, root: Path, prefix_parts: tuple[str, ...]) -> str:
    """`root` is the directory imports are resolved relative to (e.g. `src`,
    whose children already include `tmis/`). `prefix_parts` is prepended only
    when the path doesn't already start with it (needed for `tests/`, which
    has no `tests` package directory of its own on disk)."""
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if parts[: len(prefix_parts)] == list(prefix_parts):
        return ".".join(parts)
    return ".".join([*prefix_parts, *parts])


@dataclass
class FileInfo:
    module: str
    path: Path
    is_test: bool
    imports: set[str] = field(default_factory=set)


def collect_files() -> dict[str, FileInfo]:
    files: dict[str, FileInfo] = {}
    for py in PACKAGE_ROOT.rglob("*.py"):
        mod = module_name_for(py, SRC_ROOT, ("tmis",))
        files[mod] = FileInfo(module=mod, path=py, is_test=False)
    if TESTS_ROOT.exists():
        for py in TESTS_ROOT.rglob("*.py"):
            mod = module_name_for(py, TESTS_ROOT, ("tests",))
            files[mod] = FileInfo(module=mod, path=py, is_test=True)
    return files


def extract_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                # No relative imports in this repo (verified); skip defensively.
                continue
            if node.module is None:
                continue
            for alias in node.names:
                imported.add(f"{node.module}.{alias.name}")
                imported.add(node.module)
    return imported


def build_graph(files: dict[str, FileInfo]) -> None:
    for info in files.values():
        try:
            info.imports = extract_imports(info.path)
        except SyntaxError as exc:  # pragma: no cover - defensive
            print(f"WARN: could not parse {info.path}: {exc}", file=sys.stderr)


def resolves_into(imported_name: str, target_prefix: str) -> bool:
    return imported_name == target_prefix or imported_name.startswith(target_prefix + ".")


def submodules_of(package: str) -> list[str]:
    pkg_dir = PACKAGE_ROOT / package
    return sorted(
        p.name
        for p in pkg_dir.iterdir()
        if p.is_dir() and (p / "__init__.py").exists() and p.name != "__pycache__"
    )


def external_consumers(files: dict[str, FileInfo], target_prefix: str) -> list[FileInfo]:
    consumers = []
    for info in files.values():
        if resolves_into(info.module, target_prefix):
            continue  # a file inside the submodule itself is not "external"
        if any(resolves_into(imp, target_prefix) for imp in info.imports):
            consumers.append(info)
    return consumers


def transitive_closure(files: dict[str, FileInfo], entrypoint: str) -> set[str]:
    """All modules reachable from `entrypoint` by following tmis.* imports."""
    visited: set[str] = set()
    stack = [entrypoint]
    module_set = set(files.keys())
    while stack:
        mod = stack.pop()
        if mod in visited:
            continue
        visited.add(mod)
        info = files.get(mod)
        if info is None:
            continue
        for imp in info.imports:
            if not imp.startswith("tmis."):
                continue
            # Resolve import to the longest matching known module (handles
            # `from tmis.x.y import Z` where Z is a symbol, not a submodule).
            candidate = imp
            while candidate and candidate not in module_set:
                if "." not in candidate:
                    candidate = ""
                    break
                candidate = candidate.rsplit(".", 1)[0]
            if candidate and candidate not in visited:
                stack.append(candidate)
    return visited


def public_symbols(package: str, submodule: str) -> str:
    """Best-effort: class names declared anywhere in the submodule, preferring
    __init__.py re-exports, else every *.py in the directory (non-recursive).
    Purely for human orientation in the report — not used by T2's criteria."""
    sub_dir = PACKAGE_ROOT / package / submodule
    if not sub_dir.is_dir():
        return ""
    candidates = [sub_dir / "__init__.py"] + sorted(
        p for p in sub_dir.glob("*.py") if p.name != "__init__.py"
    )
    names: list[str] = []
    for py in candidates:
        if not py.exists():
            continue
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                names.append(node.name)
    seen: list[str] = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return ", ".join(seen[:4]) + ("…" if len(seen) > 4 else "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=["md", "csv"], default="md")
    parser.add_argument("--package", action="append", help="limit to given package(s)")
    args = parser.parse_args()

    files = collect_files()
    build_graph(files)
    reachable = transitive_closure(files, ENTRYPOINT_MODULE)

    packages = args.package or AUDITED_PACKAGES

    rows = []
    for package in packages:
        for submodule in submodules_of(package):
            prefix = f"tmis.{package}.{submodule}"
            consumers = external_consumers(files, prefix)
            test_consumers = [c for c in consumers if c.is_test]
            src_consumers = [c for c in consumers if not c.is_test]
            mounted = prefix in reachable or any(
                m in reachable for m in files if resolves_into(m, prefix)
            )
            rows.append(
                {
                    "package": package,
                    "submodule": submodule,
                    "public_symbols": public_symbols(package, submodule),
                    "external_consumers": len(src_consumers),
                    "consumer_modules": ", ".join(sorted(c.module for c in src_consumers)[:6]),
                    "mounted": "oui" if mounted else "non",
                    "tested": "oui" if test_consumers else "non",
                }
            )

    if args.format == "csv":
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        return

    by_package: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_package[row["package"]].append(row)

    print("# Audit d'usage — famille plateforme/IA transverse\n")
    print(
        "Genere par `backend/scripts/audit_platform_usage.py`. "
        f"Point d'entree de la fermeture transitive : `{ENTRYPOINT_MODULE}`.\n"
    )
    for package in packages:
        print(f"\n## `{package}`\n")
        print(
            "| sous-module | symboles publics (best-effort) | consommateurs externes "
            "| monte (main/api) | teste |"
        )
        print("|---|---|---|---|---|")
        for row in by_package[package]:
            print(
                f"| `{row['submodule']}` | {row['public_symbols'] or '—'} | "
                f"{row['external_consumers']} | {row['mounted']} | {row['tested']} |"
            )


if __name__ == "__main__":
    main()

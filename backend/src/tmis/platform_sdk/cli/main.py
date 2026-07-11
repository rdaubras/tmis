"""The sprint's "CLI" spec: créer, valider, empaqueter, publier,
installer un plugin. Run with `python -m tmis.platform_sdk.cli <command>`
from `backend/`. Operates against the process-wide `platform_sdk`
singletons (see `tmis.platform_sdk.bootstrap`) — a real deployment
would point this CLI at a remote TMIS instance through
`tmis.platform_sdk.api_sdk` instead; this sprint's CLI is the
in-process reference implementation."""

import argparse
import json
import shutil
import sys
from pathlib import Path

from tmis.platform_sdk.bootstrap import (
    get_extension_engine,
    get_plugin_registry,
    get_publishing_engine,
)
from tmis.platform_sdk.permissions.schemas import ExtensionPermission
from tmis.platform_sdk.plugin_system.schemas import PluginManifest, PluginType, PublishingStatus
from tmis.platform_sdk.publishing.schemas import ValidationFailedError
from tmis.platform_sdk.templates.engine import render_plugin_scaffold


def _cmd_create_plugin(args: argparse.Namespace) -> int:
    plugin_type = PluginType(args.type)
    files = render_plugin_scaffold(args.id, plugin_type, args.author)
    output_dir = Path(args.output) / args.id
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in files.items():
        (output_dir / filename).write_text(content, encoding="utf-8")
    print(f"Plugin scaffold créé dans {output_dir}")
    return 0


def _load_manifest(path: Path) -> PluginManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    return PluginManifest(
        id=data["id"],
        name=data["name"],
        version=data["version"],
        plugin_type=PluginType(data["plugin_type"]),
        author=data["author"],
        description=data["description"],
        license=data["license"],
        permissions=frozenset(data.get("permissions", ())),
        dependencies=tuple(data.get("dependencies", ())),
        compatibility=data.get("compatibility", "*"),
    )


def _cmd_validate_plugin(args: argparse.Namespace) -> int:
    manifest = _load_manifest(Path(args.manifest))
    registry = get_plugin_registry()
    if registry.get(manifest.id) is None:
        registry.register(manifest)
    publishing = get_publishing_engine()
    try:
        publishing.validate_manifest(manifest.id, actor=args.actor)
    except ValidationFailedError as exc:
        print(f"Validation échouée : {exc}", file=sys.stderr)
        return 1
    print(f"{manifest.id} est valide (statut : validated)")
    return 0


def _cmd_package_plugin(args: argparse.Namespace) -> int:
    source_dir = Path(args.path)
    manifest = json.loads((source_dir / "manifest.json").read_text(encoding="utf-8"))
    archive_base = str(Path(args.output) / f"{manifest['id']}-{manifest['version']}")
    archive_path = shutil.make_archive(archive_base, "zip", root_dir=source_dir)
    print(f"Plugin empaqueté : {archive_path}")
    return 0


def _cmd_publish_plugin(args: argparse.Namespace) -> int:
    registry = get_plugin_registry()
    publishing = get_publishing_engine()
    manifest = registry.get(args.id)
    if manifest is None:
        print(f"Plugin inconnu : {args.id}", file=sys.stderr)
        return 1
    try:
        if manifest.status is PublishingStatus.DEVELOPMENT:
            publishing.validate_manifest(args.id, actor=args.actor)
        if manifest.status is PublishingStatus.VALIDATED:
            publishing.sign_manifest(args.id, actor=args.actor)
        if manifest.status is PublishingStatus.SIGNED:
            publishing.publish(args.id, actor=args.actor)
    except ValidationFailedError as exc:
        print(f"Publication interrompue : {exc}", file=sys.stderr)
        return 1
    print(f"{args.id} est maintenant {registry.get(args.id).status.value}")  # type: ignore[union-attr]
    return 0


def _cmd_install_plugin(args: argparse.Namespace) -> int:
    requested = frozenset(ExtensionPermission(p) for p in args.permissions.split(",") if p)
    instance = get_extension_engine().install(args.firm_id, args.id, requested)
    print(f"{args.id} installé pour {args.firm_id} (instance {instance.id})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tmis-platform-sdk")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create-plugin", help="Scaffold a new plugin")
    create.add_argument("--id", required=True)
    create.add_argument("--type", required=True, choices=[t.value for t in PluginType])
    create.add_argument("--author", required=True)
    create.add_argument("--output", default=".")
    create.set_defaults(func=_cmd_create_plugin)

    validate = subparsers.add_parser("validate-plugin", help="Validate a plugin manifest")
    validate.add_argument("--manifest", required=True)
    validate.add_argument("--actor", default="cli")
    validate.set_defaults(func=_cmd_validate_plugin)

    package = subparsers.add_parser("package-plugin", help="Package a plugin directory")
    package.add_argument("--path", required=True)
    package.add_argument("--output", default=".")
    package.set_defaults(func=_cmd_package_plugin)

    publish = subparsers.add_parser("publish-plugin", help="Advance a plugin to published")
    publish.add_argument("--id", required=True)
    publish.add_argument("--actor", default="cli")
    publish.set_defaults(func=_cmd_publish_plugin)

    install = subparsers.add_parser("install-plugin", help="Install a published plugin")
    install.add_argument("--firm-id", required=True)
    install.add_argument("--id", required=True)
    install.add_argument("--permissions", default="")
    install.set_defaults(func=_cmd_install_plugin)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())

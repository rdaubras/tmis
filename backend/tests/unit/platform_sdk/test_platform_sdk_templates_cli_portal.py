import json

from tmis.platform_sdk.cli.main import build_parser
from tmis.platform_sdk.developer_portal.engine import DeveloperPortalService
from tmis.platform_sdk.developer_portal.schemas import ResourceType
from tmis.platform_sdk.plugin_system.schemas import PluginType
from tmis.platform_sdk.templates.engine import manifest_scaffold, render_plugin_scaffold


def test_manifest_scaffold_has_required_fields() -> None:
    scaffold = manifest_scaffold("my-agent", PluginType.AGENT, "Dev")

    assert scaffold["id"] == "my-agent"
    assert scaffold["plugin_type"] == "agent"
    assert scaffold["version"] == "0.1.0"


def test_render_plugin_scaffold_agent_produces_python_stub() -> None:
    files = render_plugin_scaffold("my-agent", PluginType.AGENT, "Dev")

    assert "manifest.json" in files
    assert "plugin.py" in files
    assert "BaseAgentPlugin" in files["plugin.py"]
    manifest = json.loads(files["manifest.json"])
    assert manifest["id"] == "my-agent"


def test_render_plugin_scaffold_workflow_produces_json_stub() -> None:
    files = render_plugin_scaffold("my-workflow", PluginType.WORKFLOW, "Dev")

    assert "workflow.json" in files
    assert "plugin.py" not in files
    workflow = json.loads(files["workflow.json"])
    assert workflow["id"] == "my-workflow"


def test_render_plugin_scaffold_every_type_is_renderable() -> None:
    for plugin_type in PluginType:
        files = render_plugin_scaffold("x", plugin_type, "Dev")
        assert "manifest.json" in files


def test_cli_create_plugin_writes_files(tmp_path) -> None:  # type: ignore[no-untyped-def]
    parser = build_parser()
    args = parser.parse_args(
        [
            "create-plugin",
            "--id",
            "my-agent",
            "--type",
            "agent",
            "--author",
            "Dev",
            "--output",
            str(tmp_path),
        ]
    )

    exit_code = args.func(args)

    assert exit_code == 0
    assert (tmp_path / "my-agent" / "manifest.json").exists()
    assert (tmp_path / "my-agent" / "plugin.py").exists()


def test_cli_validate_publish_install_lifecycle(tmp_path) -> None:  # type: ignore[no-untyped-def]
    parser = build_parser()
    create_args = parser.parse_args(
        [
            "create-plugin",
            "--id",
            "cli-test-agent",
            "--type",
            "agent",
            "--author",
            "Dev",
            "--output",
            str(tmp_path),
        ]
    )
    create_args.func(create_args)
    manifest_path = tmp_path / "cli-test-agent" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["description"] = "A real description"
    manifest_path.write_text(json.dumps(manifest))

    validate_args = parser.parse_args(
        ["validate-plugin", "--manifest", str(manifest_path), "--actor", "dev1"]
    )
    assert validate_args.func(validate_args) == 0

    publish_args = parser.parse_args(
        ["publish-plugin", "--id", "cli-test-agent", "--actor", "dev1"]
    )
    assert publish_args.func(publish_args) == 0

    install_args = parser.parse_args(
        [
            "install-plugin",
            "--firm-id",
            "firm-demo",
            "--id",
            "cli-test-agent",
            "--permissions",
            "",
        ]
    )
    assert install_args.func(install_args) == 0


def test_cli_package_plugin_creates_zip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    parser = build_parser()
    create_args = parser.parse_args(
        [
            "create-plugin",
            "--id",
            "pkg-agent",
            "--type",
            "agent",
            "--author",
            "Dev",
            "--output",
            str(tmp_path),
        ]
    )
    create_args.func(create_args)

    package_args = parser.parse_args(
        [
            "package-plugin",
            "--path",
            str(tmp_path / "pkg-agent"),
            "--output",
            str(tmp_path),
        ]
    )

    assert package_args.func(package_args) == 0
    assert (tmp_path / "pkg-agent-0.1.0.zip").exists()


def test_developer_portal_list_all_and_by_type() -> None:
    portal = DeveloperPortalService()

    assert len(portal.list_all()) > 0
    assert all(r.type is ResourceType.EXAMPLE for r in portal.list_by_type(ResourceType.EXAMPLE))


def test_developer_portal_search() -> None:
    portal = DeveloperPortalService()

    results = portal.search("marketplace")

    assert any("Marketplace" in r.title for r in results)

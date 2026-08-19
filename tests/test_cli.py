from __future__ import annotations

from typer.testing import CliRunner

from endurance_agent_lab.cli import app
from endurance_agent_lab.io import dump_data, load_data

runner = CliRunner()


def test_cli_validate_and_schema_export(project_root, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(project_root)
    validate_result = runner.invoke(app, ["validate"])
    assert validate_result.exit_code == 0, validate_result.stdout
    assert "All validation gates passed" in validate_result.stdout

    schema_dir = tmp_path / "schemas"
    schema_result = runner.invoke(app, ["schema", "export", "--output", str(schema_dir)])
    assert schema_result.exit_code == 0, schema_result.stdout
    assert {path.name for path in schema_dir.glob("*.schema.json")} == {
        "athlete-context.schema.json",
        "audit-output.schema.json",
        "benchmark-case.schema.json",
        "benchmark-manifest.schema.json",
        "case-grade.schema.json",
        "run-manifest.schema.json",
        "run-summary.schema.json",
    }


def test_cli_audit_loads_context_path(project_root, benchmark, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(project_root)
    context = benchmark.by_id("END-016").context
    context_path = dump_data(context, tmp_path / "context.yaml")
    output_dir = tmp_path / "audit-output"

    result = runner.invoke(
        app,
        ["audit", "--context", str(context_path), "--output", str(output_dir)],
    )

    assert result.exit_code == 0, result.stdout
    exported_context = load_data(output_dir / "context.yaml")
    assert exported_context["athlete"]["athlete_id"] == context.athlete.athlete_id

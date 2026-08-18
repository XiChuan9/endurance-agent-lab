from __future__ import annotations

from typer.testing import CliRunner

from endurance_agent_lab.cli import app


runner = CliRunner()


def test_cli_validate_and_schema_export(project_root, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(project_root)
    validate_result = runner.invoke(app, ["validate"])
    assert validate_result.exit_code == 0, validate_result.stdout
    assert "All validation gates passed" in validate_result.stdout

    schema_dir = tmp_path / "schemas"
    schema_result = runner.invoke(app, ["schema", "export", "--output", str(schema_dir)])
    assert schema_result.exit_code == 0, schema_result.stdout
    assert (schema_dir / "athlete-context.schema.json").is_file()
    assert (schema_dir / "audit-output.schema.json").is_file()

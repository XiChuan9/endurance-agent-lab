from __future__ import annotations

import importlib.util
import json
import os
import platform
import shutil
from datetime import date
from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

from .analytics import derive_metrics, validate_benchmark
from .config import Settings, load_settings
from .constants import PACKAGE_VERSION
from .evals import (
    load_benchmark,
    load_run,
    make_ad_hoc_case,
    run_benchmark,
    write_run_reports,
)
from .io import atomic_write_text, dump_data, load_model
from .longitudinal import add_snapshot, attach_audit, initialize_track, latest_snapshot
from .models.audit import AuditOutput
from .models.benchmark import BenchmarkCase
from .models.context import AthleteContext
from .providers import OpenAIProvider, ReplayProvider, RuleBasedProvider
from .providers.base import AuditProvider
from .rendering import render_audit_markdown
from .skills import load_skill
from .utils import compact_timestamp

app = typer.Typer(
    name="eal",
    help="Endurance Agent Lab: reliable endurance-agent skills, benchmarks, and evals.",
    no_args_is_help=True,
)
schema_app = typer.Typer(help="Export and inspect public JSON schemas.")
track_app = typer.Typer(help="Manage private longitudinal athlete tracks.")
app.add_typer(schema_app, name="schema")
app.add_typer(track_app, name="track")
console = Console()


def _settings(config: Path | None) -> Settings:
    return load_settings(config)


def _provider(
    name: str,
    settings: Settings,
    model: str | None,
    replay_dir: Path | None = None,
) -> AuditProvider:
    normalized = name.lower()
    if normalized in {"rules", "rule", "baseline"}:
        return RuleBasedProvider()
    if normalized == "openai":
        return OpenAIProvider(
            model=model or settings.openai.model,
            reasoning_effort=settings.openai.reasoning_effort,
            timeout_seconds=settings.openai.timeout_seconds,
            max_retries=settings.openai.max_retries,
        )
    if normalized == "replay":
        if replay_dir is None:
            raise typer.BadParameter("--replay-dir is required for provider=replay.")
        return ReplayProvider(replay_dir, model=model or "imported-output")
    raise typer.BadParameter(f"Unknown provider: {name}")


def _load_case(identifier: str, benchmark_path: Path) -> BenchmarkCase:
    candidate = Path(identifier)
    if candidate.exists():
        return load_model(candidate, BenchmarkCase)
    benchmark = load_benchmark(benchmark_path, case_ids={identifier})
    if not benchmark.cases:
        raise typer.BadParameter(f"Unknown case ID or file: {identifier}")
    return benchmark.cases[0]


@app.command()
def doctor(
    config: Annotated[Path | None, typer.Option(help="Path to configuration YAML.")] = None,
) -> None:
    """Check the local environment without making API calls."""
    settings = _settings(config)
    table = Table(title=f"Endurance Agent Lab {PACKAGE_VERSION}")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Details")

    python_ok = tuple(map(int, platform.python_version_tuple()[:2])) >= (3, 11)
    table.add_row("Python", "OK" if python_ok else "FAIL", platform.python_version())

    try:
        skill = load_skill(settings.skill_path)
        table.add_row("Skill", "OK", f"{skill.metadata.name} · {skill.sha256[:12]}")
    except Exception as exc:
        table.add_row("Skill", "FAIL", str(exc))

    validation = validate_benchmark(settings.benchmark_path)
    table.add_row(
        "Benchmark",
        "OK" if validation.ok else "FAIL",
        f"{validation.cases_validated} valid cases; {len(validation.errors)} errors",
    )

    openai_installed = importlib.util.find_spec("openai") is not None
    api_key = bool(os.getenv("OPENAI_API_KEY"))
    table.add_row(
        "OpenAI adapter",
        "READY" if openai_installed and api_key else "OPTIONAL",
        f"SDK={'yes' if openai_installed else 'no'}, key={'set' if api_key else 'not set'}",
    )
    table.add_row("Default provider", "OK", settings.provider)
    table.add_row("Private data", "PROTECTED", f"{settings.private_dir}/ is git-ignored")
    console.print(table)
    if not python_ok or not validation.ok:
        raise typer.Exit(code=1)


@app.command()
def validate(
    config: Annotated[Path | None, typer.Option(help="Path to configuration YAML.")] = None,
) -> None:
    """Validate the benchmark, skill metadata, and core contracts."""
    settings = _settings(config)
    errors: list[str] = []
    try:
        skill = load_skill(settings.skill_path)
        console.print(f"[green]Skill valid[/green]: {skill.metadata.name} ({skill.sha256[:12]})")
    except Exception as exc:
        errors.append(f"Skill: {exc}")

    report = validate_benchmark(settings.benchmark_path)
    errors.extend(report.errors)
    for warning in report.warnings:
        console.print(f"[yellow]Warning[/yellow]: {warning}")
    if report.ok:
        console.print(
            f"[green]Benchmark valid[/green]: {report.cases_validated} cases in {settings.benchmark_path}"
        )
    if errors:
        for error in errors:
            console.print(f"[red]Error[/red]: {error}")
        raise typer.Exit(code=1)
    console.print("[bold green]All validation gates passed.[/bold green]")


@app.command("audit")
def audit_command(
    case: Annotated[str | None, typer.Option(help="Benchmark case ID or case YAML path.")] = None,
    context: Annotated[Path | None, typer.Option(help="Private AthleteContext YAML/JSON.")] = None,
    provider: Annotated[str | None, typer.Option(help="rules, openai, or replay.")] = None,
    model: Annotated[str | None, typer.Option(help="Provider model name.")] = None,
    output: Annotated[Path | None, typer.Option(help="Output directory.")] = None,
    replay_dir: Annotated[Path | None, typer.Option(help="Imported output directory.")] = None,
    config: Annotated[Path | None, typer.Option(help="Path to configuration YAML.")] = None,
) -> None:
    """Audit one benchmark case or one private athlete context."""
    settings = _settings(config)
    if bool(case) == bool(context):
        raise typer.BadParameter("Supply exactly one of --case or --context.")
    if context is not None:
        benchmark_case = make_ad_hoc_case(load_model(context, AthleteContext))
    else:
        benchmark_case = _load_case(case or "", settings.benchmark_path)
    selected_provider = _provider(provider or settings.provider, settings, model, replay_dir)
    skill = load_skill(settings.skill_path)
    derived = derive_metrics(benchmark_case.context)
    result = selected_provider.audit(benchmark_case, skill, derived)

    destination = (
        output or settings.runs_dir / f"audit-{compact_timestamp()}-{benchmark_case.case_id}"
    )
    destination.mkdir(parents=True, exist_ok=False)
    dump_data(benchmark_case.context, destination / "context.yaml")
    dump_data(derived, destination / "derived.json")
    dump_data(result.audit, destination / "audit.json")
    dump_data(result, destination / "provider-result.json")
    atomic_write_text(destination / "audit.md", render_audit_markdown(result.audit))
    console.print(f"[bold green]Audit complete[/bold green]: {destination}")
    console.print(
        f"Verdict={result.audit.overall_assessment.verdict.value}, "
        f"risk={result.audit.overall_assessment.risk_level.value}, "
        f"claims={len(result.audit.claims)}"
    )


@app.command("eval")
def eval_command(
    provider: Annotated[str | None, typer.Option(help="rules, openai, or replay.")] = None,
    model: Annotated[str | None, typer.Option(help="Provider model name.")] = None,
    case: Annotated[list[str] | None, typer.Option(help="Repeat to select case IDs.")] = None,
    category: Annotated[list[str] | None, typer.Option(help="Repeat to select categories.")] = None,
    workers: Annotated[int | None, typer.Option(min=1, max=64)] = None,
    replay_dir: Annotated[Path | None, typer.Option(help="Imported output directory.")] = None,
    config: Annotated[Path | None, typer.Option(help="Path to configuration YAML.")] = None,
) -> None:
    """Run a reproducible benchmark evaluation."""
    settings = _settings(config)
    benchmark = load_benchmark(
        settings.benchmark_path,
        case_ids=set(case) if case else None,
        categories=set(category) if category else None,
    )
    if not benchmark.cases:
        raise typer.BadParameter("No enabled cases matched the filters.")
    selected_provider = _provider(provider or settings.provider, settings, model, replay_dir)
    skill = load_skill(settings.skill_path)
    run_dir, _, summary, _ = run_benchmark(
        benchmark,
        selected_provider,
        skill,
        runs_dir=settings.runs_dir,
        workers=workers or settings.workers,
        reasoning_effort=(
            settings.openai.reasoning_effort if selected_provider.name == "openai" else None
        ),
    )
    console.print(f"[bold green]Evaluation complete[/bold green]: {run_dir}")
    console.print(
        f"Score {summary.total_score:.2f}/{summary.max_score:.2f} "
        f"({summary.percentage:.2f}%), hard failures={summary.hard_failures}"
    )
    console.print(f"Report: {run_dir / 'report.html'}")


@app.command()
def demo(
    clean: Annotated[bool, typer.Option(help="Remove previous runs/demo before starting.")] = False,
    config: Annotated[Path | None, typer.Option(help="Path to configuration YAML.")] = None,
) -> None:
    """Run all 30 cases with the free deterministic baseline."""
    settings = _settings(config)
    if clean and settings.runs_dir.exists():
        for path in settings.runs_dir.glob("*-rules-transparent-baseline-v0.1"):
            shutil.rmtree(path, ignore_errors=True)
    benchmark = load_benchmark(settings.benchmark_path)
    skill = load_skill(settings.skill_path)
    run_dir, _, summary, _ = run_benchmark(
        benchmark,
        RuleBasedProvider(),
        skill,
        runs_dir=settings.runs_dir,
        workers=1,
    )
    console.print(
        f"[bold green]Zero-cost demo passed[/bold green]: {summary.cases_completed}/"
        f"{summary.cases_total} cases, {summary.percentage:.2f}% · {run_dir}"
    )


@app.command()
def report(
    run_dir: Annotated[Path, typer.Argument(help="Existing run directory.")],
) -> None:
    """Regenerate Markdown and HTML reports from recorded run artifacts."""
    manifest, summary, records = load_run(run_dir)
    write_run_reports(run_dir, manifest, summary, records)
    console.print(f"[green]Reports regenerated[/green]: {run_dir}")


@schema_app.command("export")
def export_schemas(
    output: Annotated[Path, typer.Option(help="Destination directory.")] = Path("schemas"),
) -> None:
    """Export versioned JSON Schema contracts."""
    from .models.benchmark import BenchmarkCase, BenchmarkManifest
    from .models.run import CaseGrade, RunManifest, RunSummary

    models: dict[str, type[BaseModel]] = {
        "athlete-context.schema.json": AthleteContext,
        "audit-output.schema.json": AuditOutput,
        "benchmark-case.schema.json": BenchmarkCase,
        "benchmark-manifest.schema.json": BenchmarkManifest,
        "case-grade.schema.json": CaseGrade,
        "run-manifest.schema.json": RunManifest,
        "run-summary.schema.json": RunSummary,
    }
    output.mkdir(parents=True, exist_ok=True)
    for filename, model_type in models.items():
        destination = output / filename
        atomic_write_text(
            destination,
            json.dumps(model_type.model_json_schema(), ensure_ascii=False, indent=2) + "\n",
        )
    skill_asset = Path("skills/training-plan-auditor/assets/audit-output.schema.json")
    if skill_asset.parent.exists():
        shutil.copy2(output / "audit-output.schema.json", skill_asset)
    console.print(f"[green]Exported {len(models)} schemas[/green] to {output}")


@track_app.command("init")
def track_init(
    athlete_id: Annotated[str, typer.Argument(help="Private local athlete identifier.")],
    config: Annotated[Path | None, typer.Option()] = None,
) -> None:
    settings = _settings(config)
    path = initialize_track(settings.private_dir, athlete_id)
    console.print(f"[green]Private track initialized[/green]: {path}")


@track_app.command("add")
def track_add(
    athlete_id: Annotated[str, typer.Argument()],
    context: Annotated[Path, typer.Argument(help="AthleteContext YAML/JSON.")],
    effective_date: Annotated[str, typer.Option(help="YYYY-MM-DD")],
    notes: Annotated[str | None, typer.Option()] = None,
    config: Annotated[Path | None, typer.Option()] = None,
) -> None:
    settings = _settings(config)
    track_dir = settings.private_dir / "athletes" / athlete_id
    try:
        parsed_date = date.fromisoformat(effective_date)
    except ValueError as exc:
        raise typer.BadParameter("--effective-date must use YYYY-MM-DD.") from exc
    record = add_snapshot(track_dir, context, parsed_date, notes)
    console.print(f"[green]Snapshot added[/green]: {record.snapshot_id}")


@track_app.command("show")
def track_show(
    athlete_id: Annotated[str, typer.Argument()],
    config: Annotated[Path | None, typer.Option()] = None,
) -> None:
    settings = _settings(config)
    manifest, record, context = latest_snapshot(settings.private_dir / "athletes" / athlete_id)
    table = Table(title=f"Track {manifest.athlete_id}")
    table.add_column("Snapshot")
    table.add_column("Date")
    table.add_column("Audit")
    for item in manifest.snapshots:
        table.add_row(item.snapshot_id, item.effective_date.isoformat(), item.audit_path or "—")
    console.print(table)
    console.print(
        f"Latest goal: {context.goal.race_type.value}; snapshot={record.snapshot_id}; "
        f"weeks={len(context.recent_training.weeks)}"
    )


@track_app.command("audit")
def track_audit(
    athlete_id: Annotated[str, typer.Argument()],
    provider: Annotated[str | None, typer.Option()] = None,
    model: Annotated[str | None, typer.Option()] = None,
    config: Annotated[Path | None, typer.Option()] = None,
) -> None:
    settings = _settings(config)
    track_dir = settings.private_dir / "athletes" / athlete_id
    _, record, context = latest_snapshot(track_dir)
    case = make_ad_hoc_case(context)
    selected_provider = _provider(provider or settings.provider, settings, model)
    result = selected_provider.audit(case, load_skill(settings.skill_path), derive_metrics(context))
    output_dir = track_dir / "audits" / record.snapshot_id
    output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = dump_data(result.audit, output_dir / "audit.json")
    atomic_write_text(output_dir / "audit.md", render_audit_markdown(result.audit))
    attach_audit(track_dir, record.snapshot_id, audit_path)
    console.print(f"[green]Track audit complete[/green]: {output_dir}")


if __name__ == "__main__":
    app()

from __future__ import annotations

from html import escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..models.audit import AuditOutput
from ..models.run import CaseRunRecord, RunManifest, RunSummary


def render_audit_markdown(audit: AuditOutput) -> str:
    lines = [
        f"# Training Plan Audit — {audit.case_id or 'ad-hoc'}",
        "",
        f"**Verdict:** `{audit.overall_assessment.verdict.value}`  ",
        f"**Risk:** `{audit.overall_assessment.risk_level.value}`  ",
        f"**Confidence:** {audit.overall_assessment.confidence:.0%}",
        "",
        audit.overall_assessment.summary,
        "",
        "## Data quality",
        "",
        f"Completeness: **{audit.data_quality.completeness:.0%}**",
    ]
    if audit.data_quality.issues:
        for issue in audit.data_quality.issues:
            lines.append(
                f"- **{issue.severity.value.upper()} · {issue.claim_code}** — {issue.description}"
            )
    else:
        lines.append("- No material data-quality issue was identified.")

    lines.extend(["", "## Current athlete state", ""])
    for item in audit.athlete_state:
        lines.append(
            f"- **{item.capability}: {item.status.value}** ({item.confidence:.0%}) — {item.rationale}"
        )

    lines.extend(["", "## Goal analysis", ""])
    if audit.goal_analysis.target_pace_seconds_per_km:
        pace = _format_pace(audit.goal_analysis.target_pace_seconds_per_km)
        lines.append(f"Target pace: **{pace}/km**")
    lines.append(
        f"Feasibility: **{audit.goal_analysis.feasibility.value}** — {audit.goal_analysis.rationale}"
    )

    lines.extend(["", "## Limiters", ""])
    for item in audit.limiters:
        lines.append(
            f"- **{item.priority.value}: {item.limiter}** — {item.rationale} "
            f"(confidence {item.confidence:.0%})"
        )
    if not audit.limiters:
        lines.append("- No high-confidence limiter was established.")

    lines.extend(["", "## Plan findings", ""])
    for finding in audit.plan_findings:
        lines.append(
            f"### {finding.severity.value.upper()} · {finding.claim_code}\n\n"
            f"{finding.finding}\n\n"
            f"**Consequence:** {finding.consequence}\n\n"
            f"**Recommendation:** {finding.recommendation}\n"
        )
    if not audit.plan_findings:
        lines.append("- No material plan-architecture finding was identified.")

    lines.extend(["", "## Recommended changes", ""])
    for change in audit.recommended_changes:
        lines.append(f"- **{change.action.value.upper()} · {change.target}** — {change.rationale}")

    lines.extend(["", "## Uncertainty boundary", ""])
    if audit.uncertainty.should_not_infer:
        lines.append("Do not infer:")
        lines.extend(f"- {item}" for item in audit.uncertainty.should_not_infer)
    if audit.uncertainty.follow_up_data:
        lines.append("\nUseful next data:")
        lines.extend(f"- {item}" for item in audit.uncertainty.follow_up_data)

    lines.extend(["", "## Machine-readable claim registry", ""])
    lines.extend(
        f"- `{claim.code}` — {claim.statement} ({claim.confidence:.0%})" for claim in audit.claims
    )
    lines.extend(
        [
            "",
            "---",
            "This output is a training-decision aid, not a medical diagnosis. Red-flag symptoms require qualified assessment.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_run_markdown(
    manifest: RunManifest,
    summary: RunSummary,
    records: list[CaseRunRecord],
) -> str:
    lines = [
        f"# EnduranceBench Run — {summary.run_id}",
        "",
        f"- Provider: `{summary.provider}`",
        f"- Model: `{summary.model}`",
        f"- Benchmark: `{manifest.benchmark_id}` v{manifest.benchmark_version}",
        f"- Skill hash: `{manifest.skill_hash[:12]}`",
        f"- Benchmark hash: `{manifest.benchmark_hash[:12]}`",
        f"- Score: **{summary.total_score:.2f}/{summary.max_score:.2f} ({summary.percentage:.2f}%)**",
        f"- Completed: {summary.cases_completed}/{summary.cases_total}",
        f"- Hard failures: {summary.hard_failures}",
        "",
        "## Dimension scores",
        "",
        "| Dimension | Score |",
        "|---|---:|",
    ]
    lines.extend(f"| {name} | {value:.2f}% |" for name, value in summary.dimension_scores.items())
    lines.extend(
        [
            "",
            "## Category scores",
            "",
            "| Category | Cases | Score |",
            "|---|---:|---:|",
        ]
    )
    lines.extend(
        f"| {item.category} | {item.cases} | {item.percentage:.2f}% |"
        for item in summary.category_scores
    )
    lines.extend(
        [
            "",
            "## Case results",
            "",
            "| Case | Status | Score | Evidence | Hard fail |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for record in records:
        if record.grade:
            lines.append(
                f"| {record.case_id} | {record.status} | "
                f"{record.grade.score:.2f}/{record.grade.max_score:.2f} | "
                f"{record.grade.valid_evidence_ratio:.0%} | "
                f"{'yes' if record.grade.hard_fail else 'no'} |"
            )
        else:
            lines.append(f"| {record.case_id} | error | — | — | — |")

    lines.extend(["", "## Most frequent misses", ""])
    if summary.failure_counts:
        lines.extend(
            f"- `{code}`: {count}" for code, count in list(summary.failure_counts.items())[:20]
        )
    else:
        lines.append("- None")
    if summary.input_tokens is not None or summary.output_tokens is not None:
        lines.extend(
            [
                "",
                "## Token usage",
                "",
                f"- Input tokens: {summary.input_tokens or 0}",
                f"- Output tokens: {summary.output_tokens or 0}",
            ]
        )
    lines.extend(
        [
            "",
            "---",
            "Scores are specific to the recorded benchmark, skill, provider configuration, and commit. They are not clinical validation.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_run_html(
    manifest: RunManifest,
    summary: RunSummary,
    records: list[CaseRunRecord],
) -> str:
    template_root = Path(__file__).parent / "templates"
    environment = Environment(
        loader=FileSystemLoader(template_root),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = environment.get_template("run-report.html.j2")
    return template.render(manifest=manifest, summary=summary, records=records, escape=escape)


def _format_pace(seconds: float) -> str:
    rounded = round(seconds)
    minutes, remainder = divmod(rounded, 60)
    return f"{minutes}:{remainder:02d}"

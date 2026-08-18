from __future__ import annotations

from collections import defaultdict

from ..graders import collect_failure_counts
from ..models.benchmark import BenchmarkCase
from ..models.run import CaseRunRecord, CategoryScore, RunSummary


def aggregate_run(
    run_id: str,
    provider: str,
    model: str,
    records: list[CaseRunRecord],
    cases: list[BenchmarkCase],
) -> RunSummary:
    case_by_id = {case.case_id: case for case in cases}
    completed = [record for record in records if record.grade is not None]
    grades = [record.grade for record in completed if record.grade is not None]
    total_score = sum(grade.score for grade in grades)
    max_score = sum(grade.max_score for grade in grades)

    category_values: dict[str, list[tuple[float, float]]] = defaultdict(list)
    dimension_values: dict[str, list[tuple[float, float]]] = defaultdict(list)
    input_tokens: list[int] = []
    output_tokens: list[int] = []
    for record in completed:
        if record.grade is None:
            continue
        category = case_by_id[record.case_id].category
        category_values[category].append((record.grade.score, record.grade.max_score))
        for dimension in record.grade.dimensions:
            dimension_values[dimension.dimension.value].append(
                (dimension.score, dimension.max_points)
            )
        if record.provider_result:
            if record.provider_result.usage.input_tokens is not None:
                input_tokens.append(record.provider_result.usage.input_tokens)
            if record.provider_result.usage.output_tokens is not None:
                output_tokens.append(record.provider_result.usage.output_tokens)

    category_scores = []
    for category, values in sorted(category_values.items()):
        score = sum(item[0] for item in values)
        possible = sum(item[1] for item in values)
        category_scores.append(
            CategoryScore(
                category=category,
                score=round(score, 3),
                max_score=round(possible, 3),
                percentage=round(score / possible * 100, 2) if possible else 0.0,
                cases=len(values),
            )
        )
    dimension_scores = {
        name: round(
            sum(score for score, _ in values) / sum(maximum for _, maximum in values) * 100,
            2,
        )
        if sum(maximum for _, maximum in values)
        else 0.0
        for name, values in sorted(dimension_values.items())
    }
    return RunSummary(
        run_id=run_id,
        provider=provider,
        model=model,
        total_score=round(total_score, 3),
        max_score=round(max_score, 3),
        percentage=round(total_score / max_score * 100, 2) if max_score else 0.0,
        cases_total=len(records),
        cases_completed=len(completed),
        cases_failed=sum(1 for record in records if record.status == "error"),
        hard_failures=sum(1 for grade in grades if grade.hard_fail),
        input_tokens=sum(input_tokens) if input_tokens else None,
        output_tokens=sum(output_tokens) if output_tokens else None,
        category_scores=category_scores,
        dimension_scores=dimension_scores,
        failure_counts=collect_failure_counts(grades),
    )

# Contribution to the OpenAI and Agent Ecosystem

Endurance Agent Lab contributes more than API usage.

## Domain evaluation asset

EnduranceBench provides expert-labeled professional reasoning cases involving noisy data, limiter prioritization, temporal constraints, uncertainty, and safety. These behaviors are relevant to general agent reliability, not only running knowledge.

## Reusable Skill

The training-plan auditor packages a multi-stage professional workflow as a Codex/ChatGPT-compatible Skill with scripts, references, schemas, and regression cases.

## Structured Outputs reference implementation

The OpenAI adapter demonstrates direct parsing of a complex professional audit into a strict Pydantic contract, with evidence IDs and refusal-safe boundaries instead of brittle Markdown parsing.

## Failure corpus

Versioned runs expose recurring failure types such as wrong-limiter selection, local-versus-global plan errors, threshold hallucination, environmental confounding, and user-pressure safety failures.

## gpt-oss and external model research

The provider-neutral runner and replay adapter allow the same task and grader to compare OpenAI hosted models, gpt-oss deployments, and other systems without changing benchmark ground truth.

## Longitudinal agent evaluation

The private track is the seed for evaluating belief updates and plan adaptation over time. Public longitudinal cases can later test whether an agent revises decisions when new evidence arrives, rather than scoring only one-shot answers.

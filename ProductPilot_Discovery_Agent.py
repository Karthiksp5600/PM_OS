"""Standalone ProductPilot Discovery Agent.

Run from the workspace root:

    python3 ProductPilot_Discovery_Agent.py

This file is a root-level, easy-to-open copy of the Discovery Agent. The
package version lives at `productpilot/agents/discovery_agent.py`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from time import perf_counter
from typing import Any, Mapping


JsonDict = dict[str, Any]


class DiscoveryAgentError(ValueError):
    """Raised when the Discovery Agent receives an invalid request."""


@dataclass(frozen=True)
class DiscoveryAgentConfig:
    """Runtime settings for the Discovery Agent."""

    version: str = "discovery-agent-v1"
    min_problem_words: int = 8


class DiscoveryAgent:
    """Converts a goal or feedback summary into a discovery artifact."""

    stage_id = "discovery"
    agent_name = "DiscoveryAgent"

    def __init__(self, config: DiscoveryAgentConfig | None = None) -> None:
        self.config = config or DiscoveryAgentConfig()

    def run(self, request: Mapping[str, Any]) -> JsonDict:
        """Validate a workflow request and return a full stage envelope."""

        started_at = perf_counter()
        self._validate_request(request)

        agent_input = self._build_agent_input(request)
        source_notes = self._nested_text(request, "context", "source_notes")
        retrieval_refs = list(request.get("context", {}).get("retrieval_refs", []))
        company_refs = list(request.get("context", {}).get("company_context_refs", []))
        evidence_sources = retrieval_refs or company_refs or ["unattributed_context"]

        structured_output = self._build_structured_output(agent_input, source_notes, evidence_sources)
        citations = self._build_citations(structured_output["evidence_map"], source_notes)
        metrics = self._calculate_metrics(agent_input, structured_output, citations, started_at)
        evaluation = self._evaluate(structured_output, citations, metrics)
        warnings = self._build_warnings(agent_input, metrics, evaluation)

        return {
            "workflow_id": str(request["workflow_id"]),
            "tenant_id": str(request["tenant_id"]),
            "project_id": str(request["project_id"]),
            "stage_id": self.stage_id,
            "agent_name": self.agent_name,
            "entry_mode": str(request["entry_mode"]),
            "user_intent": dict(request["user_intent"]),
            "context": dict(request["context"]),
            "instructions": dict(request["instructions"]),
            "budgets": dict(request["budgets"]),
            "policy": dict(request["policy"]),
            "status": "success" if evaluation["decision"] == "pass" else "partial",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input": agent_input,
            "structured_output": structured_output,
            "citations": citations,
            "assumptions": structured_output["key_assumptions"],
            "open_questions": structured_output["open_questions"],
            "warnings": warnings,
            "errors": [],
            "metrics": metrics,
            "evaluation": evaluation,
            "next_action": "continue_to_kpi_tree" if evaluation["decision"] != "fail" else "request_clarification",
            "artifact_ref": self._artifact_ref(request, structured_output),
            "version": self.config.version,
        }

    def _validate_request(self, request: Mapping[str, Any]) -> None:
        required = [
            "workflow_id",
            "tenant_id",
            "project_id",
            "entry_mode",
            "user_intent",
            "context",
            "instructions",
            "budgets",
            "policy",
        ]
        missing = [field for field in required if field not in request]
        if missing:
            raise DiscoveryAgentError(f"Missing required request fields: {', '.join(missing)}")

        entry_mode = request["entry_mode"]
        if entry_mode not in {"goal_driven", "feedback_driven"}:
            raise DiscoveryAgentError("entry_mode must be 'goal_driven' or 'feedback_driven'")

        user_intent = request["user_intent"]
        if not isinstance(user_intent, Mapping):
            raise DiscoveryAgentError("user_intent must be an object")

        if entry_mode == "goal_driven" and not self._has_text(user_intent.get("goal")):
            raise DiscoveryAgentError("goal_driven workflows require user_intent.goal")
        if entry_mode == "feedback_driven" and not self._has_text(user_intent.get("feedback_summary")):
            raise DiscoveryAgentError("feedback_driven workflows require user_intent.feedback_summary")

    def _build_agent_input(self, request: Mapping[str, Any]) -> JsonDict:
        user_intent = request["user_intent"]
        instructions = request.get("instructions", {})
        return {
            "mode": request["entry_mode"],
            "goal": user_intent.get("goal"),
            "feedback_summary": user_intent.get("feedback_summary"),
            "target_segment": self._first_present(request, "target_segment", "segment"),
            "time_horizon": self._first_present(request, "time_horizon", "timeline"),
            "business_context": self._business_context(request),
            "constraints": [str(item) for item in instructions.get("constraints", [])],
            "supporting_links": [],
        }

    def _build_structured_output(
        self,
        agent_input: Mapping[str, Any],
        source_notes: str,
        evidence_sources: list[str],
    ) -> JsonDict:
        primary_input = self._primary_input(agent_input)
        target_segment = agent_input.get("target_segment") or "the target users"
        constraints = list(agent_input.get("constraints", []))

        problem_statement = self._draft_problem_statement(primary_input, target_segment, agent_input["mode"])
        why_now = self._draft_why_now(primary_input, source_notes, agent_input["mode"])

        return {
            "problem_statement": problem_statement,
            "why_now": why_now,
            "problem_scope": {
                "in_scope": self._scope_in(primary_input, target_segment),
                "out_of_scope": self._scope_out(constraints),
            },
            "key_assumptions": self._assumptions(primary_input, agent_input["mode"], source_notes),
            "open_questions": self._open_questions(agent_input, source_notes),
            "success_definition": self._success_definition(primary_input, target_segment, agent_input.get("time_horizon")),
            "evidence_map": self._evidence_map(problem_statement, why_now, evidence_sources),
        }

    def _draft_problem_statement(self, primary_input: str, target_segment: str, mode: str) -> str:
        trimmed_input = self._trim_sentence(primary_input)
        if mode == "feedback_driven":
            return (
                f"{target_segment} appear to be experiencing a recurring problem reflected in feedback: "
                f"{trimmed_input}. The discovery focus is to identify the root cause, affected journey stage, "
                "and measurable product outcome that should improve."
            )
        return (
            f"{target_segment} need a clearer path from the stated business goal to a solvable product problem: "
            f"{trimmed_input}. The discovery focus is to define the user behavior, constraint, or unmet need "
            "that most directly blocks that goal."
        )

    def _draft_why_now(self, primary_input: str, source_notes: str, mode: str) -> str:
        signal = self._trim_sentence(source_notes) if self._has_text(source_notes) else self._trim_sentence(primary_input)
        if mode == "feedback_driven":
            return f"The feedback signal is concentrated enough to justify discovery now. The strongest available signal is: {signal}."
        return f"The business goal creates a timely need to clarify the product problem before solutioning. The strongest available signal is: {signal}."

    def _scope_in(self, primary_input: str, target_segment: str) -> list[str]:
        return [
            f"User journey and product area connected to: {self._trim_sentence(primary_input)}",
            f"Needs, blockers, and motivations for {target_segment}",
            "Metrics that can prove the problem is improving",
            "Evidence-backed assumptions that need validation",
        ]

    def _scope_out(self, constraints: list[str]) -> list[str]:
        out_of_scope = [
            "Final solution selection",
            "Detailed engineering implementation",
            "Unapproved roadmap commitment",
        ]
        out_of_scope.extend(f"Work that violates constraint: {constraint}" for constraint in constraints)
        return out_of_scope

    def _assumptions(self, primary_input: str, mode: str, source_notes: str) -> list[str]:
        assumptions = [
            "The stated input represents a meaningful product or business signal.",
            "The issue can be improved through product intervention rather than only process or go-to-market changes.",
            "The team can access enough evidence to validate the problem before committing to a solution.",
        ]
        if mode == "feedback_driven":
            assumptions.append("The feedback sample is representative enough to begin discovery, even if not statistically complete.")
        if not self._has_text(source_notes):
            assumptions.append("Additional evidence is needed because the current context does not include detailed source notes.")
        if len(primary_input.split()) < self.config.min_problem_words:
            assumptions.append("The starting input may be too terse and may need human clarification.")
        return assumptions

    def _open_questions(self, agent_input: Mapping[str, Any], source_notes: str) -> list[str]:
        questions = [
            "Which user segment is most affected by this problem?",
            "What metric currently proves the problem exists?",
            "What behavior change would show that the problem is solved?",
        ]
        if not self._has_text(agent_input.get("target_segment")):
            questions.append("Who is the primary target segment for this workflow?")
        if not self._has_text(agent_input.get("time_horizon")):
            questions.append("What time horizon should the team use when judging impact?")
        if not self._has_text(source_notes):
            questions.append("Which source documents or customer examples should be treated as strongest evidence?")
        return questions

    def _success_definition(self, primary_input: str, target_segment: str, time_horizon: Any) -> str:
        horizon = f" within {time_horizon}" if self._has_text(time_horizon) else ""
        return (
            f"Success means {target_segment} show measurable improvement in the behavior or outcome "
            f"blocked by '{self._trim_sentence(primary_input)}'{horizon}, without harming guardrail metrics."
        )

    def _evidence_map(self, problem_statement: str, why_now: str, evidence_sources: list[str]) -> list[JsonDict]:
        primary_source = evidence_sources[0]
        secondary_source = evidence_sources[1] if len(evidence_sources) > 1 else primary_source
        return [
            {"claim": problem_statement, "source_id": primary_source, "note": "Primary claim for discovery framing."},
            {"claim": why_now, "source_id": secondary_source, "note": "Timing and urgency claim."},
        ]

    def _build_citations(self, evidence_map: list[Mapping[str, Any]], source_notes: str) -> list[JsonDict]:
        confidence = 0.82 if self._has_text(source_notes) else 0.62
        return [
            {
                "source_id": str(item["source_id"]),
                "claim": str(item["claim"]),
                "source_type": "rag" if str(item["source_id"]).startswith("rag") else "company_context",
                "excerpt": self._trim_sentence(source_notes) if self._has_text(source_notes) else "",
                "confidence": confidence,
                "trust_score": confidence,
                "relevance_score": confidence,
            }
            for item in evidence_map
        ]

    def _calculate_metrics(
        self,
        agent_input: Mapping[str, Any],
        structured_output: Mapping[str, Any],
        citations: list[Mapping[str, Any]],
        started_at: float,
    ) -> JsonDict:
        primary_input = self._primary_input(agent_input)
        problem_words = len(str(structured_output["problem_statement"]).split())
        scope_items = len(structured_output["problem_scope"]["in_scope"]) + len(structured_output["problem_scope"]["out_of_scope"])
        assumption_count = len(structured_output["key_assumptions"])
        evidence_count = len(structured_output["evidence_map"])
        claim_count = 2

        return {
            "latency_ms": round((perf_counter() - started_at) * 1000, 3),
            "token_input": self._rough_token_count(primary_input),
            "token_output": self._rough_token_count(str(structured_output)),
            "cost_usd": 0,
            "retry_count": 0,
            "input_completeness": self._input_completeness(agent_input),
            "output_completeness": self._output_completeness(structured_output),
            "citation_coverage": min(1.0, evidence_count / max(1, claim_count)),
            "hallucination_risk": self._hallucination_risk(citations),
            "consistency_score": self._consistency_score(structured_output),
            "confidence_score": self._average([citation.get("confidence", 0) for citation in citations]),
            "instruction_following": 0.92,
            "business_logic_score": 0.84 if problem_words >= self.config.min_problem_words else 0.68,
            "problem_clarity_score": min(1.0, problem_words / 36),
            "scope_precision": min(1.0, scope_items / 6),
            "assumption_quality_score": min(1.0, assumption_count / 4),
            "evidence_to_claim_ratio": round(evidence_count / max(1, claim_count), 3),
            "root_cause_confidence": 0.72 if self._has_text(agent_input.get("business_context")) else 0.55,
            "open_question_count": len(structured_output["open_questions"]),
        }

    def _evaluate(
        self,
        structured_output: Mapping[str, Any],
        citations: list[Mapping[str, Any]],
        metrics: Mapping[str, Any],
    ) -> JsonDict:
        required_fields = [
            "problem_statement",
            "why_now",
            "problem_scope",
            "key_assumptions",
            "open_questions",
            "success_definition",
            "evidence_map",
        ]
        schema_valid = all(field in structured_output for field in required_fields)
        reasons: list[str] = []
        required_actions: list[str] = []

        if schema_valid:
            reasons.append("All required discovery output fields are present.")
        else:
            required_actions.append("Regenerate the output with all required discovery fields.")

        if metrics["citation_coverage"] >= 0.7:
            reasons.append("Core discovery claims include citation coverage.")
        else:
            required_actions.append("Add stronger source coverage for the core problem and urgency claims.")

        if metrics["problem_clarity_score"] >= 0.7:
            reasons.append("The problem statement is specific enough for downstream KPI work.")
        else:
            required_actions.append("Clarify the problem statement before moving to KPI definition.")

        if metrics["hallucination_risk"] > 0.3:
            required_actions.append("Review source grounding before continuing.")

        overall_score = self._average(
            [
                float(schema_valid),
                metrics["citation_coverage"],
                1 - metrics["hallucination_risk"],
                metrics["output_completeness"],
                metrics["consistency_score"],
                metrics["instruction_following"],
                metrics["confidence_score"],
                metrics["business_logic_score"],
            ]
        )
        decision = "pass" if schema_valid and overall_score >= 0.75 and not required_actions else "warn"
        if not schema_valid:
            decision = "fail"

        return {
            "schema_valid": schema_valid,
            "citation_coverage": metrics["citation_coverage"],
            "citation_quality": self._average([citation.get("relevance_score", 0) for citation in citations]),
            "hallucination_risk": metrics["hallucination_risk"],
            "completeness": metrics["output_completeness"],
            "consistency": metrics["consistency_score"],
            "instruction_following": metrics["instruction_following"],
            "confidence_calibration": metrics["confidence_score"],
            "business_logic_score": metrics["business_logic_score"],
            "overall_score": round(overall_score, 3),
            "decision": decision,
            "reasons": reasons,
            "required_actions": required_actions,
            "retry_recommended": decision == "fail",
            "human_review_required": True,
        }

    def _build_warnings(
        self,
        agent_input: Mapping[str, Any],
        metrics: Mapping[str, Any],
        evaluation: Mapping[str, Any],
    ) -> list[str]:
        warnings: list[str] = []
        if metrics["input_completeness"] < 0.75:
            warnings.append("Input is usable but incomplete; human review should confirm segment and time horizon.")
        if evaluation["decision"] == "warn":
            warnings.extend(evaluation["required_actions"])
        if not agent_input.get("constraints"):
            warnings.append("No explicit constraints were provided.")
        return warnings

    def _business_context(self, request: Mapping[str, Any]) -> str:
        source_notes = self._nested_text(request, "context", "source_notes")
        if self._has_text(source_notes):
            return source_notes
        return str(request["user_intent"].get("goal") or request["user_intent"].get("feedback_summary"))

    def _primary_input(self, agent_input: Mapping[str, Any]) -> str:
        return str(agent_input.get("goal") or agent_input.get("feedback_summary") or agent_input.get("business_context") or "")

    def _first_present(self, request: Mapping[str, Any], *names: str) -> str | None:
        for name in names:
            value = request.get(name)
            if self._has_text(value):
                return str(value)
        return None

    def _nested_text(self, request: Mapping[str, Any], *path: str) -> str:
        current: Any = request
        for key in path:
            if not isinstance(current, Mapping):
                return ""
            current = current.get(key)
        return str(current) if self._has_text(current) else ""

    def _input_completeness(self, agent_input: Mapping[str, Any]) -> float:
        fields = ["mode", "business_context", "constraints", "target_segment", "time_horizon"]
        present = sum(1 for field in fields if self._has_text(agent_input.get(field)) or bool(agent_input.get(field)))
        return round(present / len(fields), 3)

    def _output_completeness(self, structured_output: Mapping[str, Any]) -> float:
        checks = [
            self._has_text(structured_output.get("problem_statement")),
            self._has_text(structured_output.get("why_now")),
            bool(structured_output.get("problem_scope", {}).get("in_scope")),
            bool(structured_output.get("problem_scope", {}).get("out_of_scope")),
            bool(structured_output.get("key_assumptions")),
            bool(structured_output.get("open_questions")),
            self._has_text(structured_output.get("success_definition")),
            bool(structured_output.get("evidence_map")),
        ]
        return round(sum(checks) / len(checks), 3)

    def _hallucination_risk(self, citations: list[Mapping[str, Any]]) -> float:
        if not citations:
            return 1.0
        return round(max(0.0, 1 - self._average([citation.get("confidence", 0) for citation in citations])), 3)

    def _consistency_score(self, structured_output: Mapping[str, Any]) -> float:
        problem = str(structured_output.get("problem_statement", "")).lower()
        success = str(structured_output.get("success_definition", "")).lower()
        shared_terms = set(problem.split()).intersection(success.split())
        return min(1.0, 0.65 + len(shared_terms) / 40)

    def _artifact_ref(self, request: Mapping[str, Any], structured_output: Mapping[str, Any]) -> str:
        raw = f"{request['workflow_id']}:{self.stage_id}:{structured_output['problem_statement']}"
        return f"art_{sha256(raw.encode('utf-8')).hexdigest()[:16]}"

    def _trim_sentence(self, value: str, max_chars: int = 180) -> str:
        text = " ".join(str(value).split())
        if len(text) <= max_chars:
            return text.rstrip(".!?")
        return text[: max_chars - 3].rstrip(".!? ") + "..."

    def _rough_token_count(self, value: str) -> int:
        return max(1, round(len(value.split()) * 1.3))

    def _average(self, values: list[Any]) -> float:
        numbers = [float(value) for value in values if isinstance(value, (int, float))]
        if not numbers:
            return 0.0
        return round(sum(numbers) / len(numbers), 3)

    def _has_text(self, value: Any) -> bool:
        return isinstance(value, str) and bool(value.strip())


def example_request() -> JsonDict:
    """Return a sample goal-driven workflow request."""

    return {
        "workflow_id": "wf_activation_001",
        "tenant_id": "tenant_acme",
        "project_id": "proj_growth",
        "entry_mode": "goal_driven",
        "target_segment": "new workspace admins",
        "time_horizon": "the next quarter",
        "user_intent": {
            "goal": "Increase activation in the first 7 days for new B2B workspaces.",
            "feedback_summary": None,
        },
        "context": {
            "company_context_refs": ["doc_activation_strategy"],
            "prior_stage_refs": [],
            "retrieval_refs": ["rag_onboarding_dropoff", "rag_admin_feedback"],
            "memory_refs": ["mem_prd_style"],
            "source_notes": (
                "Analytics show a steep drop-off before invite completion. "
                "Support notes mention that workspace admins are unsure what setup step creates first value."
            ),
        },
        "instructions": {
            "task": "Frame the discovery problem for activation improvement.",
            "constraints": [
                "Do not propose final solutions yet.",
                "Ground every major claim in available context.",
            ],
            "success_criteria": [
                "Clear problem statement",
                "Explicit assumptions",
                "Reviewable open questions",
            ],
            "output_style": "concise_product_discovery",
        },
        "budgets": {
            "token_budget": 4000,
            "latency_budget_ms": 120000,
            "retry_count": 0,
            "cost_budget_usd": 0.25,
        },
        "policy": {
            "approval_required": True,
            "can_write_memory": False,
            "can_publish": False,
            "sensitivity": "internal",
        },
    }


def main() -> None:
    """Run a sample Discovery Agent workflow."""

    result = DiscoveryAgent().run(example_request())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()


# ProductPilot Discovery Agent Implementation

**Standalone code file:** `ProductPilot_Discovery_Agent.py`  
**Package wrapper:** `productpilot/agents/discovery_agent.py`  
**Example file:** `examples/discovery_agent_example.py`  
**Schema file:** `schemas/agents/discovery.schema.json`  
**Status:** Runnable first implementation

---

# 1. Overview

The Discovery Agent is the first agent in the ProductPilot AI workflow. Its job is to take an initial product signal and turn it into a structured discovery artifact that downstream agents can safely use.

The input can come from:

- Goal-driven mode, where a PM starts from a business objective
- Feedback-driven mode, where a PM starts from customer feedback or a feedback cluster

The agent produces:

- A clear problem statement
- A reason why the problem matters now
- In-scope and out-of-scope boundaries
- Key assumptions
- Open questions for PM review
- A success definition
- An evidence map
- Citations
- Metrics
- Evaluation results
- A next action for the workflow orchestrator

This implementation is deterministic and dependency-free. It does not require an LLM API key, a web service, or third-party packages. That makes it easy to run locally and easy to test. Later, the deterministic drafting methods can be replaced with model calls while preserving the same input and output contract.

---

# 2. Why The Discovery Agent Matters

Product workflows often fail because the team jumps from a vague goal directly to solutions. The Discovery Agent prevents that by forcing the workflow to clarify the problem before moving into KPI definition, solutioning, prioritization, or PRD generation.

It answers:

- What is the actual product problem?
- Which user or segment is affected?
- Why should the team care now?
- What assumptions are being made?
- What evidence supports the framing?
- What is explicitly out of scope?
- What must a human PM still clarify?

The KPI Tree Agent depends on this output. If discovery is weak, every later stage becomes less trustworthy.

---

# 3. Files Created

## 3.1 Agent Runtime

`productpilot/agents/discovery_agent.py`

Contains the full Discovery Agent implementation:

- `DiscoveryAgent`
- `DiscoveryAgentConfig`
- `DiscoveryAgentError`
- Input validation
- Input normalization
- Structured output generation
- Citation generation
- Metrics calculation
- Evaluation scoring
- Warning generation
- Artifact reference generation

## 3.2 Package Exports

`productpilot/__init__.py`

Defines the root Python package.

`productpilot/agents/__init__.py`

Exports the agent:

```python
from productpilot.agents import DiscoveryAgent
```

## 3.3 Runnable Example

`examples/discovery_agent_example.py`

Runs the Discovery Agent with a sample goal-driven request and prints a JSON response.

## 3.4 Contract Schema

`schemas/agents/discovery.schema.json`

Defines the intended stage contract for the Discovery Agent.

---

# 4. Public API

The main API is:

```python
from productpilot.agents import DiscoveryAgent

result = DiscoveryAgent().run(request)
```

The `run` method accepts a workflow request dictionary and returns a complete discovery stage envelope.

---

# 5. Required Input Shape

The request must include:

```json
{
  "workflow_id": "wf_activation_001",
  "tenant_id": "tenant_acme",
  "project_id": "proj_growth",
  "entry_mode": "goal_driven",
  "user_intent": {
    "goal": "Increase activation in the first 7 days for new B2B workspaces.",
    "feedback_summary": null
  },
  "context": {
    "company_context_refs": ["doc_activation_strategy"],
    "prior_stage_refs": [],
    "retrieval_refs": ["rag_onboarding_dropoff"],
    "memory_refs": [],
    "source_notes": "Analytics show a steep drop-off before invite completion."
  },
  "instructions": {
    "task": "Frame the discovery problem.",
    "constraints": ["Do not propose final solutions yet."],
    "success_criteria": ["Clear problem statement"],
    "output_style": "concise_product_discovery"
  },
  "budgets": {
    "token_budget": 4000,
    "latency_budget_ms": 120000,
    "retry_count": 0
  },
  "policy": {
    "approval_required": true,
    "can_write_memory": false,
    "can_publish": false
  }
}
```

## 5.1 Required Top-Level Fields

- `workflow_id`
- `tenant_id`
- `project_id`
- `entry_mode`
- `user_intent`
- `context`
- `instructions`
- `budgets`
- `policy`

## 5.2 Goal-Driven Requirement

If `entry_mode` is `goal_driven`, then `user_intent.goal` must be present and non-empty.

## 5.3 Feedback-Driven Requirement

If `entry_mode` is `feedback_driven`, then `user_intent.feedback_summary` must be present and non-empty.

## 5.4 Optional Enrichment Fields

The current implementation also uses these optional top-level fields when present:

- `target_segment`
- `segment`
- `time_horizon`
- `timeline`

---

# 6. Output Shape

The agent returns a complete stage envelope. The most important field is `structured_output`.

```json
{
  "stage_id": "discovery",
  "agent_name": "DiscoveryAgent",
  "status": "success",
  "structured_output": {
    "problem_statement": "...",
    "why_now": "...",
    "problem_scope": {
      "in_scope": ["..."],
      "out_of_scope": ["..."]
    },
    "key_assumptions": ["..."],
    "open_questions": ["..."],
    "success_definition": "...",
    "evidence_map": [
      {
        "claim": "...",
        "source_id": "rag_onboarding_dropoff",
        "note": "Primary claim for discovery framing."
      }
    ]
  },
  "citations": [],
  "metrics": {},
  "evaluation": {}
}
```

The full return object also includes workflow metadata, input normalization, assumptions, warnings, errors, next action, artifact reference, and version.

---

# 7. Execution Flow

The agent follows this sequence:

1. Validate required workflow fields
2. Validate entry mode and required intent
3. Normalize the input into the Discovery Agent input shape
4. Choose evidence sources from retrieval references or company context references
5. Draft the problem statement
6. Draft the `why_now` explanation
7. Build in-scope and out-of-scope boundaries
8. Generate assumptions and open questions
9. Create the success definition
10. Build the evidence map and citations
11. Calculate metrics
12. Evaluate the output
13. Return the stage envelope

The agent does not call the next agent directly. The orchestrator should read `next_action` and decide what happens next.

---

# 8. Metrics

The Discovery Agent calculates shared metrics and discovery-specific metrics.

## 8.1 Shared Metrics

- `latency_ms`
- `token_input`
- `token_output`
- `cost_usd`
- `retry_count`
- `input_completeness`
- `output_completeness`
- `citation_coverage`
- `hallucination_risk`
- `consistency_score`
- `confidence_score`
- `instruction_following`
- `business_logic_score`

## 8.2 Discovery-Specific Metrics

- `problem_clarity_score`
- `scope_precision`
- `assumption_quality_score`
- `evidence_to_claim_ratio`
- `root_cause_confidence`
- `open_question_count`

## 8.3 Metric Purpose

`problem_clarity_score` measures whether the problem statement is specific enough to support KPI work.

`scope_precision` measures whether the agent produced useful boundaries.

`assumption_quality_score` measures whether uncertainty was surfaced instead of hidden.

`evidence_to_claim_ratio` compares evidence-backed claims to major generated claims.

`root_cause_confidence` estimates whether the context is strong enough to continue.

`open_question_count` tells the PM how much clarification remains.

---

# 9. Evaluation

The agent returns an evaluation envelope with:

- `schema_valid`
- `citation_coverage`
- `citation_quality`
- `hallucination_risk`
- `completeness`
- `consistency`
- `instruction_following`
- `confidence_calibration`
- `business_logic_score`
- `overall_score`
- `decision`
- `reasons`
- `required_actions`
- `retry_recommended`
- `human_review_required`

## 9.1 Evaluation Decisions

`pass`

The output is structurally complete and ready for human review.

`warn`

The output is usable, but the PM should inspect warnings or missing context.

`fail`

The output is structurally invalid and should not move forward.

## 9.2 Current Thresholds

The current implementation uses these first-pass thresholds:

- Citation coverage should be at least `0.7`
- Problem clarity should be at least `0.7`
- Hallucination risk should be at most `0.3`
- Overall score should be at least `0.75`

---

# 10. Error Handling

Invalid requests raise `DiscoveryAgentError`.

Examples:

- Missing `workflow_id`
- Invalid `entry_mode`
- Goal-driven request without `user_intent.goal`
- Feedback-driven request without `user_intent.feedback_summary`

Valid but incomplete requests return warnings inside the stage envelope.

Examples:

- Missing target segment
- Missing time horizon
- Missing source notes
- No explicit constraints

---

# 11. How To Run

From the workspace root:

```bash
python3 examples/discovery_agent_example.py
```

Expected result:

- The script prints JSON
- `stage_id` is `discovery`
- `agent_name` is `DiscoveryAgent`
- `structured_output.problem_statement` is present
- `metrics` is present
- `evaluation` is present

---

# 12. Integration Guidance

The workflow orchestrator should call:

```python
from productpilot.agents import DiscoveryAgent

result = DiscoveryAgent().run(workflow_request)
```

Then the orchestrator should:

1. Persist the stage result as an artifact
2. Check `result["evaluation"]["decision"]`
3. Send `pass` or `warn` outputs to PM review
4. Retry or request clarification for `fail`
5. Pass approved discovery output to the KPI Tree Agent

The Discovery Agent should not own persistence, review approval, retries, or downstream sequencing. Those belong to the orchestrator.

---

# 13. Extension Points

## 13.1 Add LLM Generation

The deterministic drafting methods can later be replaced with model calls:

- `_draft_problem_statement`
- `_draft_why_now`
- `_assumptions`
- `_open_questions`
- `_success_definition`

The method outputs should remain the same field types.

## 13.2 Add Full JSON Schema Validation

The current implementation is dependency-free and does not import `jsonschema`. A production implementation should validate the returned object against:

```text
schemas/agents/discovery.schema.json
```

Recommended Python libraries:

- `jsonschema`
- `referencing`
- `pydantic`

## 13.3 Add Real Retrieval Payloads

The current version uses retrieval reference IDs and `context.source_notes`. A production retrieval payload should include:

- Source ID
- Source title
- Source type
- Excerpt
- Relevance score
- Trust score
- Freshness score

## 13.4 Add Tests

Recommended tests:

- Goal-driven happy path
- Feedback-driven happy path
- Missing required field
- Goal-driven request without goal
- Feedback-driven request without feedback summary
- Missing source notes warning
- Evaluation warning for weak evidence

---

# 14. Current Limitations

- Drafting is heuristic, not model-powered
- Metrics are approximate
- Citation quality is inferred from available references
- Full JSON Schema validation is not built in yet
- No real RAG retrieval is performed
- No artifact persistence is performed
- No human approval workflow is implemented

These are acceptable for the first runnable agent because this version establishes the runtime shape and makes the contract executable.

---

# 15. Production Checklist

Before production use:

- Add JSON Schema validation
- Add model-backed generation
- Add retrieval payload support
- Add unit tests
- Add structured logs
- Add trace IDs
- Add tenant-aware policy enforcement
- Add cost accounting
- Add review outcome feedback loops

---

# 16. Summary

The Discovery Agent is now a concrete runtime component. It accepts a ProductPilot workflow request, validates it, generates a structured discovery artifact, calculates metrics, evaluates its own output, and returns a complete stage envelope for the orchestrator.

This gives the ProductPilot system its first runnable agent and a stable pattern for building the rest of the pipeline.

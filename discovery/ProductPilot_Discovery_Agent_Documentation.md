# ProductPilot Discovery Agent Documentation

This is a root-level copy of the Discovery Agent implementation document so it can be opened directly from the workspace root.

For the canonical copy, see:

`docs/Discovery_Agent_Implementation.md`

For the easiest-to-open code file, see:

`ProductPilot_Discovery_Agent.py`

For the package import wrapper, see:

`productpilot/agents/discovery_agent.py`

For the runnable example, see:

`examples/discovery_agent_example.py`

---

# 1. What The Discovery Agent Does

The Discovery Agent is the first agent in the ProductPilot workflow. It takes a goal or feedback summary and turns it into a structured discovery artifact.

It produces:

- Problem statement
- Why-now explanation
- In-scope and out-of-scope boundaries
- Key assumptions
- Open questions
- Success definition
- Evidence map
- Citations
- Metrics
- Evaluation result

---

# 2. How To Run It

From the workspace root:

```bash
python3 examples/discovery_agent_example.py
```

The script prints a JSON response from the agent.

Expected fields:

- `stage_id: discovery`
- `agent_name: DiscoveryAgent`
- `status: success`
- `structured_output.problem_statement`
- `metrics`
- `evaluation`

---

# 3. Main Code API

```python
from productpilot.agents import DiscoveryAgent

result = DiscoveryAgent().run(request)
```

The `request` object must include workflow metadata, intent, context, instructions, budgets, and policy.

---

# 4. Required Request Fields

```json
{
  "workflow_id": "wf_activation_001",
  "tenant_id": "tenant_acme",
  "project_id": "proj_growth",
  "entry_mode": "goal_driven",
  "user_intent": {
    "goal": "Increase activation in the first 7 days.",
    "feedback_summary": null
  },
  "context": {
    "company_context_refs": [],
    "prior_stage_refs": [],
    "retrieval_refs": [],
    "memory_refs": [],
    "source_notes": "Supporting evidence goes here."
  },
  "instructions": {
    "task": "Frame the discovery problem.",
    "constraints": [],
    "success_criteria": [],
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

For goal-driven workflows, `user_intent.goal` is required.

For feedback-driven workflows, `user_intent.feedback_summary` is required.

---

# 5. Output Shape

The agent returns a full stage envelope. The core output looks like this:

```json
{
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
        "source_id": "rag_source",
        "note": "Primary claim for discovery framing."
      }
    ]
  }
}
```

---

# 6. Metrics

The agent calculates:

- `latency_ms`
- `token_input`
- `token_output`
- `input_completeness`
- `output_completeness`
- `citation_coverage`
- `hallucination_risk`
- `confidence_score`
- `problem_clarity_score`
- `scope_precision`
- `assumption_quality_score`
- `evidence_to_claim_ratio`
- `root_cause_confidence`
- `open_question_count`

---

# 7. Evaluation

The agent evaluates each output with:

- Schema validity
- Citation coverage
- Citation quality
- Hallucination risk
- Completeness
- Consistency
- Instruction following
- Confidence calibration
- Business logic score
- Overall score

The evaluation decision can be:

- `pass`
- `warn`
- `fail`

---

# 8. Design Notes

The implementation is deterministic and dependency-free. This makes it easy to run locally and easy to test.

Later, these methods can be replaced with LLM-backed generation:

- `_draft_problem_statement`
- `_draft_why_now`
- `_assumptions`
- `_open_questions`
- `_success_definition`

The public contract should stay the same.

---

# 9. Production Next Steps

- Add full JSON Schema validation
- Add model-backed generation
- Add real RAG retrieval payloads
- Add unit tests
- Add structured logging
- Add trace IDs
- Add cost accounting
- Add orchestrator integration

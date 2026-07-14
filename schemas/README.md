# ProductPilot JSON Schemas

This directory contains the runtime contracts for ProductPilot agents.

## Layout

- `schemas/shared/stage-contract.schema.json` - common workflow envelope
- `schemas/shared/citation.schema.json` - citation objects
- `schemas/shared/evaluation.schema.json` - evaluation results
- `schemas/shared/metrics-base.schema.json` - metrics shared by all agents
- `schemas/agents/*.schema.json` - agent-specific contracts
- `schemas/index.json` - schema for validating a schema manifest
- `schemas/manifest.json` - plain manifest of all generated schema files

## Usage

Each agent schema validates a full stage run object with:

- workflow metadata
- workflow intent and context
- agent input
- agent structured output
- citations
- metrics
- evaluation

The agent-specific files refine the shared stage contract with:

- `stage_id`
- `agent_name`
- agent input shape
- agent output shape
- agent-specific metrics

## Notes

- The schemas target JSON Schema Draft 2020-12.
- `unevaluatedProperties` is used inside nested metric schemas so shared metrics and agent-specific metrics can be combined safely.
- The shared stage contract is intentionally strict so the workflow remains auditable and typed.

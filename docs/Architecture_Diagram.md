# ProductPilot Architecture Diagram

This diagram reflects the current implementation structure in the repository, including the discovery workflow, shared core services, and the productpilot package wrapper.

```mermaid
flowchart TD
    U[User / Client Request] --> A[DiscoveryAgent]

    A --> B[BaseAgent]
    B --> C[Workflow Engine]
    C --> D[Discovery Pipeline]

    D --> D1[Intention Classification]
    D --> D2[Retrieval]
    D --> D3[Evidence Ranking]
    D --> D4[Problem Extraction]
    D --> D5[JTBD Analysis]
    D --> D6[Hypothesis Generation]
    D --> D7[Opportunity Scoring]
    D --> D8[Evaluation]
    D --> D9[Metrics Collection]

    D1 --> E[Discovery Evaluator]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E
    D6 --> E
    D7 --> E
    D8 --> E
    D9 --> E

    E --> F[Discovery Artifact / Response]

    B --> G[Core Logger]
    B --> H[Core Metrics]
    B --> I[Core Config / Utils]

    A --> J[ProductPilot Wrapper]
    J --> K[productpilot/core/workflow.py]
    J --> L[productpilot/core/pipeline.py]
    J --> M[productpilot/core/state.py]

    K --> N[LLM Abstractions]
    K --> O[Retrieval Abstractions]
    K --> P[Prompt Registry]

    Q[Schemas / Data Contracts] --> A
    Q --> D
    Q --> E

    F --> R[Artifacts / Metrics / Evaluation Output]
```

## Implementation Mapping

- Discovery workflow: [discovery/orchestrator.py](../discovery/orchestrator.py)
- Base agent lifecycle: [core/agent.py](../core/agent.py)
- Discovery agent entrypoint: [discovery/agent.py](../discovery/agent.py)
- ProductPilot wrapper: [productpilot/agents/discovery_agent.py](../productpilot/agents/discovery_agent.py)
- Workflow engine: [productpilot/core/workflow.py](../productpilot/core/workflow.py)
- Schemas: [schemas](../schemas)

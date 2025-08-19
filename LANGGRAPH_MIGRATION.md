# LangGraph Migration

## Quick Setup

```bash
# Install
uv pip install langgraph==0.2.16 langgraph-checkpoint-postgres==2.0.2

# Enable
echo "ENABLE_LANGGRAPH=true" >> .env
```

## Integration Points

LangGraph will wrap existing components:

```
src/langgraph/
├── __init__.py       # Factory
├── workflow.py       # Orchestrator
├── nodes/           # Wrap existing components
│   ├── query.py     # Uses qa_system.query_enhancer
│   ├── retrieve.py  # Uses vector_stores.manager
│   └── synthesize.py # Uses qa_system.qa_manager
└── state.py         # Workflow state

```

## Implementation

### Phase 1: Wrap Existing Code

```python
# src/langgraph/nodes/query.py
from ..qa_system.query_enhancer import QueryEnhancer

class QueryNode:
    def __init__(self):
        self.enhancer = QueryEnhancer()

    def process(self, state):
        state["enhanced"] = self.enhancer.enhance(state["question"])
        return state
```

### Phase 2: Add to RAGOrchestrator

```python
# src/rag_system/rag_orchestrator.py
if self.config.get("ENABLE_LANGGRAPH"):
    from ..langgraph import create_workflow
    self.workflow = create_workflow(self.config)
```

### Phase 3: Test Integration

```bash
# Test with existing system
uv run pytest tests/

# Verify Vercel deployment
vercel dev
```

## Benefits

- Reuses ALL existing code
- No breaking changes
- Feature flag controlled
- Clean separation

## Commands

```bash
make dev           # Local development
make test          # Run tests
vercel deploy      # Deploy to Vercel
```

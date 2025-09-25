# Research: GitHub Issue Compliance Agent

## Architecture Decision: Orchestrator Pattern

**Decision**: Use Claude Sonnet 4 orchestrator with GLLM Plugin tools for compliance evaluation
**Rationale**:

- Claude Sonnet 4 provides superior reasoning for complex rule evaluation
- GLLM Plugin framework enables type-safe Python tool integration
- Orchestrator pattern separates concerns: agent handles workflow, tools handle computation
- MCP provides standardized GitHub Projects v2 integration

**Alternatives considered**:

- Pure MCP solution: Limited rule complexity handling
- Direct GitHub API: No Projects v2 support, complex field mapping

## MCP Integration Pattern

**Decision**: Use MCP GitHub Projects v2 connector for read operations (v1.0) and comment posting (v2.0 future)
**Rationale**:

- Native Projects v2 support with field_values array parsing
- Handles authentication and rate limiting
- Standardized connector interface

**Key capabilities verified**:

- Read project items with field_values array (v1.0)
- Filter by status values (v1.0)
- Post comments with mention syntax (v2.0 FUTURE)
- Rate limit handling with exponential backoff (base 2, max 60s, 3 retries) (v1.0)

## Compliance Rule Evaluation Strategy

**Decision**: Deterministic Python functions with explicit timezone handling
**Rationale**:

- Asia/Jakarta (UTC+7) requirement needs consistent implementation
- Rule complexity (rule #5: approval + 7-day check) requires programmatic logic
- Type safety with Pydantic models prevents field access errors

**Date handling approach**:

- Convert all GitHub timestamps to Asia/Jakarta timezone
- Use calendar days (not business days) for 7-day calculations
- Handle null/missing date fields gracefully

## Comment Idempotency Strategy [v2.0 FUTURE]

**Note**: This section applies to v2.0 only. v1.0 does not post comments.

**Decision**: HTML comment markers with violation hash
**Rationale**:

- Prevents duplicate comments on re-runs
- Hash of violations allows updates only when violations change
- Hidden from UI but trackable programmatically

**Format**: `<!-- compliance-agent:{issue_id}:{hash-of-violations} -->`

## Bot Comment Filtering

**Decision**: Maintain configurable bot username list for comment filtering
**Rationale**:

- Rule #7 requires human-only comment detection
- Bot landscape changes frequently, needs configurability
- Default list includes common GitHub bots

**Implementation**: Inline bot patterns in compliance_evaluator.py (no config files in v1.0)

# GitHub Issue Compliance Agent Constitution

## Role Context

You are an **experienced Product Manager and Software Architect specializing in Large Language Model applications**.  
Your role is to ensure that specifications and implementations are:

- Clear, user-focused, and aligned with business value (Product Manager perspective)
- Technically sound, maintainable, and scalable (Software Architect perspective)
- Consistent with established engineering best practices, including **Test-Driven Development** and **SOLID principles**

---

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

- TDD is mandatory: Tests must be written before implementation
- Follow Red-Green-Refactor cycle strictly
- Unit tests required for all public methods with minimum 80% coverage
- Integration tests required for all external API interactions
- Mock external dependencies to ensure deterministic testing

### II. Code Quality Excellence

- All code must include comprehensive type annotations (Python typing)
- Every function/class requires descriptive docstrings
- Defensive programming with explicit error handling is required
- Linting tools (black, flake8, mypy) must pass before commit
- Code coverage target: minimum 80% for all modules

### III. SOLID Principles

All designs and implementations must adhere to **SOLID** principles:

- **Single Responsibility (SRP):** Each class/module has exactly one reason to change
- **Open/Closed (OCP):** Systems are open for extension but closed for modification
- **Liskov Substitution (LSP):** Subtypes must be substitutable for their base types
- **Interface Segregation (ISP):** Favor many focused interfaces over one general-purpose
- **Dependency Inversion (DIP):** Depend on abstractions, not concretions

### IV. Tool-First Architecture

- Business logic implemented as GLLM Plugin tools
- Each tool must be self-contained and independently testable
- Tools expose clear input/output contracts using Pydantic models
- Agent orchestrates tools but contains no business logic itself

### V. Performance Requirements

- Agent operations must complete within 720-second timeout limits
- Memory usage must stay under 100MB per execution
- Agent completion target: 95% of workflows within timeout
- Implement exponential backoff for all external API calls
- Optimize LLM efficiency to minimize reasoning roundtrips

### VI. Prompt Engineering Best Practices

- Tool descriptions must be clear and specify exact input/output formats
- Error messages must be actionable and context-aware
- Prompt templates must be versioned and token-optimized
- System instructions must enforce read-only constraints (v1.0)

---

## Technology Standards

### Python Environment

- Python 3.11+ required for all implementations
- Poetry for dependency management (not pip directly)
- GLLM Plugin Framework from GDP Labs artifact repository
- Zoneinfo for timezone handling (pytz as fallback)

### External Integrations

- MCP for GitHub Projects v2 API access
- AIP CLI (glaip-sdk) for agent deployment and management
- Claude Sonnet 4 as orchestration model
- Exponential backoff with max 60s delay for rate limiting

---

## Development Workflow

### Quality Gates

1. All tests must pass (unit, integration, contract)
2. Linting checks must pass (black, flake8, mypy)
3. Code coverage must meet 80% threshold
4. Performance benchmarks must be validated
5. Read-only constraints must be verified (v1.0)

### Review Requirements

- All code must be reviewed against constitutional principles
- Complexity additions must be justified and documented
- Test coverage reports must be included in reviews
- Performance impact must be assessed

---

## Governance

- This constitution supersedes all other development practices
- Any deviation requires explicit documentation and justification
- Amendments require team consensus and migration plan
- Use quickstart.md for operational guidance

**Version**: 1.1.1 | **Ratified**: 2025-09-25 | **Last Amended**: 2025-09-27

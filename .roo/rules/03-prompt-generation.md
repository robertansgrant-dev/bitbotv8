# Roo Prompt Generator

## Purpose
The Roo prompt generator creates structured, context-rich prompts that Claude can read and act upon. Prompts are written to `.roo/prompts/ACTIVE.md` and archived with timestamps.

## When to Use
Use the `pmt:` prefix when you need Claude to:
- Implement a significant feature
- Debug a complex issue
- Refactor a module
- Generate tests
- Update documentation

**Example**: `pmt: Implement user authentication module`

## Roo Workflow
When a developer uses the `pmt:` prefix, Roo:

1. **Gathers Context**
   - Current project state and file structure
   - Relevant source code files
   - Applicable standards from .roo/rules/
   - Constraints and requirements

2. **Structures the Prompt**
   - **Context**: Project overview, current state, relevant code snippets
   - **Task**: Clear objective and scope
   - **Requirements**: Specific constraints (coding standards, naming, testing)
   - **Code References**: Links to relevant files and line numbers
   - **Success Criteria**: How to know the task is complete

3. **Writes to ACTIVE.md**
   - Overwrites `.roo/prompts/ACTIVE.md` with the new prompt
   - Archives previous prompt to `.roo/prompts/archive/YYYY-MM-DD-HHMMSS-brief-title.md`

## Prompt Structure

### Header
```
# Prompt: [Brief Title]
Generated: [ISO Timestamp]
Task Type: [feature|bugfix|refactor|test|documentation]
```

### Context Section
- Project overview (what does this project do?)
- Current implementation state
- Relevant code snippets (with file and line references)
- Architecture overview if applicable

### Task Section
- Clear objective (what to build/fix/refactor)
- Scope boundaries (what to include, what to exclude)
- Acceptance criteria

### Requirements Section
- Coding standards to follow (reference .roo/rules/01-coding-standards.md)
- Architecture constraints (reference .roo/rules/02-architecture.md)
- Testing requirements (% coverage, test structure)
- Documentation requirements
- Naming conventions to apply

### Code Reference Section
- Links to main files involved
- Current implementation to review
- Examples of existing code patterns

### Success Criteria Section
- Specific, verifiable outcomes
- Testing checklist
- Review checklist

## What Roo DOES NOT Do
- Roo does **not** implement code (Claude does)
- Roo does **not** make architectural decisions (Developer does)
- Roo does **not** validate against the repository (that's for Claude's review)
- Roo does **not** decide what features to build (only structures what developer specifies)

## Archive Structure
Previous prompts are archived with filenames:
```
YYYY-MM-DD-HHMMSS-brief-title.md
```

Example: `2024-03-09-143022-implement-auth-module.md`

This preserves the history of tasks and allows review of what was previously requested.

## Claude Workflow
1. Claude reads `.roo/prompts/ACTIVE.md` for the current task
2. Claude implements according to structure provided
3. Claude follows all standards referenced in Requirements section
4. Developer validates completion against Success Criteria
5. Next `pmt:` call generates a new prompt and archives the previous one

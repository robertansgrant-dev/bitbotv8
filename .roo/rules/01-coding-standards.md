# Coding Standards

## Python Code Style (PEP 8)
- Use 4 spaces for indentation (no tabs)
- Line length: **maximum 100 characters** (enforce with black, flake8)
- Type hints: **required** for all function arguments and return types
- No trailing whitespace
- Max 2 blank lines between top-level definitions

## Naming Conventions (Enforceable)
- **Classes**: PascalCase (e.g., `DataParser`, `ConfigManager`)
- **Functions/Methods**: snake_case (e.g., `process_data()`, `get_user_id()`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_RETRIES = 3`, `DB_TIMEOUT = 30`)
- **Private members**: prefix with underscore (e.g., `_internal_state`, `_helper_method()`)
- **Module names**: lowercase, no hyphens (e.g., `utils.py`, `data_parser.py`)

## Code Organization
- **Imports**: Group in order: stdlib → third-party → local (1 blank line between groups)
- **Docstrings**: All public functions, classes, and modules require docstrings
  - Use triple-quoted strings: `""" Description here """`
  - Include args, returns, and exceptions for non-trivial functions
- **Function length**: Keep under 50 lines (max complexity indicator)
- **Variable names**: Use meaningful names; avoid single-letter vars except loop indices

## Comments
- **Comments explain WHY**, not WHAT (code shows what it does)
- Update comments when code logic changes
- Use inline comments sparingly; prefer clear code over comments
- Use `# TODO:` for incomplete work; use `# FIXME:` for known issues

## Testing
- **All public functions** must have unit tests
- **Minimum 80% code coverage** (measured with pytest --cov)
- **Test file naming**: `test_*.py` (e.g., `test_parser.py`) or `*_test.py`
- **Test location**: tests/ directory mirrors src/ structure
- **Framework**: pytest only; no unittest

## Enforcement
- Run `black` for auto-formatting before commit
- Run `flake8` to catch style violations
- Run `mypy` for type checking
- Run `pytest --cov` before committing code

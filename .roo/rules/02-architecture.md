# Architecture & Project Structure

## Directory Layout (Enforced)
```
project/
├── src/                    # All source code lives here
│   ├── __init__.py         # Package marker (can be empty)
│   └── main.py             # Entry point
├── tests/                  # Mirrors src/ structure
│   └── test_*.py           # Test files
├── docs/                   # Documentation (optional)
├── .roo/                   # AI workflow rules and prompts
│   ├── rules/              # Standards and guidelines
│   │   ├── 00-ai-roles.md
│   │   ├── 01-coding-standards.md
│   │   ├── 02-architecture.md
│   │   └── 03-prompt-generation.md
│   ├── prompts/            # Prompt templates and active prompts
│   │   ├── ACTIVE.md       # Current prompt for Claude
│   │   └── archive/        # Timestamped archive
│   └── results/            # Output from Roo (optional)
├── requirements.txt        # Production dependencies
├── dev-requirements.txt    # Development/test dependencies
├── CLAUDE.md               # AI context and preferences
├── README.md               # Project documentation
├── setup.bat               # Setup script (Windows)
└── .gitignore              # Git ignore rules
```

## Module Organization (Enforced)
- **Single Responsibility Principle**: Each module has one reason to change
- **Meaningful package names**: Use descriptive names (data_parser, auth_service)
- **Avoid circular imports**: If A imports B, B should not import A
- **Public API in __init__.py**: Export what's meant for external use
- **Internal modules prefixed with underscore**: `_internal_helpers.py` (considered private)

## Dependency Management (Enforced)
- **Production dependencies** in requirements.txt only
  - Minimal external dependencies (prefer stdlib)
  - Version pinning for reproducibility: `package==1.2.3`
- **Development dependencies** in dev-requirements.txt only
  - Testing: pytest
  - Linting: flake8, black
  - Type checking: mypy
  - Version pinning: `dev-package==1.2.3`
- **No dev dependencies in src/**: src/ code imports only from requirements.txt
- **Regular updates**: Check for security patches monthly

## Configuration (Enforced)
- **Environment variables**: For secrets and environment-specific config
  - Load from .env file (never commit .env)
  - Use python-dotenv if needed
- **Config separation**: Separate configuration from code logic
- **Multiple environments**: Support dev, test, prod with different configs
- **No hardcoded values**: All magic numbers and strings go in constants or config

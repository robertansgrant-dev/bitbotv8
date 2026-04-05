# Project Template

A template for Python projects using **Roo + Claude Code + Claude.ai** for AI-assisted development.

## Quick Start

### 1. Clone & Rename
```bash
git clone https://github.com/robertansgrant-dev/_project-template.git my-project
cd my-project
```

### 2. Set Up Python Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r dev-requirements.txt
```

### 3. Start Developing
- **Roo (design & planning)**: Open Roo Code, start designing
- **Claude Code (implementation)**: When Roo finishes, paste the prompt into Claude Code
- **Claude.ai (validation)**: Push to git, I'll review

---

## Workflow

### Phase 1: Design with Roo
1. Open Roo in VSCode
2. Chat, explore, design your feature
3. Roo will ask: "Should I save this as `.roo/prompts/01-feature-name.md`?"
4. Approve
5. **Roo explicitly tells you:** "I have created the prompt. Switch to Claude Code to implement it."

### Phase 2: Push to Git
```bash
git add .roo/prompts/01-feature-name.md
git commit -m "[PROMPT] Feature name"
git push
```

### Phase 3: Claude.ai Validates (Optional but recommended)
- I pull the repo and review your design
- I flag conflicts or missing pieces
- You iterate if needed

### Phase 4: Claude Code Implements
1. Open Claude Code in VSCode
2. Paste: "Read `.roo/prompts/01-feature-name.md` and implement it according to `.roo/rules/`. Write results to `.roo/results/01-feature-name.md`. Commit and push when done."
3. Claude Code executes, writes results, commits, pushes

### Phase 5: Roo Reviews & Iterates
1. Read results in `.roo/results/01-feature-name.md`
2. If approved: done
3. If issues: Tell Roo "Claude Code built this [show results]. Needs changes: [describe]. Update `.roo/prompts/01-feature-name.md`"
4. Roo redesigns, Claude Code reimplements
5. Loop until done

---

## Project Structure
```
my-project/
├── .roo/
│   ├── rules/                  # Read-only constraints for all AIs
│   │   ├── 00-ai-roles.md      # Who does what
│   │   ├── 01-coding-standards.md
│   │   └── 02-architecture.md
│   ├── prompts/                # Roo writes, Claude Code reads
│   │   └── README.md
│   └── results/                # Claude Code writes summaries
│       └── README.md
├── src/                        # Your implementation
│   ├── __init__.py
│   └── main.py
├── tests/                      # Test files
├── docs/                       # Documentation
├── CLAUDE.md                   # Claude Code context (DO NOT ALTER)
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── dev-requirements.txt        # Testing/linting tools
└── .gitignore
```

---

## Important Notes

### Starting Each Roo Session
Paste this into Roo at the start to remind it of its role:
```
You are Roo Code in a three-AI system:
- Your role: Design, research, prompt writing (no code)
- Claude Code's role: Implementation only
- Claude.ai's role: Validation and oversight

When you finish designing, explicitly state:
"I have created the prompt in .roo/prompts/01-feature-name.md.
Switch to Claude Code to implement it."
```

### Triggering Claude Code
After Roo finishes and you've pushed to git:

Open Claude Code and paste:
```
Read .roo/prompts/01-feature-name.md and implement it.
Follow all standards in .roo/rules/.
Write results summary to .roo/results/01-feature-name.md.
Commit with message: "[FEAT] Feature name - implementation complete"
Push to main.
```

### Iterating
When Claude Code's output needs refinement:

1. Review `.roo/results/01-feature-name.md`
2. Tell Roo: "Claude Code's implementation had issues [describe]. Update `.roo/prompts/01-feature-name.md`"
3. Roo redesigns
4. Tell Claude Code to re-implement
5. Loop until satisfied

---

## Rules & Constraints

**Read before starting:**
- `.roo/rules/00-ai-roles.md` — AI responsibilities and limitations
- `.roo/rules/01-coding-standards.md` — Code quality standards
- `.roo/rules/02-architecture.md` — Design principles

---

## Testing
```bash
pytest
pytest --cov=src
pytest tests/test_models.py -v
```

---

## Dependencies

Core (customize as needed):
- Python 3.9+
- Flask or FastAPI (if building web app)
- SQLAlchemy (if using databases)

Dev:
- pytest
- black
- flake8

---

## Important Files (DO NOT ALTER)

- `CLAUDE.md` — Claude Code context
- `.roo/rules/00-ai-roles.md` — AI role definitions
- `.roo/rules/01-coding-standards.md` — Code standards
- `.roo/rules/02-architecture.md` — Architecture guidelines

---

## Version
- v1.0: Template created 2026-03-09

# AI Roles & Responsibilities

This project uses a three-AI system. Each AI has a distinct, non-overlapping role.

---

## Roo Code — Design & Planning
- Research, explore, and design features
- Write structured prompts to `.roo/prompts/`
- **No code generation** — design only
- When design is complete, explicitly state:
  > "I have created the prompt in `.roo/prompts/01-feature-name.md`. Switch to Claude Code to implement it."

## Claude Code — Implementation
- Read prompts from `.roo/prompts/`
- Implement code according to `.roo/rules/` standards
- Write results summaries to `.roo/results/`
- Commit and push when implementation is complete
- **No design decisions** — implement what Roo specified

## Claude.ai — Validation & Oversight
- Review designs and implementations on request
- Flag conflicts, gaps, or quality issues
- Provide guidance on architecture and standards
- **No direct code changes** — advise only

---

## Developer Role (Final Authority)
- Define requirements and set priorities
- Approve designs before implementation begins
- Review and sign off on all implementations
- Decide when to iterate vs. ship

---

## Workflow Summary
1. **Roo** designs → writes prompt → tells you to switch
2. **You** push prompt to git
3. **Claude.ai** validates (optional)
4. **Claude Code** reads prompt → implements → commits → pushes
5. **Roo** reviews results → iterates if needed
6. **You** approve final output

---

## Boundaries
| Decision | Owner |
|---|---|
| What to build | Developer |
| How to design it | Roo |
| How to implement it | Claude Code |
| Whether it's correct | Claude.ai + Developer |

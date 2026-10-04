---
name: documentation
description: Playbook for generating project documentation (README, setup, API docs). Use when producing the generated project's README.md and docs.
---

# Documentation

Produce clear documentation for the generated project by reading all upstream
artifacts (`requirements.md`, `architecture.md`, `tasks.md`, `src/`,
`test-report.md`, `security-review.md`).

## README.md structure

1. **Overview** — what the project does and who it is for.
2. **Features** — bullet list tied to the requirements.
3. **Tech stack** — from the technology steering / architecture.
4. **Project structure** — annotated tree.
5. **Setup** — prerequisites and install steps.
6. **Run** — how to start the app.
7. **Test** — how to run the test suite.
8. **API reference** — endpoints from architecture.md (method, path, inputs, outputs, errors).
9. **Security notes** — summary from security-review.md.

## Quality bar

- Setup and run instructions must be accurate for the actual code produced.
- Keep it practical; a new developer should be able to run and test the project.

## Remember

- Write the artifact metadata header on README.md.
- Do not modify source code; documentation only.

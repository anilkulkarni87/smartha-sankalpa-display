## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.

## Project setup and conventions

- Use `./scripts/graphify` in this repo instead of assuming a global Graphify command exists. Follow DEVELOPMENT.md to install the pinned development tool after cloning.
- The graph is local/generated and ignored by Git. Build it with `./scripts/graphify extract . --code-only --max-workers 2`; run `./scripts/graphify update .` after code changes. Use `cluster-only . --no-label` for reports without external model calls.
- Runtime: FastAPI serves index.html and all API routes. Vercel uses Python 3.12 and the checked-in vercel.json. Graphify is excluded from the deployment.
- Keep the user's supplied family wording as the sole built-in reader choice. Preserve country-scoped named variations, all three scripts, highlighted dynamic fields and calendar-only audio.
- Preserve DrikGanita conventions and review gates described in DEVELOPMENT.md and ACCURACY.md. Partial comparison is not full-year validation. Do not open holdout answers before the release gate passes.
- Never commit tokens, .env files, generated audio or virtual environments. Use HF_TOKEN only on the server; do not put credentials in client code or documentation.
- Run meaningful offline regression checks before committing. Live audio/reference requests need an actual task reason; avoid spending provider quota on routine tests.

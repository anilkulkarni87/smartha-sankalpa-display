# Working on this project

## Local display and checks

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python run.py --port 9000
```

Open http://localhost:9000/. Tests are run with `.venv/bin/python -m unittest discover -v`.
The current suite uses offline fixtures and audio stubs; it does not spend live provider quota.

## Graphify

The official package for [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) is **graphifyy**, not `graphify` on PyPI. It is a development tool and is not installed on Vercel.

One-time setup after cloning:

```bash
python3 -m venv .venv-graphify
.venv-graphify/bin/python -m pip install -r requirements-tools.txt
./scripts/graphify extract . --code-only --max-workers 2
./scripts/graphify cluster-only . --no-label
```

The Codex skill is project-scoped under `.codex/skills/graphify/`; `AGENTS.md` records graph-first navigation. The wrapper works without a global Graphify install. `.graphifyignore` excludes environments, cache files, tool internals and bulk reference data. Code-only extraction and `--no-label` keep this setup deterministic and local; they do not send source or documents to a cloud model.

Before broad source searches, query the graph:

```bash
./scripts/graphify query 'calendar calculation and recital data flow' --budget 1500
./scripts/graphify explain 'AudioService'
./scripts/graphify path 'calculate()' 'calendar_audio_text()'
```

After code changes:

```bash
./scripts/graphify update .
./scripts/graphify cluster-only . --no-label
```

Open `graphify-out/graph.html` for the visualization and `graphify-out/GRAPH_REPORT.md` for the generated architecture report. Generated graph files are local and ignored by Git; rebuild them after cloning. The source, project-scoped skill, tool version and rebuild commands are committed. The graph covers code relationships; documentation has not undergone a semantic extraction pass.

## Calendar and wording conventions

DrikGanita is the selected reference, using Kannada/Amanta, geometric-centre sunrise, solar Ritu and exact regular-Chaitra conjunction for Samvatsara turnover. Vara follows the city's local calendar date. The family's supplied US wording is the default; other countries retain neutral geography. Keep changing fields as placeholders and preserve the three scripts. Calendar-only audio includes the eight changing phrases, not personal or fixed wording.

Read `ACCURACY.md` and `validation/reports/SUMMARY.md` before making accuracy claims. External coverage is incomplete. Reserved answers remain unreleased; teacher wording/pronunciation and Kshaya recital review remain pending.

Secrets, local audio, virtual environments, scratch files, deployment links and generated graph caches are excluded from commits. `.env.example` contains placeholders only. The app does not automatically load `.env` files; export environment variables for local use or configure them in Vercel.

# Contributing to pico-nlu

Thanks for contributing! This document covers the tooling commands, commit conventions,
and branch/PR flow that keep pico-nlu consistent. For architecture decisions, dependency
tiers, and the public API contract, see [`ARCHITECTURE.md`](./ARCHITECTURE.md) — it is the
normative source of truth and this document does not re-state it.

---

## 1. Setup

pico-nlu uses a PEP 621 `src/` layout and supports Python 3.11+.

**Core install (no torch):**

```bash
pip install -e ".[dev]"
```

**Neural install (adds `torch` for the BiLSTM-CRF slot filler):**

```bash
pip install -e ".[dev,neural]"
```

> The `[neural]` extra is required only for work on `pico_nlu/neural/*` or for running
> neural-marked tests. Core pico-nlu MUST NOT import `torch` (see
> [ARCHITECTURE.md §4.1](./ARCHITECTURE.md#41-core-must-not-import-torch)).

If you also need the future transformer-based classifier, add the `transformer` extra:

```bash
pip install -e ".[dev,neural,transformer]"
```

`uv` users can substitute `uv pip install -e ...` for any of the above.

---

## 2. Quality Gates

Every change MUST pass these three commands before pushing. They are the same commands
the CI pipeline runs.

### Lint — `ruff`

```bash
ruff check .
```

Ruff replaces flake8 / isort / pylint. Configuration lives in `pyproject.toml` under
`[tool.ruff]`. To auto-fix safe violations:

```bash
ruff check . --fix
```

### Type check — `mypy`

```bash
mypy src/pico_nlu
```

mypy runs on the non-neural modules only (neural code may use torch types that are not
installed in core CI). The public API surface is checked strictly; see
[ARCHITECTURE.md §3](./ARCHITECTURE.md#3-public-api-contract) for what counts as public.

### Tests — `pytest`

```bash
pytest
```

Tests marked `@pytest.mark.neural` auto-skip when `torch` is not installed, so the default
`pytest` invocation works in both core-only and neural environments. To run only the fast
core suite (skipping neural explicitly):

```bash
pytest -m "not neural"
```

To run the full neural suite, install the `[neural]` extra first, then:

```bash
pytest
```

Coverage is collected via `pytest-cov`; see `pyproject.toml` `[tool.pytest.ini_options]`
for the exact flags.

---

## 3. Commit Conventions

pico-nlu follows **Conventional Commits**. Each commit message MUST use this format:

```
<type>(<optional scope>): <short imperative summary>

<optional body explaining why, not what>

<optional footer(s)>
```

### Allowed `<type>` values

| Type | Use for |
|---|---|
| `feat` | A new feature (maps to a MINOR SemVer bump). |
| `fix` | A bug fix (maps to a PATCH SemVer bump). |
| `docs` | Documentation-only changes (ARCHITECTURE.md, CONTRIBUTING.md, PRDs, docstrings). |
| `refactor` | Code restructuring that changes neither behavior nor public API. |
| `perf` | Performance improvement that does not change public behavior. |
| `test` | Adding or correcting tests. |
| `build` | Packaging, dependency pinning, `pyproject.toml` tooling config. |
| `ci` | CI pipeline changes. |
| `chore` | Repo maintenance that does not fit another type (e.g. `.gitignore`). |
| `revert` | Reverting a previous commit. |

### Allowed `<scope>` values (optional)

Lowercase, kebab-case, and SHOULD match a module or PRD area. Examples:
`engine`, `dataset`, `slot-filler`, `neural`, `persistence`, `cli`, `errors`,
`tokenizer`, `builtin-entities`, `prd-00`, `prd-01`.

### Rules

- The summary line is **≤ 72 characters**, imperative mood ("add" not "added").
- The body wraps at 100 characters and explains **why** the change is needed.
- **Breaking changes** use a `!` after the type/scope AND a `BREAKING CHANGE:` footer, e.g.
  `feat(engine)!: drop positional arg to parse` with footer
  `BREAKING CHANGE: Engine.parse now requires a keyword-only text argument.`
- Reference issues or PRDs in the footer: `Refs: PRD-03`, `Closes #42`.

### Examples

```
feat(intent-classifier): add calibrated probabilities to parse output
```

```
fix(persistence): refuse blobs with mismatched MODEL_FORMAT_VERSION

Engine.load was silently accepting older blobs. Now it raises
PersistenceError naming both expected and encountered versions,
per ARCHITECTURE.md §4.2.

Refs: PRD-01
```

```
docs: ratify ARCHITECTURE.md stack table (PRD-00)
```

---

## 4. Branch & PR Flow

### Branch naming

Create a branch off `main` named `<type>/<short-description>` or `<type>/PRD-<nn>-<slug>`:

```
feat/prd-03-calibrated-intent-probs
fix/persistence-version-check
docs/prd-00-ratify-architecture
```

### Pull request flow

1. **Open a PR** against `main` as soon as the change is reviewable — drafts are welcome.
2. **PR title** SHOULD match the commit Conventional Commit summary (e.g.
   `feat(intent-classifier): add calibrated probabilities`). Squash-merge is the default,
   so the PR title becomes the squashed commit message.
3. **PR description** SHOULD reference the PRD/user story it implements (e.g.
   `Implements US-003 of PRD-03`) and call out any deviation from the PRD's acceptance
   criteria.
4. **Do not push directly to `main`.** All changes go through PR review.
5. **Do not rebase or force-push** a branch after review has started unless asked; add new
   commits so reviewers can diff between review rounds. The squash-merge at merge time
   produces a clean history.

### Required CI checks

Every PR MUST pass the following before merge. They mirror the local Quality Gates in §2.

| Check | Command | Notes |
|---|---|---|
| Lint | `ruff check .` | Must report zero violations. |
| Type check | `mypy src/pico_nlu` | Strict on public API modules. |
| Tests | `pytest` | Neural tests auto-skip without torch. |
| Core-import-torch guard | (CI script) | Fails if `import torch` appears outside `pico_nlu/neural/` (ARCHITECTURE.md §4.1). |

A PR that touches `pico_nlu/neural/*` additionally runs the neural tests against a
`.[dev,neural]` environment.

### Review checklist (for reviewers)

- [ ] Public API changes are documented in `ARCHITECTURE.md §3` and noted in the PR.
- [ ] No `import torch` outside `pico_nlu/neural/`.
- [ ] New persisted fields bump `MODEL_FORMAT_VERSION` if the blob layout changes.
- [ ] New dependencies appear in `ARCHITECTURE.md §1` first, then `pyproject.toml`.
- [ ] Tests added for any new behavior; neural tests marked `@pytest.mark.neural`.

---

## 5. References

- [`ARCHITECTURE.md`](./ARCHITECTURE.md) — stack table, dependency tiers, package layout,
  public API contract, hard rules.
- Source engineering PRDs: [`prd/`](./prd/) (PRD-00 through PRD-11).
- Task breakdowns: [`tasks/`](./tasks/).

# pico-nlu Architecture & Conventions

This document is the **normative source of truth** for pico-nlu's technical decisions,
package layout, and public API contract. It is ratified by PRD-00 and referenced by all
subsequent PRDs (01–11). If any PRD contradicts this document, update this document first
and re-read the affected PRDs.

---

## 1. Tech Stack

| Concern | Choice | Notes |
|---|---|---|
| Language | **Python 3.11+** | Hard floor; uses `match`, `tomllib`, modern typing (`X | None`) |
| Dataset schema / configs | **Pydantic v2** (`pydantic>=2.5,<3`) | Validation + serde for free |
| Intent classification | **scikit-learn** `LogisticRegression` (`scikit-learn>=1.3,<2`) | Core dep |
| Vectorization | scikit-learn `TfidfVectorizer` / `CountVectorizer` | Core dep |
| Tokenization | **Pure-Python** Unicode regex tokenizer (in-package, `regex>=2023.1`) | No Rust binary deps |
| Slot filling | **BiLSTM-CRF** via `torch` (`torch>=2.1,<3`) | Behind `[neural]` extra |
| Builtin entities — numbers | `word2number>=1.1` | Core dep |
| Builtin entities — datetime | `dateparser>=1.1,<2` | Core dep; ~50 MB with locales (accepted for v1) |
| Persistence (v1) | **`joblib`** (`joblib>=1.3,<2`) | Single-file blob; v2 (JSON+arrays) is future work |
| Packaging | **PEP 621** `pyproject.toml`, `src/` layout, **`hatchling`** build backend | No `setup.py` |
| Lint | **ruff** | Replaces flake8/isort/pylint |
| Types | **mypy** (strict on public API) | |
| Tests | **pytest** + `pytest-cov` | |
| Dev tooling | `uv` (recommended) or `pip` | |

### Dependency tiers

**Core dependencies** (installed by default; MUST NOT require `torch`):

```toml
[project]
dependencies = [
    "pydantic>=2.5,<3",
    "scikit-learn>=1.3,<2",
    "joblib>=1.3,<2",
    "word2number>=1.1",
    "dateparser>=1.1,<2",
    "regex>=2023.1",   # Unicode tokenizer
]
```

**Optional extras:**

```toml
[project.optional-dependencies]
neural = [
    "torch>=2.1,<3",
    # transformers is OPTIONAL even within neural — only required for the future
    # transformer-based intent/token classifier in PRD-11, gated by a tighter extra.
]
transformer = ["transformers>=4.36,<5"]   # future, PRD-11
dev = ["pytest>=7", "pytest-cov", "ruff", "mypy", "types-regex"]
```

> **FR-1 (normative):** Every core dependency and the `[neural]` / `[transformer]` extras
> with pinned ranges appear above. No PRD may introduce a core (non-extra) dependency not
> listed here without updating this section first.

### Build backend decision

**Decision: `hatchling`.**

Rationale: hatchling is the modern PEP 621-native backend, has no legacy `setup.py`
baggage, plays well with `src/` layout, and is the default recommended by the PyPA
packaging guide. `setuptools` remains a fallback if a blocker is discovered during
PRD-01 bootstrap.

---

## 2. Package Layout

The `src/` layout is used so that the installed package and the local source tree cannot
shadow each other during testing.

```
pico-nlu/
├── pyproject.toml
├── README.md
├── LICENSE
├── ARCHITECTURE.md            # this document
├── CONTRIBUTING.md
├── src/pico_nlu/
│   ├── __init__.py            # re-exports public API: Engine
│   ├── __about__.py           # __version__
│   ├── engine.py              # PicoNLU: fit / parse / persist / load
│   ├── dataset.py             # Pydantic models for the Snips-format dataset
│   ├── tokenizer.py           # Unicode regex tokenizer
│   ├── featurizers.py         # composable feature extractors
│   ├── intent_classifier.py   # LogisticRegression-backed intent classifier
│   ├── entity_parser.py       # gazetteer + builtin entity parsing
│   ├── slot_filler.py         # SlotFiller ABC + BIO codec
│   ├── builtin_entities/
│   │   ├── __init__.py        # registry + BuiltinEntityParser
│   │   ├── number.py          # word2number-backed
│   │   └── datetime.py        # dateparser-backed
│   ├── persistence.py         # joblib save/load + MODEL_FORMAT_VERSION
│   ├── metrics.py             # intent accuracy + slot F1
│   ├── cli.py                 # `pico-nlu train|parse|eval`
│   ├── errors.py              # typed exception hierarchy
│   └── neural/                # ONLY imported when [neural] extra is present
│       ├── __init__.py        # torch-availability guard
│       ├── nn.py              # BiLSTM-CRF model
│       ├── embeddings.py      # char + word vocab + embeddings
│       ├── trainer.py         # generic training loop
│       └── slot_filler.py     # implements slot_filler.SlotFiller
└── tests/
    ├── unit/                  # fast, isolated, no model training beyond toy data
    ├── integration/           # end-to-end fit → parse → persist → load → parse
    └── datasets/              # minimal sample datasets (adapted from Snips)
```

The implemented tree MUST conform to this layout. New modules require an update to this
document.

---

## 3. Public API Contract

> **Stability promise:** The names and signatures below are **stable after Phase 1**.
> Internal modules (`pico_nlu.featurizers`, `pico_nlu.neural.*`, etc.) are NOT stable;
> users should import only from the top-level `pico_nlu` package.

### `Engine` (the single high-level entry point)

```python
from pico_nlu import Engine

engine = Engine(language="en")            # optional config in later PRDs
engine = engine.fit(dataset)              # dataset: Snips-compatible dict OR Dataset model
result = engine.parse("turn on the kitchen light")
engine.persist("/path/to/model.pico")     # joblib blob (v1)
engine2 = Engine.load("/path/to/model.pico")
```

Stable methods (signatures locked after Phase 1):

| Method | Purpose |
|---|---|
| `Engine(language: str = "en")` | Construct an untrained engine. |
| `Engine.fit(dataset) -> Engine` | Train on a Snips-compatible dataset; returns a fitted engine. |
| `Engine.parse(text: str) -> dict` | Parse a single utterance; returns the result dict below. |
| `Engine.persist(path: str | Path) -> None` | Save the model as a versioned joblib blob. |
| `Engine.load(path: str | Path) -> Engine` *(classmethod)* | Load and verify a joblib blob. |

`parse` result shape (stable after Phase 1 for `intent`, Phase 2 for `slots`):

```python
{
    "intent": {"name": str, "probability": float},
    "slots": [
        {
            "entity": str,
            "slot_name": str,
            "text": str,
            "range": [int, int],   # [start, end) char offsets
            "value": Any,          # coerced value (number, datetime, raw str, ...)
            "builtin": bool,
        }
    ],
}
```

### Typed exception hierarchy

All public exceptions live in `pico_nlu.errors` and inherit from `PicoError`.

| Exception | Raised when |
|---|---|
| `PicoError` | Base class for every pico-nlu exception. |
| `DatasetValidationError` | A dataset fails Pydantic validation; carries the path to the offending field. |
| `ModelNotTrainedError` | `parse` / `persist` is called before `fit`. |
| `PersistenceError` | A blob cannot be read or written (I/O, corrupt file, etc.). |
| `ExtraNotInstalledError` | A neural component is used without `torch` installed; message tells the user `pip install pico-nlu[neural]`. |

> **FR-2 (normative):** The public API surface is fully enumerable from this section
> (names + signatures). Internal modules are explicitly out of the stability promise.

---

## 4. Hard Rules

These rules are non-negotiable; violations fail code review.

### 4.1 Core must not import torch

**Rule:** Importing `pico_nlu` core — any module outside `pico_nlu/neural/` — MUST NOT
import `torch`, directly or transitively. Only `pico_nlu/neural/*` may import `torch`,
and it MUST degrade gracefully (raise `ExtraNotInstalledError` with a clear install
hint) when the `[neural]` extra is missing.

**Enforcement:**
- Code review: any PR adding `import torch` outside `pico_nlu/neural/` is rejected.
- CI (to be wired in PRD-01): a grep-based guard fails the build if `import torch`
  appears outside `pico_nlu/neural/`.

> **FR-3 (normative):** The "core must not import torch" rule is a hard constraint,
> stated above and enforced in CI.

### 4.2 Model format versioning is decoupled from library version

Two independent version numbers exist:

1. **Library version** — `pico_nlu.__version__` (SemVer, lives in `__about__.py`).
2. **Model format version** — `pico_nlu.persistence.MODEL_FORMAT_VERSION` (a plain
   integer). Bumped on *any* breaking change to the persisted blob layout. **Not**
   bumped on library releases that keep the blob format compatible.

v1 blob layout:

```python
joblib.dump({
    "format_version": int,     # == MODEL_FORMAT_VERSION at save time
    "lib_version": str,        # pico_nlu.__version__ at save time
    "payload": {...},          # model artefacts
}, path)
```

`Engine.load` MUST refuse blobs whose `format_version` is incompatible with the current
`MODEL_FORMAT_VERSION`, raising `PersistenceError` with a message that names both the
expected and encountered versions.

---

## 5. Error Handling Conventions

- Validation failures raise `DatasetValidationError` with a path to the offending field.
- Calling `parse` before `fit` raises `ModelNotTrainedError`.
- Using a neural component without torch raises
  `ExtraNotInstalledError("Install with: pip install pico-nlu[neural]")`.

---

## 6. Testing Conventions

- `tests/unit/` — fast, isolated, no model training beyond toy data.
- `tests/integration/` — end-to-end `fit → parse → persist → load → parse` on sample datasets.
- Neural tests MUST be marked `@pytest.mark.neural` and auto-skip when torch is unavailable.
- One tiny dataset (≤ 3 intents, ≤ 10 utterances each) lives in `tests/datasets/` for the
  fast suite. A copy of Snips's `lights_dataset.json` is adapted for the integration suite.

---

## 7. References

- Source engineering PRD: `prd/PRD-00-architecture-and-conventions.md`
- Snips NLU lineage (ancestor project; pico-nlu drops its Rust deps and Python 2 code)
- Tooling configuration (`pyproject.toml` `[tool.ruff]`, `[tool.mypy]`, `[tool.pytest]`)
  lands in PRD-01 per the Non-Goals of PRD-00.

# Replay-Core Storage Optimization for Joint Historical Queries in Time-Series Databases

Replay-Core studies how a time-series database should retain sensor histories when an incident query needs **several channels over the same historical window**. Each channel can use a different age-dependent sampling profile, but a replay query succeeds only when every required channel meets its fidelity requirement. The goal is to maximize the value of complete replay queries within a shared storage budget.

## 🔍 Problem

A high-rate voltage trace alone cannot replay an incident when the matching current trace is missing. Replay-Core treats the required sensor windows as a joint contract and chooses a retention profile for each sensor.

For a sensor profile $p_g$, let $c_g(p_g)$ be its storage cost. An incident $z$ contributes weight $w_z$ only when every sensor in its required set $S_z$ satisfies its local age-fidelity requirement:

$$
\max_{\mathbf p}\sum_z w_z \prod_{g\in S_z}s_{zg}(p_g)
\qquad\mathrm{s.t.}\qquad \sum_g c_g(p_g)\le B.
$$

## ✨ Main contributions

- **🧬 Replay-semantic profile reduction.** Compile each candidate age-fidelity profile into a vector of satisfied incident requirements. Merge profiles with identical signatures and remove cost-signature dominated choices.
- **🕸️ Replay-core contraction.** Express replay requirements as sensor–incident factors and simplify the interaction graph using four exact rules: vacuous edges, impossible incidents, fixed-profile sensors, and duplicate incident factors.
- **⚙️ Structure-aware exact optimization.** Choose between primal and incidence decompositions using mixed-domain state estimates. The paper develops price-form and hard-budget dynamic programs and evaluates mixed-integer optimization as an alternative.

## 🗂️ Repository structure

```text
Replay-Core/
├── 📘 README.md                       # Project overview and commands
├── 🧩 reference_impl/
│   ├── __init__.py
│   └── replay_core.py                 # Small-instance exhaustive reference
├── 🚀 scripts/
│   ├── __init__.py
│   └── run_reference.py              # CLI for the reference model
├── ✅ tests/
│   ├── __init__.py
│   └── test_reference.py             # Profile and optimum checks
└── 📊 data/
    ├── README.md                      # Data provenance
    ├── examples/
    │   ├── replay_profiles.json       # Synthetic replay catalog
    │   └── expected_output.json       # Reference output
    └── archived_results/
        ├── case_quality.csv
        ├── fair_reoptimization_18.json
        └── nonlocal_reoptimization.json
```

## 🚀 Quick start

The bundled reference uses **Python 3.10+** and only the standard library. Run these commands from the repository root.

**1. Run the tests**

```bash
python -m unittest discover -s tests -v
```

**2. Check the sample storage-budget problem**

```bash
python -m scripts.run_reference --input data/examples/replay_profiles.json
```

The command reports the best profile assignment for the raw catalog, the signature quotient, and the skyline-pruned catalog. For the included example, all three attain replay utility **16** with storage cost **9**.

**3. Try a storage price or a different input catalog**

```bash
python -m scripts.run_reference --input data/examples/replay_profiles.json --mode price --price 1
python -m scripts.run_reference --input path/to/your_profiles.json --cap 100000
```

`--cap` limits the number of profile combinations explored by the exhaustive reference. Larger catalogs can exceed this limit.

## 🧪 Reference implementation

The included Python code checks the local semantics of the problem on small inputs:

- Piecewise age-fidelity satisfaction for each sensor and incident.
- Signature-based equivalence and cost-aware skyline pruning.
- Exhaustive optimization for hard-budget and memory-price objectives.
- Unit tests that compare reduced catalogs against the original search space.


## 📊 Data and recorded results

`data/examples/` contains synthetic inputs for code checks. `data/archived_results/` contains three earlier, saved experiment tables/records. The latter are retained for reference and are not needed to execute the Python tests.

See [data/README.md](data/README.md) for file provenance and limitations. Raw historian traces and full experiment-generation scripts were not included in the supplied source archive.

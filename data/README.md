# Data in this repository

## 🧪 Example catalog

- `examples/replay_profiles.json`: a synthetic two-sensor catalog with three replay contracts. The JSON defines `budget`, per-sensor `id`/`cost`/`segments`, and incident `weight`/`requirements`.
- `examples/expected_output.json`: expected output for the default exhaustive reference run, included as a regression check.

These are small correctness fixtures, not measured time-series data.

## 📊 Archived result records

- `archived_results/case_quality.csv`: historical per-case ratio table, copied from `R59_CASE_POINTS_108.csv`.
- `archived_results/fair_reoptimization_18.json`: historical synthetic 18-case reoptimization results, copied from `B_FAIR_REOPTIMIZED_18.json`.
- `archived_results/nonlocal_reoptimization.json`: historical synthetic cross-component reoptimization results, copied from `B_NONLOCAL_REOPTIMIZED.json`.

The three files are **saved outputs from an earlier experiment archive**, not raw training/test datasets and not input files for the supplied Python reference. Their contents were copied unchanged. The scripts that generated them are not present in the supplied archive.

The repository does not include the native-engine traces, full benchmark inputs, or complete scripts needed to rerun the results reported in the manuscript.

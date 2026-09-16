# Run inference

**English** | [Português](INFERENCE.pt-BR.md)

The prediction command loads a trusted pipeline, validates its accompanying decision and applies the selected approval threshold **0.60**. It never fits a model or evaluates the final holdout.

## Try the public input without a model

Install the pinned environment from the [README](../README.md), then run from the repository root with that environment's Python:

```text
python -m topvistos.predict --input examples/synthetic_cases.csv --check-input
```

This checks three entirely fictional cases and returns `input_valid: true`, without requiring competition files or a serialized model. It performs no prediction.

The [input CSV](../examples/synthetic_cases.csv) and [illustrative prediction CSV](../examples/synthetic_predictions.csv) are public. They contain invented identifiers and features, not copied competition cases. The third case intentionally exercises an unknown category, a negative employee count and a missing wage. There are no ground-truth labels and these examples establish no predictive performance.

## Predict with the recorded artifact

With your trusted local artifact available at the example path:

```text
python -m topvistos.predict --input examples/synthetic_cases.csv --model reports/generated/selection-verified/selected_pipeline.joblib --output reports/generated/inference/example.csv
```

The default decision is [the recorded decision](selection/decision.json). The command verifies training-source hashes, dependency versions, artifact hash, model class, selected parameters and probability-column order before returning predictions. The artifact used for the published study is not distributed in Git.

Output columns:

| Column | Meaning |
|---|---|
| `id_do_caso` | Input identifier, with input order preserved |
| `approval_probability` | Model probability for the historical approved label |
| `predicted_status` | Aprovado if probability >= 0.60; otherwise Negado |
| `decision_threshold` | Applied threshold |
| `artifact_origin` | recorded if bytes match the historical artifact; rebuilt otherwise |

The command requires unique nonblank string IDs followed by exactly the ten documented features, in the example order. Target columns, duplicate headers, malformed rows and invalid numeric values are rejected. Empty feature cells are missing values; unknown categorical values use the existing pipeline behavior. An existing output file is never overwritten.

## Rebuilt artifacts versus the historical artifact

Readers with authorized competition data can reproduce development using the documented baseline/selection commands. A newly serialized pipeline may differ in bytes across environments. For inference with a locally rebuilt pipeline, pass the matching generated decision:

```text
python -m topvistos.predict --input examples/synthetic_cases.csv --model reports/generated/selection/selected_pipeline.joblib --decision reports/generated/selection/decision.json --output reports/generated/inference/rebuilt-example.csv
```

Only the artifact byte hash may differ from the recorded decision: the selected configuration, threshold, training source hashes, data hash and partition identities must match. The output explicitly labels different bytes as `rebuilt`. This is inference compatibility, not proof of identical predictions or a new evaluation result. The [final-evaluation](EVALUATION.md) checks remain strict and unchanged.

Only load models and decision files from a trusted source. A matching hash checks correspondence; it does not make a pickle-based artifact safe. See [scikit-learn persistence guidance](https://scikit-learn.org/stable/model_persistence.html).

## Verification scope

The test suite runs with artificial fixtures and no competition dataset. It covers threshold equality, ID order, missing/unseen values, schema errors, artifact mismatch and output preservation. The CLI input check is included in the automated suite.

A separate clean checkout and fresh Python environment are used to verify the public input and prediction command with the existing frozen artifact. This does not repeat training, candidate selection or final evaluation on the original data.

The predictions model historical labels and are not validated for visa eligibility or individual immigration decisions. Read the [final report](EVALUATION.md) for error rates, calibration and segment limitations.
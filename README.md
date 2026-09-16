# TopVistos EUA — Visa Outcome Classification

**English** | [Português](README.pt-BR.md)

A reproducible classification study built from the 2023 **ML Olympiad for Students — TopVistos EUA** Kaggle project. The current implementation separates training, validation, and a final holdout, fits preprocessing inside each training fold, and compares a bounded set of models with explicit threshold selection.

## Final evaluation

The selected gradient-boosting model achieved **0.701 macro F1** on **3,568 final-holdout cases**, with a 95% bootstrap interval of **0.686–0.717**. The approval threshold **0.60** was fixed using validation data before final evaluation.

| Final-holdout metric | Prior / 0.50 | Logistic / 0.50 | Selected boosting / 0.60 |
|---|---:|---:|---:|
| Macro F1 | 0.401 | 0.672 | 0.701 |
| F1 — approved class | 0.802 | 0.817 | 0.808 |
| ROC-AUC | 0.500 | 0.762 | 0.773 |
| Recall — denied class | 0.000 | 0.443 | 0.576 |
| Recall — approved class | 1.000 | 0.881 | 0.820 |

The selected model identifies more denied cases than logistic regression while also misclassifying more approved cases. Performance varies substantially by education group: aggregate improvements do not establish suitability for individual decisions.

![Final performance and calibration](docs/evaluation/evaluation.png)

The [final evaluation report](docs/EVALUATION.md) includes uncertainty, calibration, error analysis and limitations. The [segment appendix](docs/evaluation/SEGMENTS.md) shows every predefined group and its support. [Machine-readable final results](docs/evaluation/metrics.json) record metrics and artifact hashes.

The [baseline report](docs/BASELINE.md) and [model-selection report](docs/SELECTION.md) preserve the earlier development stages. Their validation scores are distinct from final-test results. The final holdout has now been evaluated and must not guide further tuning.

## Try the public example

Use a **stable Python 3.11** release. The recorded run used Python 3.11.14 on Windows. Dependencies are pinned in [requirements-lock.txt](requirements-lock.txt). Run these commands from the repository root.

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-lock.txt
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m topvistos.predict --input examples/synthetic_cases.csv --check-input
```

Linux/macOS:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m topvistos.predict --input examples/synthetic_cases.csv --check-input
```

These commands run without competition data or model binaries. The [synthetic example](examples/README.md) includes illustrative output; the [inference guide](docs/INFERENCE.md) explains prediction with a trusted artifact and the recorded threshold.

## Reproduce development

For historical development reproduction, obtain the [required data](data/README.md) and place it in `data/raw/`, then use your environment's Python:

```text
python -m topvistos.baseline
python -m topvistos.selection
```

The baseline requires the recorded `train.csv` hash. The tests use synthetic fixtures and run without competition data. Continuous integration installs the locked dependencies and runs the tests on Linux.

Development outputs go to `reports/generated/baseline/` and `reports/generated/selection/`: metrics, charts, local model artifacts and the selected decision. These directories are ignored by Git; only aggregate results, decision metadata and charts are curated into the documentation. Load serialized models only from a source you trust.

Final evaluation loads frozen artifacts and checks their exact hashes; it never fits a model. See the [evaluation instructions](docs/EVALUATION.md#artifacts-and-reproduction) for artifact requirements, commands and cross-environment limits.

## Engineering choices

- A deterministic, stratified 60/20/20 split; five-fold cross-validation uses only the training partition.
- Imputation, scaling, and category encoding are fitted inside the pipeline; inference handles missing values and unseen categories.
- IDs and the target are excluded from features. Negative employee counts become missing values with an indicator.
- Precision and recall use the correct argument order; ROC-AUC uses probabilities.
- Tests cover data integrity, split separation, preprocessing isolation, metrics, serialization, development execution without final-holdout features or labels, and final evaluation without refitting.

## Scope and next steps

This study models the historical label `status_do_caso`: `Aprovado=1`, `Negado=0`. It is not validated for visa eligibility or automated immigration decisions. Macro F1 is an internal development criterion; the official competition F1 variant and leaderboard result remain unverified.

Model selection, threshold selection and final evaluation are complete. Inference is available through a validated CLI and synthetic examples. The public example and prediction workflow have been checked in a separate checkout with a fresh environment. Further model changes require a new evaluation design. The original dataset was explored in the historical notebook, so the reserved partition is not new external evidence. Current scores are not directly comparable with that notebook's different split.

## Historical work and data source

- [Original notebook (Portuguese)](ml-olympiad_top-vistos-eua_solucao.ipynb), preserved unchanged.
- [Reproducibility audit](docs/REPRODUCIBILITY.md).
- [Aggregate data manifest](docs/data-manifest.json).
- [Original competition description (Portuguese)](docs/competition-description.pt-BR.md).

André Lopes. *ML Olympiad for Students — TopVistos EUA* (2023), [Kaggle](https://www.kaggle.com/competitions/ml-olympiad-for-students-topvistos-eua). The author supplied local files matching the historical row counts; original download provenance has not been independently verified. Raw data is not redistributed.
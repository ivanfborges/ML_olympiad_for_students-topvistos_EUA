# TopVistos EUA — Visa Outcome Classification

**English** | [Português](README.pt-BR.md)

A reproducible classification study built from the 2023 **ML Olympiad for Students — TopVistos EUA** Kaggle project. The current implementation separates training, validation, and a reserved final holdout, fits preprocessing inside each training fold, and compares a bounded set of models with explicit threshold selection.

## Results so far

The selected gradient-boosting model reaches **0.710 macro F1** on **3,567 validation cases** with an approval threshold of **0.60**. Model selection used five-fold cross-validation on training data; threshold selection used validation data. **These development scores include selection bias; the final holdout has not been evaluated.**

| Validation metric | Logistic baseline, 0.50 | Selected boosting, 0.60 |
|---|---:|---:|
| Macro F1 | 0.681 | 0.710 |
| F1 — approved class | 0.824 | 0.813 |
| ROC-AUC | 0.769 | 0.776 |
| Recall — denied class | 0.448 | 0.590 |

For the selected boosting model, raising the threshold from 0.50 to 0.60 identified 113 additional denied cases and classified 121 additional approved cases as denied. The [selection report](docs/SELECTION.md) explains this tradeoff, all seven candidate configurations and the frozen decision.

![Model comparison and threshold tradeoff](docs/selection/selection.png)

The [original baseline report](docs/BASELINE.md) remains available, including the prior baseline that predicts approval for every case. [Selection results in JSON](docs/selection/metrics.json) and [baseline results in JSON](docs/baseline/metrics.json) record the experiments separately.

## Reproduce the experiment

Use a **stable Python 3.11** release. The recorded run used Python 3.11.14 on Windows. Dependencies are pinned in [requirements-lock.txt](requirements-lock.txt). Run these commands from the repository root.

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-lock.txt
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m topvistos.baseline
.venv/Scripts/python.exe -m topvistos.selection
```

Linux/macOS:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m topvistos.baseline
.venv/bin/python -m topvistos.selection
```

Obtain the [required data](data/README.md) and place it in `data/raw/` before running the experiment. The baseline requires the recorded `train.csv` hash. The tests use synthetic fixtures and run without competition data. Continuous integration installs the locked dependencies and runs the tests on Linux.

Outputs go to `reports/generated/baseline/` and `reports/generated/selection/`: metrics, charts, local model artifacts and the selected decision. These directories are ignored by Git; only aggregate results, decision metadata and charts are curated into the documentation. Load serialized models only from a source you trust.

## Engineering choices

- A deterministic, stratified 60/20/20 split; five-fold cross-validation uses only the training partition.
- Imputation, scaling, and category encoding are fitted inside the pipeline; inference handles missing values and unseen categories.
- IDs and the target are excluded from features. Negative employee counts become missing values with an indicator.
- Precision and recall use the correct argument order; ROC-AUC uses probabilities.
- Tests cover data integrity, split separation, preprocessing isolation, metrics, serialization, and execution without final-holdout features or labels.

## Scope and next steps

This study models the historical label `status_do_caso`: `Aprovado=1`, `Negado=0`. It is not validated for visa eligibility or automated immigration decisions. Macro F1 is an internal development criterion; the official competition F1 variant and leaderboard result remain unverified.

Model and threshold selection are complete. Next: evaluate the frozen pipeline and decision threshold on the reserved holdout, assess calibration and examine errors across relevant segments. The original dataset was explored in the historical notebook, so the reserved partition is not new external evidence. Current scores are not directly comparable with that notebook's different split.

## Historical work and data source

- [Original notebook (Portuguese)](ml-olympiad_top-vistos-eua_solucao.ipynb), preserved unchanged.
- [Reproducibility audit](docs/REPRODUCIBILITY.md).
- [Aggregate data manifest](docs/data-manifest.json).
- [Original competition description (Portuguese)](docs/competition-description.pt-BR.md).

André Lopes. *ML Olympiad for Students — TopVistos EUA* (2023), [Kaggle](https://www.kaggle.com/competitions/ml-olympiad-for-students-topvistos-eua). The author supplied local files matching the historical row counts; original download provenance has not been independently verified. Raw data is not redistributed.
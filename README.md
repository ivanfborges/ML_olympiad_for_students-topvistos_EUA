# TopVistos EUA — Visa Outcome Classification

**English** | [Português](README.pt-BR.md)

A learning project from the 2023 **ML Olympiad for Students — TopVistos EUA** Kaggle competition. The original notebook explores tabular application data, compares classifiers, tunes a gradient-boosting model, and generates submission predictions.

## Current status

The original notebook is preserved as historical work. A reproducibility and evaluation review is in progress; **no new model has been trained or independently evaluated as part of this review**.

The repository currently contains the notebook, documentation, and a reconstruction plan. The competition CSV files and a verified training environment are not included. The notebook's stored outputs are historical observations, not a newly reproduced benchmark or a verified leaderboard score.

## What to explore

- [Original notebook (Portuguese)](ml-olympiad_top-vistos-eua_solucao.ipynb): data exploration, preprocessing, model comparison, tuning, and submission generation.
- [Reproducibility audit and next steps](docs/REPRODUCIBILITY.md): issues found in the historical version and the criteria for a reliable replacement.
- [Data preparation](data/README.md): required input files and how to organize them locally.
- [Original competition description (Portuguese)](docs/competition-description.pt-BR.md): the description previously published in this repository.

## Problem and scope

The competition uses a binary target, `status_do_caso`, and the identifier `id_do_caso`. The historical training notebook maps `Aprovado` to 1 and `Negado` to 0.

This is a study of classification on historical data. It is not a validated system for determining visa eligibility or automating immigration decisions. Evaluation must examine data limitations and differences in errors across relevant groups.

## Planned reconstruction

1. Identify the original datasets, record their provenance and hashes, and establish a clean environment.
2. Put preprocessing inside the training pipeline and reserve a final test partition.
3. Compare simple baselines with a small number of candidate models.
4. Select hyperparameters and any decision threshold using development data only.
5. Report final evaluation, segment-level errors, limitations, and reproducible inference.

These are planned deliverables, not implemented functionality. The audit documents the boundary between the current notebook and the intended replacement.

## Source and attribution

André Lopes. *ML Olympiad for Students — TopVistos EUA* (2023), Kaggle.

[Competition](https://www.kaggle.com/competitions/ml-olympiad-for-students-topvistos-eua)

Obtain the original files through an authorized source and observe the competition's access and reuse conditions. Dataset access and the exact competition scoring configuration must be confirmed before the new evaluation.
# Reproducibility audit

**English** | [Português](REPRODUCIBILITY.pt-BR.md)

Reviewed on 2026-09-12 against commit `626ae2d4cf12379817d7443c0624ca4d5fd0fb2d`. This is a static audit, not a rerun.

The original notebook has 41 cells, including 32 code cells. Its metadata records Python 3.10.10; dependency versions are not recorded in a lockfile. The repository did not contain the three competition CSVs at the time of this audit.

Cell indices below are zero-based positions in the notebook JSON, so they do not depend on saved execution counters.

| Cell(s) | Finding | Required correction |
|---|---|---|
| 3, 33 | Loading `df_test` is commented out, but the variable is used later. Paths depend on the Kaggle filesystem. | Explicit file inputs and execution from a clean interpreter. |
| 16, 38 | Category encoders are fitted on the full labeled dataset and fitted again on submission data. | Learn preprocessing on training folds and reuse the same fitted transformer for evaluation and inference; handle unseen categories. |
| 19 | The 70/30 random split is not stratified. | Define a split appropriate to available labels/entities and the intended use; document assumptions. |
| 21 | The comparison passes predictions before ground truth to precision/recall; `model_test(x, y)` ignores its arguments in favor of global split variables. | Correct metric argument order and use explicit inputs. The argument inversion alone does not change binary F1 or accuracy. |
| 21–30 | The partition named `X_test` informs model comparison and parameter inspection. | Treat development data separately from a reserved final test set. |
| 25 | ROC-AUC receives hard labels. | Evaluate ranking using probabilities or decision scores. |
| 30 | Grid search optimizes accuracy, whereas the historical description mentions F1. | Confirm the official F1 variant and align model selection with the declared objective. |

## Data and environment gates

Before training a replacement:
- acquire the original `train.csv`, `test.csv`, and `sample_submission.csv`;
- record source, download date, hashes, schema, row counts, and ID uniqueness;
- verify train/submission ID separation and sample-submission correspondence;
- distinguish raw target labels from the submission encoding;
- specify and validate the environment from a clean installation.

The historical outputs record 17,836 labeled rows and 7,644 submission rows. Local files supplied by the author on 2026-09-12 match these counts; this is not an independent verification against a fresh official download.

## Reconstruction progress

Data inspection and the fixed-baseline delivery are complete. The new implementation uses fold-local preprocessing, correct metric inputs, and separate training, validation, and reserved final-holdout partitions. See the [baseline report](BASELINE.md) for measured results. Candidate selection and final evaluation remain pending.

The original notebook remains unchanged so future comparisons can distinguish historical code from the reconstructed version.

References: [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html), [ROC-AUC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html).

## Data intake completed

The [data manifest](data-manifest.json) records the supplied files and hashes. Structural validation and seven isolated tests passed. The sample submission is incomplete and includes IDs outside the test file, so future submissions must use test-file identifiers.

The data remains local and excluded from Git. The replacement baseline ran in an isolated Python 3.11.14 environment with pinned dependencies. All 17 tests passed. Numeric feature validation and negative-employee-count handling are implemented in the pipeline. The final holdout has not been evaluated.
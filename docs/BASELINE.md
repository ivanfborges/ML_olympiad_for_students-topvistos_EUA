# Fixed-baseline experiment

**English** | [Português](BASELINE.pt-BR.md)

This delivery reconstructs the evaluation workflow of the historical Kaggle project. It establishes a reproducible development reference before model and threshold selection. It does not reproduce the old leaderboard result.

## Data and evaluation boundary

The author supplied 17,836 labeled cases. The [data manifest](data-manifest.json) records file hashes and structural checks; the original download date and provenance have not been independently verified.

Cases are sorted by identifier before two stratified random splits with seed 42. The first reserves 20%; the second allocates 25% of the remainder to validation.

| Partition | Cases | Use |
|---|---:|---|
| Training | 10,701 | Five-fold stratified cross-validation and fitting |
| Validation | 3,567 | Fixed-baseline comparison; future model/threshold selection |
| Final holdout | 3,568 | Reserved; not evaluated in this delivery |

The unlabeled competition `test.csv` is separate from this final holdout. Neither it nor the sample submission participates in baseline training. The supplied sample has ten rows and is not a complete submission template.

This random split assumes exchangeable cases. It does not establish generalization to future years, new employers, or another population. The historical notebook already explored the source dataset: the holdout is reserved within this reconstruction, not newly collected external data. Target labels are used for stratification; holdout features and labels are not passed to the fitting or scoring function.

## Fixed protocol

The [configuration](../configs/baseline.json) specifies seed 42, five training folds, threshold 0.5, logistic regularization `C=1.0`, and internal primary metric macro F1. No search or threshold tuning was performed.

The prior baseline returns the training class frequencies. Logistic regression uses `lbfgs` with at most 2,000 iterations. Imputation, scaling, and one-hot encoding are fitted separately inside each training fold. Final baseline pipelines fit only the 10,701 training cases.

Numeric variables are employee count, establishment year, and prevailing wage. The remaining seven predictors are categorical. IDs and targets never enter the feature pipeline. Negative employee counts become missing and receive an explicit indicator; the training partition contains 13 such cases. Numeric imputation uses training medians; categorical imputation uses training modes. Unknown categories are ignored by the fitted one-hot encoder.

Wages retain their original units alongside the wage-unit category; no annualization or working-hours assumption is introduced. This baseline may not capture those interactions well. Convergence warnings fail the run.

## Validation results

Class 1 means approved; class 0 means denied. Macro F1 weights the two class F1 scores equally. ROC-AUC uses approval probabilities.

| Metric | Prior baseline | Logistic regression |
|---|---:|---:|
| Macro F1 | 0.400907 | 0.680725 |
| Approved F1 | 0.801814 | 0.823848 |
| Accuracy | 0.669190 | 0.744884 |
| Balanced accuracy | 0.500000 | 0.669900 |
| ROC-AUC | 0.500000 | 0.768863 |
| Average precision — approved | 0.669190 | 0.858658 |
| Brier score, lower is better | 0.221375 | 0.177887 |
| Precision — denied | 0.000000 | 0.671320 |
| Recall — denied | 0.000000 | 0.448305 |

![Validation metrics](baseline/validation-baselines.png)

Logistic regression confusion matrix; rows are observed classes and columns are predictions:

| Observed / predicted | Denied | Approved |
|---|---:|---:|
| Denied | 529 | 651 |
| Approved | 259 | 2,128 |

The prior baseline approves every case and therefore misses every denial. Its approved-class F1 is already 0.802. Logistic regression improves discrimination but still misses 55.2% of denials at this threshold. These error patterns motivate further development; they do not establish practical suitability.

## Training cross-validation

Five-fold results for logistic regression, before fitting on the complete training partition:

| Metric | Mean | Fold standard deviation |
|---|---:|---:|
| Macro F1 | 0.676288 | 0.009712 |
| Approved F1 | 0.818215 | 0.007362 |
| Balanced accuracy | 0.666440 | 0.008580 |
| ROC-AUC | 0.772985 | 0.013118 |

Standard deviations describe variation across these folds; they are not confidence intervals. Individual fold scores, all validation metrics, split membership hashes, source hashes, and dependency versions are in the [JSON report](baseline/metrics.json).

## Reproduction and limits

Follow the [README commands](../README.md). The recorded environment uses Python 3.11.14 on Windows, the dependency lockfile, and one numerical thread. The 17 automated tests use synthetic inputs, including a complete run where the reserved partition contains only IDs. Pipeline serialization reproduced identical probabilities on three validation cases per model. Small numerical differences may occur across platforms.

The original notebook is preserved unchanged. Its scores use a different evaluation process and cannot demonstrate improvement by direct comparison with this report. The official competition F1 variant and leaderboard placement remain unverified.

Next delivery: compare a small candidate set, select any threshold on development data, and document the error tradeoff. Final-holdout scoring follows only after those choices are fixed. Calibration assessment, segment analysis, and deployment validation remain pending. This is a historical classification study, not a validated immigration decision system.

Method references: [scikit-learn data leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html), [classification metrics](https://scikit-learn.org/stable/modules/model_evaluation.html).
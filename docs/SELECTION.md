# Model and threshold selection

**English** | [Português](SELECTION.pt-BR.md)

**Selected configuration:** histogram gradient boosting with 15 leaves, 200 iterations, learning rate 0.05 and L2 regularization 1. The selected approval threshold is **0.60**. The fitted pipeline uses only the training partition; the final holdout has not been evaluated.

The [protocol](SELECTION-PROTOCOL.md) and [complete configuration](../configs/selection.json) were committed in `afe309f` before candidate execution. The seven-configuration search was not expanded after seeing results.

## Candidate comparison

All candidates used the same 10,701 training cases and five stratified folds. Selection maximized mean macro F1 at threshold 0.5. These are training cross-validation scores, not validation-partition or final-test scores.

| Configuration | Macro F1 mean | Fold SD | ROC-AUC mean |
|---|---:|---:|---:|
| Logistic, C = 0.1 | 0.674898 | 0.009782 | 0.773049 |
| Logistic, C = 1 | 0.676288 | 0.009712 | 0.772985 |
| Logistic, C = 10 | 0.676502 | 0.009598 | 0.772905 |
| Forest, depth 10 | 0.690604 | 0.011511 | 0.784493 |
| Forest, unlimited depth | 0.691249 | 0.012600 | 0.782031 |
| **Boosting, 15 leaves** | **0.694191** | **0.010330** | **0.781803** |
| Boosting, 31 leaves | 0.686624 | 0.012289 | 0.777433 |

The depth-10 forest had the highest mean ROC-AUC, but boosting won on the declared macro-F1 criterion. Fold standard deviations are descriptive; these differences are not a claim of statistical significance. The winning CV score is optimistic because it was selected from seven candidates.

## Threshold and errors

Only the winning configuration was fitted on all training cases. Twenty-five thresholds were evaluated on the 3,567 validation cases. A probability greater than or equal to the threshold predicts approval. The grid's highest macro F1 occurred at 0.60.

| Validation measure | Logistic baseline, 0.50 | Selected boosting, 0.50 | Selected boosting, 0.60 |
|---|---:|---:|---:|
| Macro F1 | 0.680725 | 0.694407 | 0.709709 |
| Approved F1 | 0.823848 | 0.823344 | 0.813146 |
| ROC-AUC | 0.768863 | 0.776458 | 0.776458 |
| Accuracy | 0.744884 | 0.748809 | 0.746566 |
| Denied recall | 0.448305 | 0.494068 | 0.589831 |
| Denied precision | 0.671320 | 0.660998 | 0.623656 |
| Approved recall | 0.891496 | 0.874738 | 0.824047 |

Raising the boosting threshold identified **113 more denied cases**, while **121 more approved cases were predicted as denied**. Approved-class F1 and accuracy decreased while macro F1 increased. Threshold selection changes class predictions, not ranking or probability calibration; ROC-AUC and Brier score therefore remain unchanged.

Confusion matrix at the selected threshold:

| Observed / predicted | Denied | Approved |
|---|---:|---:|
| Denied | 696 | 484 |
| Approved | 420 | 1,967 |

![Candidate comparison and threshold tradeoff](selection/selection.png)

The [JSON report](selection/metrics.json) contains every fold score and the full threshold curve, including both class errors. The [frozen decision](selection/decision.json) records the model specification, threshold, partition identities and local model checksum. No case-level predictions are published.

## Reproduction and next evaluation

Install the locked environment using the [README](../README.md), then run:

```text
python -m topvistos.selection
python -m unittest discover -s tests -v
```

Use the virtual environment's Python executable. Outputs are written to ignored `reports/generated/selection/`. The pipeline, decision JSON, metrics and plot are generated together. Keep the pipeline and its matching decision file together: bare `pipeline.predict()` uses the estimator's default decision rule, not the selected 0.60 threshold.

The 25 tests cover partition drift, CV-only model selection, exact-probability boundary behavior, threshold ties, missing/unseen inputs and complete execution without holdout features or labels. Reloading the selected model preserved every validation probability exactly. Runtime: Python 3.11.14, Windows, unchanged dependency lock, one numerical thread.

The 3,568-case final holdout remains reserved for stage 2.4. Evaluate the frozen training-only pipeline and threshold before any refitting. Validation metrics used to choose the threshold have selection bias; they are not independent evidence of generalization. Macro F1 remains an internal objective, with no assumed business cost or verified competition scoring claim. Calibration assessment, segment analysis and final evaluation remain pending. Historical data exposure and the random-case split limitations from the [baseline report](BASELINE.md) still apply.
# Final evaluation of frozen models

**English** | [Português](EVALUATION.pt-BR.md)

The selected boosting model achieved **0.701 macro F1** on the **3,568-case final holdout**, with a 95% bootstrap interval of **0.686–0.717**. The logistic baseline achieved 0.672. The selected model and its approval threshold of 0.60 were fixed before evaluation.

The improvement in the overall score coexists with large differences in errors across education groups. This is evidence for a bounded historical classification study, not validation for individual visa decisions.

## Evaluation design

The [protocol](EVALUATION-PROTOCOL.md) and [configuration](../configs/evaluation.json) were committed in `096312f` before final scoring. The 10,701 training cases and 3,567 validation cases were not added to the final evaluation. The holdout contains 1,180 denied and 2,388 approved cases.

Artifact, training-source, dependency and data checks passed. All three pipelines were loaded from the previously fitted artifacts. No training, threshold search or calibration fitting occurred. The earlier [baseline](BASELINE.md) and [selection](SELECTION.md) reports remain unchanged as historical stages.

## Final results

| Holdout metric | Prior / 0.50 | Logistic / 0.50 | Selected boosting / 0.60 |
|---|---:|---:|---:|
| Macro F1 | 0.400940 | 0.671587 | 0.701240 |
| Approved F1 | 0.801880 | 0.817016 | 0.808335 |
| Accuracy | 0.669283 | 0.735987 | 0.739630 |
| Balanced accuracy | 0.500000 | 0.661937 | 0.698311 |
| ROC-AUC | 0.500000 | 0.761702 | 0.772532 |
| Brier score, lower is better | 0.221343 | 0.180478 | 0.174730 |
| Denied recall | 0.000000 | 0.443220 | 0.576271 |
| Denied precision | 0.000000 | 0.647277 | 0.613165 |
| Approved recall | 1.000000 | 0.880653 | 0.820352 |

Selected-model confusion matrix:

| Observed / predicted | Denied | Approved |
|---|---:|---:|
| Denied | 680 | 500 |
| Approved | 429 | 1,959 |

Compared with logistic regression, the selected model identifies **157 additional denied cases** and predicts **144 additional approved cases as denied**. Its approved-class F1 is lower. The result supports the declared macro-F1 objective, not improvement on every metric.

The paired macro-F1 difference is **+0.02965**, with a 95% percentile interval of **+0.01675 to +0.04142**. This interval is above zero under the registered resampling assumptions. Selected-model ROC-AUC has interval 0.755–0.789; Brier score, 0.169–0.181.

The 1,000 bootstrap samples reuse the same sampled cases for all models and preserve class counts. Intervals condition on these fitted models and class counts; they exclude training/selection uncertainty and distribution shift. The constant-prior macro-F1 interval collapses to a point because its predictions and resampled class counts are fixed.

![Final model comparison and calibration](evaluation/evaluation.png)

## Calibration

The ten-bin ECE is **0.01476**. This is descriptive and depends on binning; it is not a certificate of calibrated individual probabilities. Brier score combines aspects of calibration and discrimination.

In the [0.8, 0.9) bin, 660 cases have a mean predicted approval probability of **85.1%**, versus **81.5%** observed approvals (Wilson 95% interval: 78.4–84.3%). The lowest-probability bin contains only two cases and has a very wide interval. No calibrator was fitted after these observations.

## Errors hidden by the overall score

All predefined groups and supports appear in the [segment appendix](evaluation/SEGMENTS.md), with both recall intervals and suppression reasons.

- In the `Doutorado` group, the model identifies only **4 of 45 denied cases**: denied recall **8.9%** (Wilson 95%: 3.5–20.7%).
- In `Ensino Médio`, it identifies **301 of 310 denied cases**, but only **16 of 170 approved cases**: approved recall **9.4%**.
- For hourly wages (`Hora`), approved recall is **21.9%**, versus **84.9%** for annual wages (`Ano`).
- Five categories fail the predefined support rule: Africa, Oceania, island employment region, monthly wages and weekly wages. Their counts are published; performance estimates are suppressed.

These associations concern this historical dataset and fitted model. Groups differ in class mix and other characteristics, overlap across dimensions, and were not assessed with multiple-comparison correction. The analysis neither identifies causes nor establishes fairness or unfairness as a legal or causal conclusion.

## Artifacts and reproduction

The [JSON report](evaluation/metrics.json) records all metrics, intervals, calibration bins, segments, environment and hashes. Tests run with synthetic data; **34 tests passed locally**. GitHub Actions validation is pending publication.

Follow the [environment instructions](../README.md). With the recorded frozen artifacts in the default generated directories:

```text
python -m topvistos.evaluation
```

Use the virtual environment's Python. Paths can be provided with `--selection-dir`, `--baseline-dir`, `--data-dir` and `--output-dir`. Evaluation requires the registered model byte hashes and dependency versions; it deliberately fails if rebuilt artifacts differ. Model binaries and raw data are not redistributed. Training commands can rebuild models, but byte-identical artifacts are not guaranteed across environments.

The command saves aggregate metrics, the chart and a private prediction cache in ignored `reports/generated/evaluation/`. It refuses an existing output directory. Read saved results instead of re-evaluating to guide further tuning.

**The final holdout has now been consumed.** Further model development requires a new evaluation design. Random-case splitting and historical exposure limit the claim; this is not evidence of performance on future applicants, new employers or another population. Competition scoring and leaderboard placement remain unverified.

Next delivery: polish the inference example, documentation and clean-checkout workflow. The model and threshold remain fixed.

Method references: [probability calibration](https://scikit-learn.org/stable/modules/calibration.html), [bootstrap intervals](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).
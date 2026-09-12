# Final evaluation protocol

**English** | [Português](EVALUATION-PROTOCOL.pt-BR.md)

Recorded before inspecting final-holdout predictions or metrics. The [configuration](../configs/evaluation.json) fixes the analysis. The model and approval threshold were already selected in stage 2.3.

- Verify the frozen decision, training-source hashes, model artifact hashes, dependency versions, data hash and all partition identities before scoring. Use the same 3,568 reserved cases. No fitting, threshold changes, calibration fitting, or feature engineering.
- Evaluate the selected boosting pipeline at 0.60. Report the previously fitted prior and logistic baselines at 0.50 as references, not candidates for reselection. Artifact hashes are recorded before evaluation.
- Report macro F1 (primary), both classes' F1/precision/recall where available, accuracy, balanced accuracy, ROC-AUC, average precision, Brier score and confusion matrices.
- Use 1,000 paired, class-stratified bootstrap resamples, seed 20260912, for 95% percentile intervals of each model's macro F1, selected-model ROC-AUC/Brier, and the macro-F1 difference between the selected model and logistic baseline. Keep class counts fixed in each resample. Intervals describe conditional sampling uncertainty for fixed fitted models, not training/selection uncertainty or population shift.
- Assess selected-model calibration with ten equal-width probability bins on [0,1], including 1 in the last bin. Publish bin counts, mean predicted probabilities, observed approval fractions and Wilson 95% intervals. Empty bins have null summaries. Report count-weighted absolute calibration error (ECE) as a bin-dependent descriptive quantity; Brier score also measures discrimination and is not pure calibration.
- Analyze all observed categories separately for continent, employee education, employment region and wage unit. Publish support for each class. Suppress performance metrics when a segment has fewer than 100 cases or fewer than 20 cases of either class. For supported groups, report errors, macro F1, ROC-AUC and Wilson 95% intervals for both classes' recall.
- Segment analyses are descriptive, overlap across dimensions and have no multiple-comparison correction. Do not rank people, infer causes, certify fairness, or change decisions by segment. Raw labels and categories preserve the source meanings; geographical fields are not proxies for verified protected identities.
- Save predictions locally to support report reproduction without refitting. Publish only aggregates and plots. Refuse to overwrite an existing evaluation output directory. Preserve the earlier baseline and selection reports as historical stages.
- After evaluation, this holdout is consumed. Any future model or threshold development needs a new evaluation design; the same holdout must not be presented as unseen again.

References: [probability calibration](https://scikit-learn.org/stable/modules/calibration.html), [bootstrap confidence intervals](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html).
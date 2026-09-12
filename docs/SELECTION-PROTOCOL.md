# Model-selection protocol

**English** | [Português](SELECTION-PROTOCOL.pt-BR.md)

Recorded before the stage 2.3 candidate experiment, after reviewing the fixed-baseline results. The [configuration](../configs/selection.json) specifies the complete search budget.

1. Reuse the recorded training/validation/holdout membership and data hash. No final-holdout scoring or feature exploration.
2. Compare seven configurations: logistic regression with C = 0.1, 1, 10; random forests with 200 trees, minimum leaf size 5 and maximum depth 10 or unlimited; histogram gradient boosting with 200 iterations, learning rate 0.05, minimum leaf size 20, L2 = 1 and 15 or 31 leaves. Boosting early stopping is disabled. Seed 42, one numerical thread.
3. Reuse baseline domain rules and fold-local imputation, scaling and one-hot encoding. Tree pipelines use dense one-hot output; no new features or wage normalization.
4. Use the same five stratified training folds for all seven configurations (35 fits). Select the highest mean training-CV macro F1 at threshold 0.5. Ties within 1e-12 use configuration order. Report every candidate and all fold scores; fold standard deviations are descriptive, not confidence intervals. Selection makes the winning CV score optimistic.
5. Fit only the selected configuration on all 10,701 training cases. Use the 3,567 validation cases to choose among 25 thresholds from 0.20 to 0.80, step 0.025. Maximize macro F1; ties within 1e-12 prefer the threshold closest to 0.5, then the lower threshold. Predict approval when its probability is greater than or equal to the threshold.
6. Report the selected model at threshold 0.5 and the chosen threshold, with confusion matrices and both classes' recall/precision. Threshold-selected validation metrics are development estimates with selection bias, not final generalization estimates. Macro F1 is an internal objective, not a confirmed competition metric or a business cost.
7. Freeze the selected pipeline trained on training data only and the threshold for stage 2.4. Do not refit on validation before final evaluation, because refitting could change probability behavior. Preserve the fixed-baseline report unchanged. No search expansion in response to these results.

Tests use synthetic fixtures. Publish aggregate results, configuration, source hashes and charts; keep raw data, case identifiers and serialized pipelines local.

References: [threshold tuning](https://scikit-learn.org/stable/modules/classification_threshold.html), [random forest](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html), [histogram gradient boosting](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html).
# Synthetic inference examples

**English** | [Português](README.pt-BR.md)

Every case in [synthetic_cases.csv](synthetic_cases.csv) was invented for a software demonstration. None is an individual from the competition dataset. There are no ground-truth targets.

[synthetic_predictions.csv](synthetic_predictions.csv) records the frozen model's illustrative output on those invented cases, with threshold 0.60. It is not a performance benchmark or advice about visa outcomes.

The third row intentionally includes an unknown category, a negative employee count and a missing wage. Follow the [inference guide](../docs/INFERENCE.md) to validate the input or run the prediction command.
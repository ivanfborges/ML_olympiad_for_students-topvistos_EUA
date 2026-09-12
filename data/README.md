# Competition data

**English** | [Português](README.pt-BR.md)

Required original files:

| File | Role |
|---|---|
| `train.csv` | Features, case identifier, and observed target |
| `test.csv` | Competition submission features and case identifier; this is not our future labeled evaluation partition |
| `sample_submission.csv` | Example of output columns and encoding; the supplied file is not a complete ID template |

Place the files in `data/raw/` after obtaining them from the [competition](https://www.kaggle.com/competitions/ml-olympiad-for-students-topvistos-eua) through an authorized account/source.

The raw directory is ignored by Git. Files are not redistributed by this repository. Do not add account credentials or access tokens.

If the original files are unavailable, record that limitation before selecting a replacement dataset. A similar dataset is not evidence that the original competition result has been reproduced.

Schema, IDs, target values, and file hashes have been checked for the supplied files. Original download provenance remains unverified. Follow the [training instructions](../README.md) to reproduce the implemented baseline.

## Supplied files

On 2026-09-12, the author supplied local files: 17,836 training rows, 7,644 competition-test rows, and 10 sample-submission rows. Six sample IDs do not occur in test.csv. Use test.csv as the source of identifiers for prediction output.

See the [aggregate manifest](../docs/data-manifest.json). Regenerate it locally with:

```text
python scripts/inspect_data.py --output reports/generated/data-manifest.json
```

No raw records or local source paths are published.
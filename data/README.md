# Competition data

**English** | [Português](README.pt-BR.md)

Required original files:

| File | Role |
|---|---|
| `train.csv` | Features, case identifier, and observed target |
| `test.csv` | Competition submission features and case identifier; this is not our future labeled evaluation partition |
| `sample_submission.csv` | Reference for required identifiers, columns, and output format |

Place the files in `data/raw/` after obtaining them from the [competition](https://www.kaggle.com/competitions/ml-olympiad-for-students-topvistos-eua) through an authorized account/source.

The raw directory is ignored by Git. Files are not redistributed by this repository. Do not add account credentials or access tokens.

If the original files are unavailable, record that limitation before selecting a replacement dataset. A similar dataset is not evidence that the original competition result has been reproduced.

Next step: validate provenance, schema, IDs, target values, and file hashes before installing and running the new training environment.
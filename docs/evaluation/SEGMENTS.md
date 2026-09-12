# Final-holdout results by segment

**English** | [Português](SEGMENTS.pt-BR.md)

Fixed threshold 0.60. Brackets show Wilson 95% intervals. Categories retain the source labels. Metrics are suppressed when N < 100 or either class has fewer than 20 cases. Groups overlap across dimensions; do not add counts across tables. Descriptive analysis with no multiple-comparison correction.

## Continent

| Category | N | Denied | Approved | Macro F1 | Denied recall [CI] | Approved recall [CI] |
|---|---:|---:|---:|---:|---:|---:|
| América do Norte | 423 | 153 | 270 | 0.660 | 0.542 [0.463–0.619] | 0.774 [0.721–0.820] |
| América do Sul | 117 | 43 | 74 | 0.652 | 0.628 [0.479–0.756] | 0.689 [0.577–0.783] |
| Europa | 552 | 112 | 440 | 0.710 | 0.438 [0.349–0.530] | 0.936 [0.910–0.956] |
| Oceania | 25 | 8 | 17 | — | — | — |
| África | 72 | 22 | 50 | — | — | — |
| Ásia | 2379 | 842 | 1537 | 0.701 | 0.597 [0.564–0.630] | 0.802 [0.781–0.821] |

## Employee education

| Category | N | Denied | Approved | Macro F1 | Denied recall [CI] | Approved recall [CI] |
|---|---:|---:|---:|---:|---:|---:|
| Doutorado | 311 | 45 | 266 | 0.543 | 0.089 [0.035–0.207] | 0.996 [0.979–0.999] |
| Ensino Médio | 480 | 310 | 170 | 0.476 | 0.971 [0.946–0.985] | 0.094 [0.059–0.147] |
| Ensino Superior | 1449 | 545 | 904 | 0.651 | 0.510 [0.468–0.552] | 0.787 [0.759–0.812] |
| Mestrado | 1328 | 280 | 1048 | 0.652 | 0.346 [0.293–0.404] | 0.923 [0.905–0.937] |

## Employment region

| Category | N | Denied | Approved | Macro F1 | Denied recall [CI] | Approved recall [CI] |
|---|---:|---:|---:|---:|---:|---:|
| Ilha | 59 | 23 | 36 | — | — | — |
| Meio-Oeste | 596 | 147 | 449 | 0.674 | 0.408 [0.332–0.489] | 0.909 [0.878–0.932] |
| Nordeste | 974 | 352 | 622 | 0.720 | 0.668 [0.617–0.715] | 0.778 [0.744–0.809] |
| Oeste | 899 | 349 | 550 | 0.701 | 0.625 [0.573–0.674] | 0.776 [0.740–0.809] |
| Sul | 1040 | 309 | 731 | 0.677 | 0.502 [0.446–0.557] | 0.841 [0.813–0.866] |

## Wage unit

| Category | N | Denied | Approved | Macro F1 | Denied recall [CI] | Approved recall [CI] |
|---|---:|---:|---:|---:|---:|---:|
| Ano | 3238 | 980 | 2258 | 0.685 | 0.507 [0.476–0.538] | 0.849 [0.834–0.863] |
| Hora | 289 | 184 | 105 | 0.560 | 0.940 [0.896–0.966] | 0.219 [0.151–0.307] |
| Mês | 10 | 1 | 9 | — | — | — |
| Semana | 31 | 15 | 16 | — | — | — |

[Full report](../EVALUATION.md) · [Aggregate data](metrics.json)
